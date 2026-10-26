"""Checks the moment registry (proposed D99): the droid noticing what keeps happening at the same time.
Run:  python tests/test_wear_moments.py
"""
import random
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402

CHECKS = []
START = date(2026, 10, 1)


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def setup(tmp):
    cart = Cartridge.create(tmp / "c", on=START)
    b = HeirloomBrain(play_sound=lambda n: None, cartridge=cart)
    return cart, b


def moments_of(b):
    return next(w for w in b.wear if w.name == "moments")


def at(b, day: int, hh: int, mm: int, what: str = "wave"):
    """Pretend it's this day and time, then do something."""
    b.now = datetime.combine(START + timedelta(days=day), datetime.min.time()) + timedelta(hours=hh, minutes=mm)
    b.today = b.now.date()
    b.handle(Event(what, source="hands"))
    b.pass_time(120)                      # two minutes later, so moments don't overlap


def morning_waves(b, days=(0, 3, 6, 9, 12, 15)):
    for i, d in enumerate(days):
        at(b, d, 9, (i * 7) % 15)          # 9:00 to 9:14, a little different every day


@check("one busy week isn't a moment: 5 mornings in a row is not a habit yet")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b, days=(0, 1, 2, 3, 4))
    assert cart.read_page("L1", "moments")["moments"] == {}


@check("waving around 9 on six days over two weeks becomes a moment")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    ms = cart.read_page("L1", "moments")["moments"]
    assert list(ms) == ["L1.m01"], ms
    m = ms["L1.m01"]
    assert m["cue"] == "wave" and 540 <= m["at"] <= 555 and m["days"] == 6, m
    assert m["name"].startswith("wave around 9:"), m["name"]


@check("random times never become a moment")
def _(tmp):
    cart, b = setup(tmp)
    rng = random.Random(4)
    for d in range(0, 40, 2):
        at(b, d, rng.randrange(24), rng.randrange(60))
    assert cart.read_page("L1", "moments")["moments"] == {}


@check("waving at random all day for months never fakes a habit, but a real 9 am wave still stands out")
def _(tmp):
    cart, b = setup(tmp)
    rng = random.Random(11)
    for d in range(60):
        for _ in range(2):
            at(b, d, rng.randrange(9, 23), rng.randrange(60))
    assert cart.read_page("L1", "moments")["moments"] == {}, cart.read_page("L1", "moments")["moments"]
    for d in range(60, 80):
        if d % 7 < 5:
            at(b, d, 9, rng.randrange(10))
    names = [m["name"] for m in cart.read_page("L1", "moments")["moments"].values()]
    assert len(names) == 1 and names[0].startswith("wave around 9:"), names


@check("the same thing at two times of day is two moments (hello at 9, good night at 11 pm)")
def _(tmp):
    cart, b = setup(tmp)
    for d in (0, 2, 4, 6, 8, 10, 12, 14, 16):     # two habits of one event take a few more days to tell apart
        at(b, d, 9, 5)
        at(b, d, 23, 0)
    ms = cart.read_page("L1", "moments")["moments"]
    assert sorted(m["at"] for m in ms.values()) == [545, 1380], ms


@check("a moment just before midnight and just after is one moment, not two")
def _(tmp):
    cart, b = setup(tmp)
    for i, d in enumerate((0, 3, 6, 9, 12, 15)):
        at(b, d, 23 if i % 2 else 0, 50 if i % 2 else 10, "sleep")
    ms = cart.read_page("L1", "moments")["moments"]
    assert len(ms) == 1 and _near_midnight(next(iter(ms.values()))["at"]), ms


def _near_midnight(m):
    return m < 30 or m > 1410


@check("when it happens again at its usual time, the brain knows which moment it is")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    at(b, 18, 9, 20)
    assert b.moment == "L1.m01", b.moment
    b.pass_time(100)
    at(b, 18, 15, 0)                       # same wave, wrong time of day
    assert b.moment is None, b.moment
    assert cart.read_page("L1", "moments")["moments"]["L1.m01"]["days"] == 7


@check("with a pretend date and no clock (the time skip), it learns nothing instead of nonsense")
def _(tmp):
    cart, b = setup(tmp)
    for d in range(20):
        b.today = START + timedelta(days=d)
        b.handle(Event("wave", source="sim"))
    assert cart.read_page("L1", "moments") == {}


@check("passed down: the new owner waving at 9 wakes the old moment, with its lineage")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    cart.handoff("granddaughter", on=START + timedelta(days=30))
    b2 = HeirloomBrain(play_sound=lambda n: None, cartridge=cart)
    at(b2, 31, 9, 10)
    ms = cart.read_page("L2", "moments")["moments"]
    assert list(ms) == ["L2.m01"] and ms["L2.m01"]["from"] == "L1.m01", ms
    line = moments_of(b2).explain("L2.m01")
    assert "used to do this with keeper L1" in line and "first home" in line, line


@check("an old moment only wakes once (the next morning counts toward the new one)")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    cart.handoff("granddaughter", on=START + timedelta(days=30))
    b2 = HeirloomBrain(play_sound=lambda n: None, cartridge=cart)
    at(b2, 31, 9, 10)
    at(b2, 32, 9, 5)
    ms = cart.read_page("L2", "moments")["moments"]
    assert list(ms) == ["L2.m01"] and ms["L2.m01"]["days"] == 2, ms


@check("a faded past keeps its moments asleep, never deleted")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    cart.handoff("new home", on=START + timedelta(days=30))
    cart.set_weight("L1", "fade", on=START + timedelta(days=30))
    b2 = HeirloomBrain(play_sound=lambda n: None, cartridge=cart)
    b2.now = datetime.combine(START + timedelta(days=200), datetime.min.time())
    b2.today = b2.now.date()
    moments_of(b2).apply(b2)
    assert "L1.m01" in b2.moments and b2.moments["L1.m01"]["dormant"], b2.moments


@check("the owner can name a moment, and the name sticks")
def _(tmp):
    cart, b = setup(tmp)
    morning_waves(b)
    moments_of(b).tag("L1.m01", "when Riya sits down")
    assert cart.read_page("L1", "moments")["moments"]["L1.m01"]["tag"] == "when Riya sits down"
    assert moments_of(b).explain("L1.m01").startswith("when Riya sits down")


@check("raw notes older than 60 days are dropped, so the page stays small")
def _(tmp):
    cart, b = setup(tmp)
    at(b, 0, 14, 0, "good")
    at(b, 70, 10, 0, "good")
    seen = cart.read_page("L1", "moments")["seen"]["good"]
    assert list(seen) == [(START + timedelta(days=70)).isoformat()], seen


@check("reflexes and 'huh?' are never moments")
def _(tmp):
    cart, b = setup(tmp)
    for d in (0, 3, 6, 9, 12, 15):
        b.now = datetime.combine(START + timedelta(days=d), datetime.min.time()) + timedelta(hours=9)
        b.today = b.now.date()
        b.handle(Event("hearing", source="voice"))
    assert cart.read_page("L1", "moments") == {}


@check("a broken page is refused with a clear message")
def _(tmp):
    from heirloom.wear.moments import MomentsWear
    try:
        MomentsWear().validate({"moments": {"L1.m01": {"cue": "wave", "at": 2000, "first": "x", "last": "x", "days": 1}}}, "moments.json")
    except ValueError as e:
        assert "not a time of day" in str(e)
        return
    raise AssertionError("accepted a moment at minute 2000")


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
