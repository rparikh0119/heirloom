"""Checks patina: moves it does often wear in, moves it rarely does stay hesitant.
Run:  python tests/test_wear_patina.py
"""
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.behavior.expressions import EXPRESSIONS, ExpressionPlayer  # noqa: E402
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge, FADE_DAYS  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.wear.patina import load_settings  # noqa: E402

DAY = date(2026, 10, 23)
DT = 1 / 30
CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def brain_with(cart, **kw):
    return HeirloomBrain(play_sound=lambda name: None, cartridge=cart, **kw)


def patina(brain):
    return next(w for w in brain.wear if w.name == "patina")


def performance(brain, move):
    """Play one move and measure it: seconds before it starts moving, total length, biggest offset."""
    brain.expr.play(move)
    frames, start, peak = 0, None, 0.0
    first_key = set(EXPRESSIONS[move][1][1])          # channels the move actually animates
    while brain.expr.name is not None and frames < 30 * 20:
        out = brain.expr.step(DT)
        frames += 1
        moving = max((abs(out.get(k, 0.0)) for k in first_key - {"head_roll", "head_yaw"}), default=0.0)
        if start is None and moving > 1e-6:
            start = frames * DT
        peak = max(peak, max((abs(v) for v in out.values()), default=0.0))
    return {"starts_at": start or 0.0, "length": frames * DT, "peak": peak}


def wave_many(brain, n):
    for _ in range(n):
        brain.handle(Event("wave", source="hands"))
        brain.pass_time(5)


# ---------------------------------------------------------------------------------------------

@check("no cartridge: every expression plays exactly as keyframed (nothing changed)")
def _(tmp):
    plain = ExpressionPlayer()
    b = HeirloomBrain(play_sound=lambda name: None)
    assert b.expr.style is None
    for move in EXPRESSIONS:
        plain.play(move)
        b.expr.play(move)
        for _ in range(60):
            assert plain.step(DT) == b.expr.step(DT)


@check("a fresh droid hesitates before it moves")
def _(tmp):
    b = brain_with(Cartridge.create(tmp, on=DAY))
    perf = performance(b, "hello")
    assert perf["starts_at"] >= 0.3, perf


@check("every wave counts as a use of 'hello' in the cartridge")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    wave_many(b, 5)
    assert cart.read_page("L1", "patina")["hello"]["uses"] == 5


@check("after 300 waves, hello is worn: no pause, quicker, bigger")
def _(tmp):
    cart = Cartridge.create(tmp / "fresh", on=DAY)
    fresh = performance(brain_with(cart), "hello")
    cart2 = Cartridge.create(tmp / "worn", on=DAY)
    b = brain_with(cart2)
    wave_many(b, 300)
    worn = performance(b, "hello")
    assert worn["starts_at"] <= 0.1, worn             # first frames are the keyframe ease-in, no pause
    assert worn["length"] < fresh["length"] * 0.75, (fresh, worn)
    assert worn["peak"] > fresh["peak"] * 1.15, (fresh, worn)


@check("wear is per move: 300 waves leave 'happy' as hesitant as new")
def _(tmp):
    b = brain_with(Cartridge.create(tmp, on=DAY))
    wave_many(b, 300)
    assert patina(b).style("hello")["hesitate_s"] < 0.01
    assert patina(b).style("happy")["hesitate_s"] == load_settings()["fresh"]["hesitate_s"]


@check("key presses don't wear moves in when ignored (testing stays clean)")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart, wear_ignores={"unity"})
    b.handle(Event("wave", source="unity"))
    assert cart.read_page("L1", "patina") == {}


@check("passed on: the next owner meets the worn moves, a faded past goes back to stiff")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    wave_many(brain_with(cart), 300)
    cart.handoff("second home", on=DAY)
    assert patina(brain_with(cart)).style("hello")["hesitate_s"] < 0.01          # kept: still worn
    cart.set_weight("L1", "fade", on=DAY)
    b = brain_with(cart)
    b.today = DAY + timedelta(days=FADE_DAYS)
    patina(b).apply(b)
    assert patina(b).style("hello")["hesitate_s"] == load_settings()["fresh"]["hesitate_s"]


@check("the settings file loads, and a typo stops with a clear message")
def _(tmp):
    load_settings()
    raw = json.loads(json.dumps(load_settings()))
    raw["worn"]["sped"] = raw["worn"].pop("speed")
    (tmp / "p.json").write_text(json.dumps(raw))
    try:
        load_settings(tmp / "p.json")
        raise AssertionError("accepted a typo")
    except ValueError as e:
        assert "sped" in str(e)


@check("the time skip wears moves in: a family's droid has a worn hello after a year")
def _(tmp):
    from heirloom.sim import time_skip
    time_skip("loud_family", tmp, years=1, seed=5, quiet=True)
    page = Cartridge.open(tmp / "loud_family_year1").read_page("L1", "patina")
    assert page["hello"]["uses"] > 200, page


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
