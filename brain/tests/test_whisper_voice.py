"""Checks the Whisper listener without a microphone or the Whisper model (a fake stands in).
Run:  python tests/test_whisper_voice.py
"""
import sys
import time
from collections import namedtuple
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.perception.intents import match  # noqa: E402
from heirloom.perception.whisper_voice import FRAME, SAMPLE_RATE, Segmenter, WhisperListener, confident  # noqa: E402

Seg = namedtuple("Seg", "text no_speech_prob avg_logprob")
CHECKS = []
RNG = np.random.default_rng(3)


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def room(seconds, level=0.003):
    return RNG.normal(0, level, int(seconds * SAMPLE_RATE)).astype(np.float32)


def voice(seconds, level=0.15):
    """Something speech-loud: a wobbling tone with a syllable rhythm."""
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    env = 0.6 + 0.4 * np.sin(2 * np.pi * 4 * t)
    return (level * env * np.sin(2 * np.pi * 180 * t)).astype(np.float32) + room(seconds)


def clips_from(audio):
    s, out = Segmenter(), []
    for i in range(0, len(audio) - FRAME + 1, FRAME):
        c = s.feed(audio[i:i + FRAME])
        if c is not None:
            out.append((i / SAMPLE_RATE, len(c) / SAMPLE_RATE))
    return out


class FakeModel:
    def __init__(self, segs):
        self.segs = segs

    def transcribe(self, clip, **kw):
        return iter(self.segs), None


def names(events):
    return [e.name if hasattr(e, "name") else e for e in events]


def listener(segs, addressed=True):
    v = WhisperListener()
    v._model = FakeModel(segs)
    v.addressed = addressed
    return v


# ---------------------------------------------------------------------------------------------

@check("three things said with pauses between become three clips")
def _():
    audio = np.concatenate([room(1), voice(0.5), room(1), voice(1.2), room(1), voice(0.8), room(1)])
    clips = clips_from(audio)
    assert len(clips) == 3, clips


@check("a clip ends soon after you stop talking (under half a second)")
def _():
    audio = np.concatenate([room(1), voice(0.6), room(1.5)])
    (ended, _), = clips_from(audio)
    assert ended - 1.6 < 0.5, ended


@check("the start of the word isn't cut off (it keeps a little audio from before)")
def _():
    audio = np.concatenate([room(1), voice(0.6), room(1)])
    (_, length), = clips_from(audio)
    assert length >= 0.6, length


@check("a quiet room never triggers it, and neither does a single click")
def _():
    click = np.zeros(SAMPLE_RATE // 100, dtype=np.float32) + 0.5
    audio = np.concatenate([room(2), click, room(2)])
    assert clips_from(audio) == []


@check("a louder room (fan, music) raises the bar instead of triggering all the time")
def _():
    audio = np.concatenate([room(3, level=0.02), voice(0.6, level=0.3), room(1.5, level=0.02)])
    assert len(clips_from(audio)) == 1


@check("Whisper's punctuation and phrasing still match: 'Hey there!' is hello")
def _():
    v = listener([Seg("Hey there!", 0.05, -0.3)])
    v.hear_clip(voice(0.5))
    assert names(v.pop_events()) == ["wave"]


@check("the name spelled 'Heir loom' still wakes it from far away")
def _():
    v = listener([Seg("Heir loom, good job.", 0.05, -0.3)], addressed=False)
    v.hear_clip(voice(0.5))
    assert names(v.pop_events()) == ["good"]


@check("far away without the name: ignored")
def _():
    v = listener([Seg("Hi!", 0.05, -0.3)], addressed=False)
    v.hear_clip(voice(0.5))
    assert names(v.pop_events()) == []


@check("a low-confidence 'Thank you.' (Whisper hearing noise) is dropped, not praise")
def _():
    v = listener([Seg(" Thank you.", 0.8, -1.4)])
    v.hear_clip(voice(0.5))
    assert names(v.pop_events()) == []
    assert not confident([Seg("x", 0.2, -1.5)]) and confident([Seg("x", 0.1, -0.4)])


@check("everyday phrasings land: 'what's up', 'well done', 'leave me alone', 'night night'")
def _():
    got = [match(t, loose=True)[1] for t in ["What's up?", "Well done!", "Leave me alone.", "Night night."]]
    assert got == ["wave", "good", "not_now", "sleep"], got


@check("the longest phrase still wins: 'Good night' is sleep, 'Not now' isn't a scold")
def _():
    assert match("Good night!", loose=True)[1] == "sleep"
    assert match("No, not now.", loose=True)[1] == "not_now"


def run_audio(v, audio):
    """Push audio through the listener's real loop (the thread that reads the mic)."""
    import threading
    t = threading.Thread(target=v._run, daemon=True)
    t.start()
    for i in range(0, len(audio) - FRAME + 1, FRAME):
        v._audio.put(audio[i:i + FRAME])
    time.sleep(0.3)
    v.stop()
    return names(v.pop_events())


@check("it says 'hearing' the moment you start talking, before Whisper has finished")
def _():
    v = listener([Seg("Hi.", 0.05, -0.3)])
    events = run_audio(v, np.concatenate([room(1), voice(0.6), room(1)]))
    assert events == ["hearing", "wave"], events


@check("far away with --need-name, it doesn't perk at every voice in the room")
def _():
    v = listener([Seg("Hi.", 0.05, -0.3)], addressed=False)
    events = run_audio(v, np.concatenate([room(1), voice(0.6), room(1)]))
    assert "hearing" not in events, events


@check("the brain: 'hearing' lifts the antennas at once, plays no move, learns nothing")
def _():
    import tempfile
    from datetime import date
    from heirloom.brain import HeirloomBrain
    from heirloom.cartridge import Cartridge
    with tempfile.TemporaryDirectory() as d:
        cart = Cartridge.create(Path(d), on=date.today())
        b = HeirloomBrain(play_sound=lambda name: None, cartridge=cart)
        b.step(1 / 30, None)
        before = b.step(1 / 30, None)[0].antenna_left
        b.handle("hearing")
        assert b.expr.name is None                                  # no expression, so no patina pause
        after = max(b.step(1 / 30, None)[0].antenna_left for _ in range(8))
        assert after > before + 8, (before, after)
        assert cart.read_page("L1", "patina") == {} and cart.read_page("L1", "dials") == {}


@check("asleep, it doesn't perk up at voices")
def _():
    from heirloom.brain import HeirloomBrain
    b = HeirloomBrain(play_sound=lambda name: None)
    b.handle("sleep")
    b.handle("hearing")
    assert b.presence._perk == 0.0


def main() -> None:
    ok = 0
    for label, fn in CHECKS:
        try:
            fn()
            ok += 1
            print(f"  PASS  {label}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {label}\n        {type(e).__name__}: {e}")
    print(f"\n{ok}/{len(CHECKS)} passed")


if __name__ == "__main__":
    main()
