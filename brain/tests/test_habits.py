"""Checks habits wear: it picks up its keeper's way of moving, overnight, and passes it down with a floor.
Synthetic hands, no headset.  Run:  python tests/test_habits.py
"""
import json
import math
import random
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.wear.habits import CAP, FEATURES, FLOOR, MIN_GESTURES  # noqa: E402

CHECKS = []
HZ = 30
START = datetime(2026, 10, 1, 20, 0)

ENERGETIC = {"peak": 1.5, "reach": 0.28, "wiggles": 3, "wander": 0.06, "settle": 0.15, "rest_s": 0.6, "roll": 7.0}
CALM = {"peak": 0.4, "reach": 0.12, "wiggles": 0, "wander": 0.0, "settle": 0.6, "rest_s": 4.0, "roll": -1.0}


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def droid(folder: Path, learn=True, day=0):
    cart = Cartridge.open(folder) if (folder / "cartridge.json").exists() else Cartridge.create(folder, on=START.date())
    b = HeirloomBrain(play_sound=lambda n: None, cartridge=cart, learn=learn)
    b.now = START + timedelta(days=day)
    return b


def hands_msg(p):
    arr = [0.0] * 78
    arr[0:3] = list(p)
    return {"type": "hands", "left_tracked": False, "left": [], "right_tracked": True, "right": arr}


def _stroke(style: dict, reach: float):
    """Speeds for one stroke: a bell up to the keeper's peak, then an exponential slow-down
    (settle), with optional wiggle (extra speed peaks). Distance adds up to `reach`."""
    peak, tau = style["peak"], style["settle"] / 2.5
    w = max(0.03, (reach / peak - tau) * 2 / math.sqrt(math.pi))
    t, v, out = 0.0, 0.0, []
    tp = 2 * w
    while True:
        if t < tp:
            v = peak * math.exp(-((t - tp) / w) ** 2)
        else:
            v = peak * math.exp(-(t - tp) / tau)
        if style["wiggles"]:                                # jerky: the speed surges and dips a few times
            v *= 1 + 0.8 * math.sin(2 * math.pi * style["wiggles"] * t / (tp + 4 * tau))
        out.append(max(0.0, v))
        t += 1 / HZ
        if t > tp and v < 0.01:
            break
    total = sum(out) / HZ
    return [x * reach / total for x in out]


def gesture_frames(style: dict, rng: random.Random):
    """One gesture out from rest and back, then a pause. Yields wrist positions at 30 Hz."""
    home = np.array([0.15, -0.25, 0.45])
    reach = style["reach"] * rng.uniform(0.85, 1.15)
    direction = np.array([rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(-0.5, 0.5)])
    direction /= np.linalg.norm(direction)
    side = np.cross(direction, [0, 0, 1.0])
    side = side / (np.linalg.norm(side) or 1)
    pos = home.copy()
    for sign in (1, -1):
        speeds = _stroke(style, reach)
        done = 0.0
        for v in speeds:
            done += v / HZ
            u = min(1.0, done / reach)
            pos = (home if sign > 0 else home + direction * reach) + sign * direction * done \
                + side * style["wander"] * math.sin(math.pi * u)
            yield pos
        for _ in range(int(style["rest_s"] * HZ)):
            yield pos


def a_day(b, style: dict, gestures=60, seed=0):
    rng = random.Random(seed)
    for _ in range(gestures):
        for p in gesture_frames(style, rng):
            b.sense_body(hands_msg(p), head=[0.0, 0.1, 0.6], roll=style["roll"] + rng.uniform(-1, 1))
            b.t += 1 / HZ
    b.handle(Event("sleep", source="voice"))
    b.handle(Event("wake", source="voice"))


def days(b, style, n, seed=0):
    for d in range(n):
        b.now = b.now + timedelta(days=1)
        a_day(b, style, seed=seed + d)


def page(b, lid="L1"):
    return b.cartridge.read_page(lid, "habits")


def habits(b):
    return next(w for w in b.wear if w.name == "habits")


# ---------------------------------------------------------------------------------------------

@check("off unless learning: it doesn't watch, and nothing is written")
def _(tmp):
    b = droid(tmp / "c", learn=False)
    a_day(b, ENERGETIC)
    assert page(b) == {}


@check("one night: the day becomes seven numbers, and that's all that's kept (no raw motion)")
def _(tmp):
    b = droid(tmp / "c")
    a_day(b, ENERGETIC)
    p = page(b)
    assert set(p) == {"schema", "style", "days", "last"}, p
    assert set(p["style"]) == set(FEATURES), p["style"]
    assert len(json.dumps(p)) < 400, len(json.dumps(p))
    h = habits(b)
    assert h._gestures == [] and h._frames == 0, "today's raw numbers should be gone after dreaming"


@check("it measures the difference: energetic hands read faster, bigger, busier and more tilted than calm ones")
def _(tmp):
    e, c = droid(tmp / "e"), droid(tmp / "c")
    a_day(e, ENERGETIC)
    a_day(c, CALM)
    se, sc = page(e)["style"], page(c)["style"]
    assert se["tempo"] > 2 * sc["tempo"] and se["amplitude"] > 2 * sc["amplitude"], (se, sc)
    assert se["stillness"] < sc["stillness"] - 0.2 and se["directness"] <= sc["directness"], (se, sc)
    assert se["tilt"] > 4 and abs(sc["tilt"]) < 3, (se["tilt"], sc["tilt"])


