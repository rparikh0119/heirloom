"""Checks voice memories (D33): "record this", it keeps your next sentence in the cartridge, and
"play it back" plays it through the tape filter. No microphone or Whisper model needed.
Run:  python tests/test_voice_memories.py
"""
import io
import json
import sys
import tempfile
import time
import wave
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.journal import Journal  # noqa: E402
from heirloom.perception.intents import match  # noqa: E402
from heirloom.perception.whisper_voice import (FRAME, RECORD_END_SILENCE, SAMPLE_RATE, END_SILENCE,  # noqa: E402
                                               Segmenter, WhisperListener)
from heirloom.sound.tape import tape  # noqa: E402

Seg = namedtuple("Seg", "text no_speech_prob avg_logprob")
RNG = np.random.default_rng(7)
CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def room(seconds, level=0.003):
    return RNG.normal(0, level, int(seconds * SAMPLE_RATE)).astype(np.float32)


def voice(seconds, level=0.15, hz=180):
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    return (level * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t)) * np.sin(2 * np.pi * hz * t)).astype(np.float32) + room(seconds)


class Script:
    """A fake Whisper that answers each clip with the next line."""
    def __init__(self, lines):
        self.lines = list(lines)

    def transcribe(self, clip, **kw):
        return iter([Seg(self.lines.pop(0), 0.05, -0.3)]), None


def listener(lines):
    v = WhisperListener()
    v._model = Script(lines)
    v.addressed = True
    return v


def names(v):
    return [e.name for e in v.pop_events()]


def brain(cart):
    clips, sounds = [], []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=cart, play_clip=clips.append)
    return b, clips, sounds


def new_cart(tmp):
    return Cartridge.create(tmp / "c", on=date.today())


# ---------------------------------------------------------------------------------------------

@check("'record this', then the next sentence is kept as a recording, not read as a command")
def _(tmp):
    v = listener(["Record this.", "Two cups of flour, good job remembering."])
    v.hear_clip(voice(0.6))
    assert names(v) == ["record"] and v.recording
    v.hear_clip(voice(2.0))
    events = v.pop_events()
    assert [e.name for e in events] == ["recorded"], events
    assert len(events[0].data["audio"]) == len(voice(2.0)) and "flour" in events[0].data["said"]
    assert not v.recording


@check("while recording it allows natural pauses (1.5 s), then goes back to quick replies")
def _(tmp):
    v = listener(["Record this.", "x"])
    v.hear_clip(voice(0.5))
    assert v.segmenter.end_silence == RECORD_END_SILENCE
    s = Segmenter()
    s.end_silence = RECORD_END_SILENCE
    clips = []
    audio = np.concatenate([room(1), voice(1.0), room(0.8), voice(1.0), room(2.0)])    # a 0.8 s pause mid-sentence
    for i in range(0, len(audio) - FRAME + 1, FRAME):
        c = s.feed(audio[i:i + FRAME])
        if c is not None:
            clips.append(c)
    assert len(clips) == 1, len(clips)
    v.hear_clip(voice(1.0))
    assert v.segmenter.end_silence == END_SILENCE


@check("'not now' instead of a memory cancels it, nothing saved")
def _(tmp):
    v = listener(["Record this.", "Not now."])
    v.hear_clip(voice(0.5))
    v.pop_events()
    v.hear_clip(voice(0.5))
    assert names(v) == ["not_now"] and not v.recording


@check("if you say nothing for 15 s it stops waiting")
def _(tmp):
    import threading
    v = listener(["Record this."])
    v.hear_clip(voice(0.5))
    v._armed_until = time.monotonic() - 0.1
    t = threading.Thread(target=v._run, daemon=True)
    t.start()
    v._audio.put(room(0.03))
    time.sleep(0.2)
    v.stop()
    assert not v.recording


@check("the brain keeps it in the cartridge: a WAV exactly as recorded, plus what was said")
def _(tmp):
    cart = new_cart(tmp)
    b, _, sounds = brain(cart)
    b.handle("record")
    assert b.mode == "recording"
    b.handle("good")                                   # waits while recording
    assert b.mode == "recording"
    audio = voice(1.5)
    b.handle(Event("recorded", source="voice", data={"audio": audio, "sr": SAMPLE_RATE, "said": "two cups of flour"}))
    assert b.mode != "recording" and sounds[-1] == "saved", (b.mode, sounds)
    (wav_path, note), = Journal.for_cartridge(cart).voices()
    assert note["said"] == "two cups of flour" and note["seconds"] == 1.5
    data, sr = Journal.load_voice(wav_path)
    assert sr == SAMPLE_RATE and np.allclose(data, np.clip(audio, -1, 1), atol=1 / 16000)


