"""Checks rolling: beckon it and it rolls over to you, stops at a comfortable distance, never leaves
the desk, and goes back to its spot when asked.  Run:  python tests/test_rolling.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.behavior.rolling import MAX_ROAM, STOP_AT, Roller  # noqa: E402
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.perception.intents import match  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def live(b, person, seconds):
    """The person stands still in the room. Each frame the brain sees them relative to where it has rolled."""
    poses = []
    for _ in range(int(seconds * 30)):
        rel = (person[0] - b.roller.x, person[1], person[2] - b.roller.z)
        poses.append(b.step(1 / 30, rel)[0])
    return poses


def brain():
    return HeirloomBrain(play_sound=lambda name: None)


@check("beckoned from 70 cm away: it rolls over and stops about 45 cm from you")
def _():
    b = brain()
    person = (0.0, 0.25, 0.70)
    live(b, person, 0.5)
    b.handle("curious")
    assert b.mode == "rolling"
    poses = live(b, person, 5)
    gap = math.hypot(person[0] - b.roller.x, person[2] - b.roller.z)
    assert abs(gap - STOP_AT) < 0.01, gap
    assert b.mode != "rolling" and poses[-1].drive_z > 0.2


@check("it rolls at a calm pace and slows down as it arrives")
def _():
    b = brain()
    person = (0.0, 0.25, 0.75)
    live(b, person, 0.5)
    b.handle("curious")
    z = [p.drive_z for p in live(b, person, 4)]
    v = [(b2 - a) * 30 for a, b2 in zip(z, z[1:])]
    assert max(v) <= 0.121 and max(v) > 0.1, max(v)
    moving = [x for x in v if x > 1e-4]
    assert moving[-1] < 0.5 * max(v), moving[-5:]


@check("it heads toward you, wherever you are (off to the side too)")
def _():
    b = brain()
    person = (-0.5, 0.25, 0.5)                          # front left
    live(b, person, 0.5)
    b.handle("curious")
    live(b, person, 6)
    assert b.roller.x < -0.1 and b.roller.z > 0.1, (b.roller.x, b.roller.z)


@check("it never goes more than 35 cm from its spot, so it stays on the desk")
def _():
    b = brain()
    person = (0.0, 0.25, 2.0)
    live(b, person, 0.5)
    b.handle("curious")
    live(b, person, 8)
    assert math.hypot(b.roller.x, b.roller.z) <= MAX_ROAM + 1e-6


@check("already close: it just reacts, it doesn't shuffle")
def _():
    b = brain()
    person = (0.0, 0.25, 0.48)
    live(b, person, 0.5)
    b.handle("curious")
    assert b.mode != "rolling" and not b.roller.moving


@check("nobody seen (or asleep): it doesn't go anywhere")
def _():
    b = brain()
    b.handle("curious")
    assert not b.roller.moving
    s = brain()
    live(s, (0, 0.25, 0.8), 0.3)
    s.handle("sleep")
    s.handle("curious")
    assert not s.roller.moving


@check("'go back' rolls it home to where it started")
def _():
    b = brain()
    person = (0.0, 0.25, 0.8)
    live(b, person, 0.5)
    b.handle("curious")
    live(b, person, 5)
    assert b.roller.z > 0.2
    b.handle("go_home")
    live(b, person, 6)
    assert math.hypot(b.roller.x, b.roller.z) < 0.003


@check("the pose carries where it is, so a body that can roll goes there")
def _():
    b = brain()
    p = live(b, (0, 0.25, 0.8), 0.2)[-1]
    assert p.drive_x == 0.0 and p.drive_z == 0.0


@check("the words: 'come here' beckons, 'go back' / 'back to your spot' send it home")
def _():
    got = [match(t, loose=True)[1] for t in ["Come here.", "Go back.", "Back to your spot.", "Go home."]]
    assert got == ["curious", "go_home", "go_home", "go_home"], got


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
