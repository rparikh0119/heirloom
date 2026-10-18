"""Offline voice listener. Hears "Heirloom", then listens a few seconds for a command.

Runs on its own thread. Nothing leaves the computer: Vosk does speech recognition locally,
and it is limited to the phrases in intents.py, which keeps it fast and hard to fool.

The brain reads events with pop_events(), the same way it reads events from Unity:
    "listen"        the wake word was heard (Heirloom perks up)
    "good", "wave"  ...any event from intents.INTENTS

Needs:  python -m pip install -e .[voice]
The speech model (~40 MB) downloads automatically the first time.
"""
from __future__ import annotations

import json
import queue
import threading
import time
from collections import deque

from .intents import WAKE_WORDS, all_phrases, match

MODEL_NAME = "vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
LISTEN_SECONDS = 5.0


class VoiceListener:
    def __init__(self, mic: int | None = None, listen_seconds: float = LISTEN_SECONDS,
                 require_wake_word: bool = True) -> None:
        self.mic = mic
        self.listen_seconds = listen_seconds
        self.require_wake_word = require_wake_word
        self._events: deque[str] = deque(maxlen=20)
        self._lock = threading.Lock()
        self._audio: queue.Queue[bytes] = queue.Queue()
        self._listen_until = 0.0
        self._stop = threading.Event()
        self.last_heard = ""

    # ---------- public ----------
    def start(self) -> "VoiceListener":
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)  # hide Kaldi's chatter
        print(f"[voice] loading {MODEL_NAME} (downloads once, ~40 MB)...")
        model = Model(model_name=MODEL_NAME, lang="en-us")
        self._warn_missing_words(model)

        # Only these phrases (plus "[unk]" for everything else) can ever be recognised.
        grammar = json.dumps(all_phrases() + ["[unk]"])
        self._rec = KaldiRecognizer(model, SAMPLE_RATE, grammar)

        self._stream = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, dtype="int16",
                                         channels=1, device=self.mic, callback=self._on_audio)
        self._stream.start()
        name = sd.query_devices(self.mic, "input")["name"]
        print(f"[voice] listening on: {name}. Say \"{WAKE_WORDS[0]}\" first.")
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if getattr(self, "_stream", None) is not None:
            self._stream.stop()
            self._stream.close()

    def pop_events(self) -> list[str]:
        with self._lock:
            events = list(self._events)
            self._events.clear()
        return events

    @property
    def listening(self) -> bool:
        return time.monotonic() < self._listen_until

    # ---------- internals ----------
    def _on_audio(self, indata, frames, time_info, status) -> None:
        self._audio.put(bytes(indata))   # runs on the audio thread, so keep it tiny

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                chunk = self._audio.get(timeout=0.5)
            except queue.Empty:
                continue
            if self._rec.AcceptWaveform(chunk):   # True when a phrase just ended (a pause)
                text = json.loads(self._rec.Result()).get("text", "").replace("[unk]", "").strip()
                if text:
                    self._heard(text)

    def _heard(self, text: str) -> None:
        self.last_heard = text
        woke, event = match(text)
        open_window = self.listening or not self.require_wake_word

        if woke and event:                 # "Heirloom, good job" in one breath
            self._emit(event)
            self._listen_until = 0.0
            tag = event
        elif woke:                         # just the name: perk up and wait
            self._emit("listen")
            self._listen_until = time.monotonic() + self.listen_seconds
            tag = "listen"
        elif event and open_window:        # command inside the listening window
            self._emit(event)
            self._listen_until = 0.0
            tag = event
        elif event:
            tag = f"ignored (would be {event}, but it wasn't called by name)"
        else:
            tag = "ignored"
        print(f"[voice] heard \"{text}\" -> {tag}")

    def _emit(self, event: str) -> None:
        with self._lock:
            self._events.append(event)

    @staticmethod
    def _warn_missing_words(model) -> None:
        missing = sorted({w for p in all_phrases() for w in p.split()
                          if model.vosk_model_find_word(w) == -1})
        if missing:
            print(f"[voice] WARNING: not in the speech model's vocabulary, will never be heard: {missing}")
