"""The journal: photos (later voice memories) that live in the cartridge and pass down with the droid.

    <cartridge>/journal/*.jpg|png     the photos (D04: separate from the personality, open formats)
    <cartridge>/journal/retired.json  photos retired with "not now" while shown (D45). Never shown again.
    <cartridge>/journal/voice/*.wav   voice memories (D33), 16-bit mono WAV exactly as recorded,
    <cartridge>/journal/voice/*.json  with what was said (Whisper, on this computer) and when

Without a cartridge, or with an empty journal, it uses brain/journal_samples/ so the projector can be
tested. Memories are only ever shown when asked (D45).
"""
from __future__ import annotations

import json
import random
import re
import wave
from datetime import datetime
from pathlib import Path

import numpy as np

SAMPLES = Path(__file__).resolve().parents[1] / "journal_samples"
_FILLER = {"play", "the", "it", "back", "one", "about", "recording", "message", "a", "my", "that", "me", "let",
           "hear", "again", "please", "heirloom", "with", "of", "to", "and"}
PHOTO_TYPES = {".jpg", ".jpeg", ".png"}


class Journal:
    def __init__(self, folder: Path | None = None, rng: random.Random | None = None) -> None:
        self.folder = Path(folder) if folder else None
        self.rng = rng or random.Random()
        self._recent: list[str] = []

    @classmethod
    def for_cartridge(cls, cartridge) -> "Journal":
        return cls(cartridge.folder / "journal" if cartridge is not None else None)

    def _retired_file(self) -> Path | None:
        return self.folder / "retired.json" if self.folder else None

    def retired(self) -> set[str]:
        f = self._retired_file()
        if f is None or not f.exists():
            return set()
        try:
            return set(json.loads(f.read_text(encoding="utf-8")).get("retired", []))
        except (json.JSONDecodeError, OSError):
            return set()

    def photos(self) -> list[Path]:
        """Photos it may show: the cartridge's own, minus retired ones. Samples if it has none."""
        own = sorted(p for p in (self.folder.glob("*") if self.folder and self.folder.exists() else [])
                     if p.suffix.lower() in PHOTO_TYPES)
        gone = self.retired()
        own = [p for p in own if p.name not in gone]
        if own or (self.folder and any(p.suffix.lower() in PHOTO_TYPES for p in self.folder.glob("*"))):
            return own                      # a journal where everything is retired stays empty
        return sorted(p for p in SAMPLES.glob("*") if p.suffix.lower() in PHOTO_TYPES)

    def pick(self) -> Path | None:
        """One photo, avoiding the last few it showed."""
        options = self.photos()
        if not options:
            return None
        avoid = self._recent[-min(3, len(options) - 1):] if len(options) > 1 else []
        fresh = [p for p in options if p.name not in avoid] or options
        choice = self.rng.choice(fresh)
        self._recent = (self._recent + [choice.name])[-3:]
        return choice

    # ---------- photos ----------

    def save_photo(self, jpeg: bytes, when: datetime | None = None) -> Path | None:
        """Keep a photo the droid took (D02: only ever when asked). Needs a cartridge."""
        if self.folder is None or not jpeg:
            return None
        when = when or datetime.now()
        self.folder.mkdir(parents=True, exist_ok=True)
        stem = when.strftime("%Y-%m-%d_%H%M%S")
        path, k = self.folder / f"{stem}.jpg", 1
        while path.exists():
            path, k = self.folder / f"{stem}_{k}.jpg", k + 1
        path.write_bytes(jpeg)
        return path

    # ---------- voice memories (D33) ----------

    def save_voice(self, samples: np.ndarray, sr: int, said: str, when: datetime | None = None) -> Path | None:
        """Keep a recording in the cartridge, untouched. Needs a cartridge (nowhere else to keep it)."""
        if self.folder is None:
            return None
        when = when or datetime.now()
        folder = self.folder / "voice"
        folder.mkdir(parents=True, exist_ok=True)
        stem = when.strftime("%Y-%m-%d_%H%M%S")
        path = folder / f"{stem}.wav"
        k = 1
        while path.exists():
            path, k = folder / f"{stem}_{k}.wav", k + 1
        pcm = (np.clip(np.asarray(samples, dtype=np.float32), -1, 1) * 32767).astype("<i2").tobytes()
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm)
        path.with_suffix(".json").write_text(json.dumps({"said": said, "when": when.isoformat(timespec="seconds"),
                                                         "seconds": round(len(samples) / sr, 1)}, indent=2),
                                             encoding="utf-8")
        return path

    def voices(self) -> list[tuple[Path, dict]]:
        """Every voice memory, oldest first, with its note."""
        folder = self.folder / "voice" if self.folder else None
        if folder is None or not folder.exists():
            return []
        out = []
        for wav_path in sorted(folder.glob("*.wav")):
            try:
                note = json.loads(wav_path.with_suffix(".json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                note = {}
            out.append((wav_path, note))
        return out

    def find_voice(self, asked: str = "") -> Path | None:
        """The recording that best matches the words asked for ("play the one about the recipe"),
        or the newest one if nothing matches."""
        found = self.voices()
        if not found:
            return None
        words = set(re.findall(r"[a-z']+", asked.lower())) - _FILLER
        if words:
            scored = [(len(words & set(re.findall(r"[a-z']+", n.get("said", "").lower()))), i, p)
                      for i, (p, n) in enumerate(found)]
            best = max(scored)
            if best[0] > 0:
                return best[2]
        return found[-1][0]

    @staticmethod
    def load_voice(path: Path) -> tuple[np.ndarray, int]:
        with wave.open(str(path), "rb") as w:
            sr = w.getframerate()
            data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        return data, sr

    def retire(self, photo: Path) -> None:
        """'Not now' while it's shown: never show this one again (D45). Samples can't be retired."""
        if self.folder is None or photo.parent != self.folder:
            return
        names = sorted(self.retired() | {photo.name})
        self.folder.mkdir(parents=True, exist_ok=True)
        self._retired_file().write_text(json.dumps({"retired": names}, indent=2), encoding="utf-8")
