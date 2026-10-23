"""Checks how the voice listener reacts, with a fake recogniser (no microphone, no vosk needed).
Run:  python tests/test_voice.py
"""
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.perception.intents import can_act_early  # noqa: E402
from heirloom.perception.voice import VoiceListener  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


class FakeRec:
    """Replays what vosk would say, one step per audio chunk: ("partial", text) or ("final", text)."""

    def __init__(self, script):
        self.script = list(script)
        self.step = ("partial", "")
        self.resets = 0

    def AcceptWaveform(self, chunk):
        self.step = self.script.pop(0) if self.script else ("partial", "")
        return self.step[0] == "final"

    def Result(self):
        return json.dumps({"text": self.step[1]})

    def PartialResult(self):
        return json.dumps({"partial": self.step[1]})

    def Reset(self):
        self.resets += 1
        self.script = [s for s in self.script if s[0] == "partial"]   # the rest of that sentence is gone


def hear(script, addressed=False, listening=False):
    """Feed a script through the listener. Returns (events, how many chunks it took to fire)."""
    v = VoiceListener()
    v._rec = FakeRec(script)
    v.addressed = addressed
    if listening:
        v._listen_until = time.monotonic() + 5
    fired_at = []
    t = threading.Thread(target=v._run, daemon=True)
    t.start()
    for i in range(len(script) + 2):
        v._audio.put(b"\0" * 10)
        time.sleep(0.01)
        if v._events and not fired_at:
            fired_at.append(i + 1)
    time.sleep(0.05)
    v.stop()
    return v.pop_events(), (fired_at[0] if fired_at else None)


@check("up close, a plain 'hi' works without saying Heirloom")
def _():
    events, _ = hear([("partial", "hi"), ("final", "hi")], addressed=True)
    assert events == ["wave"], events


@check("far away, a plain 'hi' is still ignored (the name keeps a loud room out)")
def _():
    events, _ = hear([("partial", "hi"), ("final", "hi")], addressed=False)
    assert events == [], events


@check("far away, 'Heirloom hi' works")
def _():
    events, _ = hear([("partial", "heirloom"), ("partial", "heirloom hi"), ("final", "heirloom hi")])
    assert events == ["wave"], events


@check("'hi' fires while you're still talking, before the pause at the end, and only once")
def _():
    events, at = hear([("partial", "hi"), ("partial", "hi"), ("partial", "hi"), ("final", "hi")], addressed=True)
    assert events == ["wave"], events
    assert at <= 2, at                     # acts on the second live read (0.2 s in), not at the pause


@check("'good' waits for the end, because it might be 'good night'")
def _():
    events, _ = hear([("partial", "good"), ("partial", "good night"), ("final", "good night")], addressed=True)
    assert events == ["sleep"], events


@check("'no' waits, so 'not now' isn't mistaken for a scold")
def _():
    events, _ = hear([("partial", "no"), ("partial", "no"), ("partial", "not now"), ("final", "not now")], addressed=True)
    assert events == ["not_now"], events


@check("a guess that flickers doesn't fire early")
def _():
    events, at = hear([("partial", "hi"), ("partial", "hey"), ("partial", "hi"), ("final", "hi")], addressed=True)
    assert events == ["wave"], events
    assert at == 4, at                     # waited for the end, because the guess kept changing


@check("'good' on its own still counts as praise once you stop")
def _():
    events, _ = hear([("partial", "good"), ("partial", "good"), ("final", "good")], addressed=True)
    assert events == ["good"], events


@check("which phrases are safe to act on early")
def _():
    assert can_act_early("hi") and can_act_early("hello") and can_act_early("heirloom hi")
    assert can_act_early("go to sleep") and can_act_early("i love you")
    assert not can_act_early("good")          # good night / good morning
    assert not can_act_early("no")            # a live "no" can become "not now", so it waits
    assert not can_act_early("")
    assert not can_act_early("banana")


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
