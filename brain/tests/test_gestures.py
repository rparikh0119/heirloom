"""Synthetic hands to check the gesture maths. Run: python -m pytest tests  (or python tests/test_gestures.py)"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.perception.gestures import GestureDetector  # noqa: E402


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def make_hand(side="right", wrist=(0, 0, 0.4), up=(0, 1, 0), normal=(0, 0, -1),
              extended=("index", "middle", "ring", "little"), thumb_dir=None):
    """A simple hand. up = where the fingers point, normal = where the palm faces."""
    w, u, n = np.asarray(wrist, float), unit(up), unit(normal)
    # r points from the little finger toward the index finger. Right hand: r = n x u in these maths.
    r = unit(np.cross(n, u)) * (1 if side == "right" else -1)
    # check the palm-normal convention used by the detector and flip r if needed
    j = np.zeros((26, 3))
    j[0] = w
    j[1] = w + u * 0.05
    offs = {"index": 0.03, "middle": 0.01, "ring": -0.01, "little": -0.03}
    starts = {"index": 6, "middle": 11, "ring": 16, "little": 21}
    for f, s in starts.items():
        base = w + u * 0.08 + r * offs[f]
        j[s] = w + r * offs[f] * 0.5 + u * 0.02          # metacarpal
        j[s + 1] = base
        if f in extended:
            for k in range(2, 5):
                j[s + k] = base + u * 0.025 * (k - 1)
        else:  # curl toward the palm
            j[s + 2] = base + n * 0.02 + u * 0.01
            j[s + 3] = base + n * 0.03 - u * 0.01
            j[s + 4] = base + n * 0.015 - u * 0.025
    tb = w + r * 0.04 + u * 0.02
    td = unit(thumb_dir) if thumb_dir is not None else unit(r + u)
    j[2] = w + r * 0.02
    for k in range(3, 6):
        j[k] = tb + td * 0.025 * (k - 3)
    return j


def msg(right=None, left=None):
    m = {"type": "hands", "right_tracked": right is not None, "left_tracked": left is not None}
    if right is not None:
        m["right"] = right.ravel().tolist()
    if left is not None:
        m["left"] = left.ravel().tolist()
    return m


def run(frames, secs=1.0):
    g = GestureDetector()
    out = []
    n = int(secs * 30)
    for i in range(n):
        f = frames(i / 30) if callable(frames) else frames
        out += g.step(1 / 30, f)
    return out


def test_palm_normal_points_at_robot():
    from heirloom.perception.gestures import HandState
    for side in ("right", "left"):
        h = HandState(make_hand(side), side)
        assert h.toward_robot > 0.9, (side, h.toward_robot)


def test_static_gestures():
    assert run(msg(make_hand())) == ["not_now"]
    assert run(msg(left=make_hand("left"))) == ["not_now"]
    thumbs = make_hand(up=(0, 0, -1), normal=(-1, 0, 0), extended=(), thumb_dir=(0, 1, 0))
    assert run(msg(thumbs)) == ["good"]
    rude = make_hand(normal=(0, 0, 1), extended=("middle",))
    assert run(msg(rude)) == ["offended"]
    fist = make_hand(extended=(), thumb_dir=(1, 0, 0))
    assert run(msg(fist)) == []


def test_hold_fires_once():
    assert run(msg(make_hand()), secs=8) == ["not_now"]


def test_wave():
    def frame(t):
        x = 0.08 * math.sin(2 * math.pi * 2.0 * t)
        return msg(make_hand(wrist=(x, 0.1, 0.4)))
    out = run(frame, secs=2)
    assert out and out[0] == "wave", out
    assert "not_now" not in out[:1]


def hooked_index(hook):
    """Palm up, index finger hooked by 0..1, other fingers curled (the 'come here' finger)."""
    j = make_hand(up=(0, 0, -1), normal=(0, 1, 0), extended=("index",))
    base, u, n = j[7], unit((0, 0, -1)), unit((0, 1, 0))
    for k in range(2, 5):
        straight = base + u * 0.025 * (k - 1)
        bent = base + u * 0.02 + n * 0.012 * (k - 1) - u * 0.004 * (k - 1) ** 2
        j[6 + k] = straight * (1 - hook) + bent * hook
    return j


def test_beckon():
    def frame(t):
        hook = (1 - math.cos(2 * math.pi * 1.5 * t)) / 2      # partial hook, never a full curl
        return msg(hooked_index(hook))
    out = run(frame, secs=2.5)
    assert "curious" in out, out


def test_single_open_close_is_not_beckon():
    def frame(t):
        ext = () if 0.5 < t < 1.0 else ("index", "middle", "ring", "little")
        return msg(make_hand(up=(0, 0, -1), normal=(0, 1, 0), extended=ext))
    assert "curious" not in run(frame, secs=2.5)


def heart_hands():
    """Left and right hands making a heart in front of the robot."""
    hands = {}
    for side, sx in (("left", 1), ("right", -1)):   # person's left hand is on robot's +x
        j = make_hand(side, wrist=(sx * 0.09, -0.02, 0.35), up=(-sx, 1, 0), normal=(0, 0, -1),
                      extended=(), thumb_dir=(-sx, -1, 0))
        j[10] = (0.0, 0.08, 0.35)    # index tips meet on top
        j[5] = (0.0, -0.06, 0.35)    # thumb tips meet at the bottom
        hands[side] = j
    return hands


def test_heart():
    h = heart_hands()
    assert run(msg(right=h["right"], left=h["left"]), secs=3) == ["heart"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