@check("tracking jitter (2 mm) doesn't hide the difference in the numbers it trusts")
def _(tmp):
    nr = np.random.default_rng(0)

    def jittery_day(b, style):
        rng = random.Random(0)
        for _ in range(60):
            for p in gesture_frames(style, rng):
                b.sense_body(hands_msg(p + nr.normal(0, 0.002, 3)), roll=style["roll"] + rng.uniform(-1, 1))
                b.t += 1 / HZ
        b.handle(Event("sleep", source="voice"))
    e, c = droid(tmp / "e"), droid(tmp / "c")
    jittery_day(e, ENERGETIC)
    jittery_day(c, CALM)
    se, sc = page(e)["style"], page(c)["style"]
    assert se["tempo"] > 2 * sc["tempo"] and se["amplitude"] > 2 * sc["amplitude"], (se, sc)
    assert sc["stillness"] > 0.6 and se["stillness"] < sc["stillness"] - 0.2, (se, sc)


@check("a thin day teaches nothing")
def _(tmp):
    b = droid(tmp / "c")
    a_day(b, ENERGETIC, gestures=MIN_GESTURES // 2 - 2)   # each one is out and back: two gestures
    assert page(b) == {}


@check("never live: the way it moves only changes after it sleeps on it")
def _(tmp):
    b = droid(tmp / "c")
    days(b, ENERGETIC, 10)
    before = dict(habits(b).offsets)
    rng = random.Random(9)
    for _ in range(80):                                   # a very calm afternoon, no sleep yet
        for p in gesture_frames(CALM, rng):
            b.sense_body(hands_msg(p))
            b.t += 1 / HZ
    assert habits(b).offsets == before


@check("over weeks an energetic keeper's droid moves quicker and bigger, a calm keeper's slower and smaller")
def _(tmp):
    e, c = droid(tmp / "e"), droid(tmp / "c")
    days(e, ENERGETIC, 40)
    days(c, CALM, 40, seed=100)
    plain = dict(e.expr.PLAIN)
    se, sc = habits(e).restyle("hello", plain), habits(c).restyle("hello", plain)
    assert se["speed"] > sc["speed"] and se["size"] > sc["size"], (se, sc)
    assert se["tilt_deg"] > 1.0, se["tilt_deg"]
    assert "quicker" in e.wear_state()["habits_line"] or "bigger" in e.wear_state()["habits_line"], e.wear_state()["habits_line"]


@check("it stays itself: no setting moves more than 30% however extreme the keeper")
def _(tmp):
    b = droid(tmp / "c")
    plain = dict(b.expr.PLAIN)
    days(b, ENERGETIC, 60)
    st = habits(b).restyle("hello", plain)
    assert st["speed"] <= plain["speed"] * (1 + CAP) + 1e-9 and st["size"] <= plain["size"] * (1 + CAP) + 1e-9, st


@check("a new keeper's influence ramps up over weeks")
def _(tmp):
    b = droid(tmp / "c")
    days(b, ENERGETIC, 3)
    w3 = habits(b).mix[0][1]
    days(b, ENERGETIC, 20, seed=50)
    w23 = habits(b).mix[0][1]
    assert w3 < 0.15 < w23, (w3, w23)


@check("passed down: the old keeper's numbers freeze, fade, and never drop below the floor")
def _(tmp):
    a = droid(tmp / "c")
    days(a, ENERGETIC, 40)
    frozen = dict(page(a)["style"])
    a.cartridge.handoff("keeper B", on=a.now.date())
    b = droid(tmp / "c", day=41)
    days(b, CALM, 3, seed=200)
    assert page(b, "L1")["style"] == frozen
    b.now += timedelta(days=400)
    habits(b).apply(b)
    old = dict(habits(b).mix)["L1"]
    assert abs(old - FLOOR) < 1e-9, habits(b).mix


@check("strength 0 turns it off for that keeper")
def _(tmp):
    b = droid(tmp / "c")
    days(b, ENERGETIC, 40)
    p = page(b)
    p["strength"] = 0.0
    b.cartridge.write_page("L1", "habits", p)
    b2 = droid(tmp / "c", day=41)
    assert b2.wear_state()["habits_line"] == "", b2.wear_state()["habits_line"]


@check("a page with anything beyond the seven numbers is refused")
def _(tmp):
    cart = Cartridge.create(tmp / "bad")
    cart.write_page("L1", "habits", {"schema": "heirloom.wear.habits/1", "style": {"tempo": 1, "wrist_path": [1, 2]}})
    try:
        HeirloomBrain(play_sound=lambda n: None, cartridge=Cartridge.open(tmp / "bad"))
    except Exception as e:  # noqa: BLE001
        assert "seven style numbers" in str(e), e
        return
    raise AssertionError("accepted raw motion in the page")


# ---------------------------------------------------------------------------------------------

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
