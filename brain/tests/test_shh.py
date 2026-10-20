"""Checks Riya's shh gesture with fake hands. Run:  python tests/test_shh.py"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from heirloom.perception.gestures import GestureDetector  # noqa: E402
from test_gestures import make_hand, msg  # noqa: E402

HEAD = (0.0, 0.25, 0.60)          # your eyes: 25 cm above the robot's head, 60 cm in front of it


def finger_at(tip, extended=("index",), up=(0, 1, 0), normal=(-1, 0, 0)):
    """A right hand whose index fingertip sits at `tip`."""
    hand = make_hand("right", wrist=(0, 0, 0), up=up, normal=normal, extended=extended, thumb_dir=(0, 0, -1))
    return hand + (np.asarray(tip) - hand[10])


def fires(hand, head=HEAD, secs=1.0) -> list:
    g = GestureDetector()
    out = []
    for _ in range(int(secs * 30)):
        out += g.step(1 / 30, msg(right=hand), head)
    return out


CASES = [
    ("finger on your lips",                    finger_at((0, 0.16, 0.57)),                       True),
    ("finger up, but out in front (not lips)", finger_at((0, 0.10, 0.30)),                       False),
    ("fist at your mouth (no finger up)",      finger_at((0, 0.16, 0.57), extended=()),          False),
    ("whole open hand at your mouth",          finger_at((0, 0.16, 0.57), extended=("index", "middle", "ring", "little")), False),
    ("finger pointing sideways at your mouth", finger_at((0, 0.16, 0.57), up=(1, 0, 0), normal=(0, 0, -1)), False),
]


def main() -> None:
    ok = 0
    for label, hand, should in CASES:
        got = "shh" in fires(hand)
        ok += got == should
        print(f"  {'PASS' if got == should else 'FAIL'}  {label:42s} expected {'shh' if should else 'nothing'}, got {'shh' if got else 'nothing'}")
    unknown_head = "shh" in fires(CASES[0][1], head=None)
    ok += not unknown_head
    print(f"  {'PASS' if not unknown_head else 'FAIL'}  {'no head position known':42s} expected nothing")
    print(f"\n{ok}/{len(CASES) + 1} passed")


if __name__ == "__main__":
    main()