@check("'play it back' plays the person's recording, framed by a chirp before and after, and it listens along quietly")
def _(tmp):
    cart = new_cart(tmp)
    Journal.for_cartridge(cart).save_voice(voice(2.0), SAMPLE_RATE, "happy birthday")
    b, clips, sounds = brain(cart)
    b.handle(Event("play_memory", data={"said": "play it back"}))
    assert b.mode == "replaying" and len(clips) == 1
    with wave.open(io.BytesIO(clips[0])) as w:
        frames = w.getnframes()
        assert w.getframerate() == SAMPLE_RATE and 2.4 * SAMPLE_RATE < frames < 3.4 * SAMPLE_RATE, frames
    b.handle("good")
    assert "happy" not in sounds                       # no chirps over the recording
    for _ in range(int(4.5 * 30)):
        b.step(1 / 30, None)
    assert b.mode != "replaying"


@check("'play the one about the birthday' finds it by what was said, otherwise the newest")
def _(tmp):
    j = Journal(tmp / "journal")
    j.save_voice(voice(0.5), SAMPLE_RATE, "Grandma's recipe, two cups of flour", when=datetime(2026, 1, 1, 9))
    j.save_voice(voice(0.5), SAMPLE_RATE, "Happy birthday Maya", when=datetime(2026, 2, 1, 9))
    j.save_voice(voice(0.5), SAMPLE_RATE, "Remember to water the plants", when=datetime(2026, 3, 1, 9))
    assert "2026-02" in j.find_voice("play the one about the birthday").name
    assert "2026-01" in j.find_voice("play grandma's recipe").name
    assert "2026-03" in j.find_voice("play it back").name


@check("no recordings yet, or no cartridge: it says so, nothing breaks")
def _(tmp):
    b, clips, _ = brain(new_cart(tmp))
    b.handle(Event("play_memory"))
    assert clips == [] and b.mode != "replaying"
    nb, _, _ = brain(None)
    nb.handle("record")
    nb.handle(Event("recorded", data={"audio": voice(1.0), "sr": SAMPLE_RATE, "said": "hi"}))
    assert nb.mode != "recording"


@check("every style keeps the voice: same length, mids kept, deep bass and top softened, never above 0.8")
def _(tmp):
    sr = 22050
    t = np.arange(sr) / sr
    x = sum(0.25 * np.sin(2 * np.pi * f * t) for f in (40, 1000, 10000)).astype(np.float32)
    from heirloom.sound.tape import STYLES
    for style in STYLES:
        y = tape(x, sr, style=style)
        assert len(y) == len(x) and np.max(np.abs(y)) <= 0.8001, style
        spec = np.abs(np.fft.rfft(y)) ** 2             # compare small bands around each tone
        band = {f: np.sqrt(spec[f - 30:f + 30].sum()) for f in (40, 1000, 10000)}
        assert band[40] < 0.5 * band[1000] and band[10000] < 0.6 * band[1000], (style, band)


@check("the right words: 'remember this' records, 'remember when' shows a photo, 'let me hear it' plays")
def _(tmp):
    got = {t: match(t, loose=True)[1] for t in ["Record this.", "Remember this.", "Remember when?", "Play it back.",
                                                 "Let me hear it.", "Show me a memory."]}
    assert got == {"Record this.": "record", "Remember this.": "record", "Remember when?": "show_memory",
                   "Play it back.": "play_memory", "Let me hear it.": "play_memory",
                   "Show me a memory.": "show_memory"}, got


def main() -> None:
    ok = 0
    for label, fn in CHECKS:
        with tempfile.TemporaryDirectory() as d:
            try:
                fn(Path(d))
                ok += 1
                print(f"  PASS  {label}")
            except Exception as e:  # noqa: BLE001
                print(f"  FAIL  {label}\n        {type(e).__name__}: {e}")
    print(f"\n{ok}/{len(CHECKS)} passed")


if __name__ == "__main__":
    main()
