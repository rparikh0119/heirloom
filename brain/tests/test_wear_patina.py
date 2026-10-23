"""Checks patina: moves wear in over weeks, take on the home over years, never repeat exactly,
and rust after time apart.
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

DAY = date.today()          # the brain wakes up on the real date, so the tests do too
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


def seeded(brain, seed=1):
    patina(brain).rng = __import__("random").Random(seed)
    return brain


def deep_cart(tmp, uses, last=DAY):
    """A cartridge whose hello has been played `uses` times, last on `last`."""
    cart = Cartridge.create(tmp, on=DAY - timedelta(days=4000))
    cart.write_page("L1", "patina", {"hello": {"uses": uses, "last": last.isoformat()}})
    return cart


@check("a worn move keeps a little looseness, never machine-perfect (Okada, R51)")
def _(tmp):
    b = brain_with(Cartridge.create(tmp, on=DAY))
    wave_many(b, 300)
    st = patina(b).base_style("hello")
    assert st["wobble_deg"] > 0 and st["smooth"] < 1.0, st


@check("no two plays are identical (Hyodol, R59)")
def _(tmp):
    b = seeded(brain_with(Cartridge.create(tmp, on=DAY)))
    wave_many(b, 300)
    a, c = performance(b, "hello"), performance(b, "hello")
    assert a != c, (a, c)


@check("character deepens over years: 1 year of hellos is far from 12")
def _(tmp):
    pat = patina(brain_with(deep_cart(tmp / "a", 870)))
    y1 = pat.depth["hello"]
    pat = patina(brain_with(deep_cart(tmp / "b", 6150)))
    y12 = pat.depth["hello"]
    assert y1 < 0.4 and y12 > 0.85, (y1, y12)


@check("two homes, same use, different dials: the worn hello moves differently (keinen henka, R67)")
def _(tmp):
    bold = brain_with(deep_cart(tmp / "a", 6000))
    calm = brain_with(deep_cart(tmp / "b", 6000))
    bold.character.dials.update(boldness=0.7, sass=0.65, energy=0.5)
    calm.character.dials.update(boldness=0.4, sass=0.5, energy=0.3)
    sb, sc = patina(bold).base_style("hello"), patina(calm).base_style("hello")
    assert sb["lean_deg"] > 5 and sc["lean_deg"] < 0, (sb, sc)          # bold leans in, shy hangs back
    assert sb["flick_deg"] > 15 and abs(sc["flick_deg"]) < 1, (sb, sc)
    assert sc["size"] < sb["size"] and sc["speed"] < sb["speed"], (sb, sc)


@check("the character shows up in the motion: a bold home's hello leans in")
def _(tmp):
    b = seeded(brain_with(deep_cart(tmp, 6000)))
    b.character.dials.update(boldness=0.75)
    b.expr.play("hello")
    pitch = max(b.expr.step(DT).get("head_pitch", 0.0) for _ in range(40))
    assert pitch > 12, pitch          # hello's own nod peaks at 8 deg x size, the lean adds about 10


@check("rust: after 3 months apart it's stiff again, then warms up within a few moments (Rule 5)")
def _(tmp):
    b = brain_with(deep_cart(tmp, 300, last=DAY - timedelta(days=90)))
    b.today = DAY
    pat = patina(b)
    rusty = pat.base_style("hello")["hesitate_s"]
    assert rusty > 0.15, rusty
    for _ in range(5):
        b.handle(Event("wave", source="hands"))
        b.pass_time(5)
    warm = pat.base_style("hello")["hesitate_s"]
    assert warm < 0.03, warm


@check("no rust after a normal week, and a brand new droid has none")
def _(tmp):
    b = brain_with(deep_cart(tmp / "a", 300, last=DAY - timedelta(days=5)))
    b.today = DAY
    assert patina(b).base_style("hello")["hesitate_s"] < 0.01
    fresh = brain_with(Cartridge.create(tmp / "b", on=DAY))
    assert patina(fresh).rust == 0.0


@check("the time skip: a shelved droid comes back rusty, a family's keeps deepening")
def _(tmp):
    from heirloom.sim import time_skip
    shelf = time_skip("shelved", tmp / "s", years=2, seed=5, quiet=True)
    assert shelf["year2"]["rust"] > 0.5, shelf["year2"]
    fam = time_skip("loud_family", tmp / "f", years=12, seed=5, quiet=True)
    assert fam["year12"]["deep"]["hello"] > fam["year1"]["deep"]["hello"] + 0.3, fam


@check("a year-1 snapshot opened today isn't rusty (its dates end today), a shelved one is")
def _(tmp):
    from heirloom.sim import time_skip
    time_skip("loud_family", tmp, years=3, seed=5, quiet=True)
    time_skip("shelved", tmp, years=3, seed=5, quiet=True)
    assert patina(brain_with(Cartridge.open(tmp / "loud_family_year1"))).rust == 0.0
    assert patina(brain_with(Cartridge.open(tmp / "shelved_year1"))).rust > 0.5


@check("after time apart it notices you only when you're closer, then opens back up (Rule 5)")
def _(tmp):
    b = brain_with(deep_cart(tmp, 300, last=DAY - timedelta(days=90)))
    normal = b.character.notice_distance
    shy = b.presence.cfg.notice_distance
    assert shy < normal - 0.4, (shy, normal)                # about 1.9 m instead of 2.5 m
    for _ in range(5):
        b.handle(Event("wave", source="hands"))
        b.pass_time(5)
    assert abs(b.presence.cfg.notice_distance - normal) < 0.1, b.presence.cfg.notice_distance


@check("left running with nobody around for weeks, it still gets shy")
def _(tmp):
    b = brain_with(deep_cart(tmp, 300, last=DAY))
    b.today = DAY
    normal = b.presence.cfg.notice_distance
    b.today = DAY + timedelta(days=60)
    for _ in range(70):
        b.step(1.0, None)
    assert b.presence.cfg.notice_distance < normal - 0.3, (b.presence.cfg.notice_distance, normal)


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
