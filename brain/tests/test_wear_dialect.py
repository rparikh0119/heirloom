"""Checks dialect v0: family chirps for moments, distinct, kept, passed down.
Run:  python tests/test_wear_dialect.py
"""
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.sound import chirps as C  # noqa: E402
from heirloom.sound import genome as G  # noqa: E402

CHECKS = []
START = date(2026, 10, 1)


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def setup(tmp, cart=None):
    cart = cart or Cartridge.create(tmp / "c", on=START)
    sounds = []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=cart)
    return cart, b, sounds


def at(b, day, hh, mm, what="wave"):
    b.now = datetime.combine(START + timedelta(days=day), datetime.min.time()) + timedelta(hours=hh, minutes=mm)
    b.today = b.now.date()
    b.handle(Event(what, source="hands"))
    b.pass_time(120)


def habit(b, hh=9, what="wave", days=(0, 3, 6, 9, 12, 15)):
    for i, d in enumerate(days):
        at(b, d, hh, (i * 7) % 15, what)


def core():
    return {n: G.capture(n) for n in list(C.CHIRPS) if not n.startswith("m:")}


@check("reading a core chirp as a genome gives back the same sound")
def _(tmp):
    for name in ("hello", "happy", "love", "sleepy"):
        a = np.concatenate(C.CHIRPS[name](1.0, 1.0))
        b = np.concatenate(G.recipe(G.capture(name))(1.0, 1.0))
        assert len(a) == len(b) and np.allclose(a, b), name


@check("before the habit it says the plain hello. At the habit, its family hello")
def _(tmp):
    cart, b, sounds = setup(tmp)
    habit(b)                                       # the 6th morning makes it a moment
    assert sounds[:5] == ["hello"] * 5, sounds
    sounds.clear()
    at(b, 18, 9, 5)
    assert sounds == ["m:L1.m01"], sounds
    sounds.clear()
    at(b, 18, 16, 0)                               # an afternoon wave is just a hello
    assert sounds == ["hello"], sounds


@check("the family hello is related to hello but clearly its own chirp")
def _(tmp):
    cart, b, _ = setup(tmp)
    habit(b)
    at(b, 18, 9, 5)
    rec = cart.read_page("L1", "dialect")["L1.m01"]
    assert rec["parent"] == "hello"
    for name, g in core().items():
        assert G.distance(rec["notes"], g) >= G.MIN_DIST, (name, G.distance(rec["notes"], g))


@check("it plays everywhere a core chirp plays (bodies render it by name)")
def _(tmp):
    cart, b, _ = setup(tmp)
    habit(b)
    at(b, 18, 9, 5)
    s = C.render("m:L1.m01")
    assert 0.05 < len(s) / C.SR <= G.LONGEST + 0.1 and np.abs(s).max() <= 1.0


@check("it keeps the same chirp: after a restart it still says it the same way")
def _(tmp):
    cart, b, _ = setup(tmp)
    habit(b)
    at(b, 18, 9, 5)
    first = cart.read_page("L1", "dialect")["L1.m01"]["notes"]
    cart2 = Cartridge.open(tmp / "c")
    _, b2, sounds = setup(tmp, cart2)
    at(b2, 19, 9, 2)
    assert sounds == ["m:L1.m01"] and cart2.read_page("L1", "dialect")["L1.m01"]["notes"] == first


@check("two droids with the same 9 am habit grow different family hellos")
def _(tmp):
    c1, b1, _ = setup(tmp / "a")
    c2, b2, _ = setup(tmp / "b")
    for b in (b1, b2):
        habit(b)
        at(b, 18, 9, 5)
    assert c1.read_page("L1", "dialect")["L1.m01"]["notes"] != c2.read_page("L1", "dialect")["L1.m01"]["notes"]


@check("a household with many habits: every family chirp is distinct from every other")
def _(tmp):
    cart, b, _ = setup(tmp)
    plan = [(8, "wake"), (9, "wave"), (11, "good"), (13, "wave"), (15, "curious"), (17, "good"),
            (19, "heart"), (21, "wave"), (23, "sleep")]
    for d in range(0, 40, 2):        # three waves a day dilute each other, so it takes more days to trust them
        for hh, what in plan:
            at(b, d, hh, 0, what)
    for hh, what in plan:
        at(b, 41, hh, 0, what)
    page = cart.read_page("L1", "dialect")
    assert len(page) == 9, sorted(page)
    chirps = [r["notes"] for r in page.values()]
    for i, a in enumerate(chirps):
        for bb in chirps[i + 1:]:
            assert G.distance(a, bb) >= G.MIN_DIST


@check("passed down: the new owner's 9 am wave wakes the moment AND the old family hello")
def _(tmp):
    cart, b, _ = setup(tmp)
    habit(b)
    at(b, 18, 9, 5)
    old = cart.read_page("L1", "dialect")["L1.m01"]["notes"]
    cart.handoff("granddaughter", on=START + timedelta(days=30))
    _, b2, sounds = setup(tmp, cart)
    at(b2, 31, 9, 10)
    rec = cart.read_page("L2", "dialect")["L2.m01"]
    assert sounds == ["m:L2.m01"] and rec["from"] == "L1.m01" and rec["notes"] == old, (sounds, rec)


@check("without a cartridge nothing changes: plain chirps only")
def _(tmp):
    sounds = []
    b = HeirloomBrain(play_sound=sounds.append)
    b.handle(Event("wave", source="hands"))
    assert sounds == ["hello"]


@check("a broken dialect page is refused with a clear message")
def _(tmp):
    from heirloom.wear.dialect import DialectWear
    try:
        DialectWear().validate({"L1.m01": {"parent": "hello", "notes": [{"f0": 900, "f1": 0, "dur": 0.1}]}}, "dialect.json")
    except ValueError as e:
        assert "positive number" in str(e)
        return
    raise AssertionError("accepted a note with no end pitch")


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
