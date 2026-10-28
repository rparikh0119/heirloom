"""Checks dialect drift: family chirps bend toward the versions the household reacts warmly to.
Run:  python tests/test_dialect_drift.py
"""
import random
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.sim import time_skip  # noqa: E402
from heirloom.sound import chirps as C  # noqa: E402
from heirloom.sound import genome as G  # noqa: E402
from heirloom.wear.dialect import CAP_PITCH  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def worn(tmp: Path, learn=True, hand_down=False):
    """The desk student after a year, at 10:01, so a wave is its 10 am moment."""
    time_skip("desk_student", tmp, years=1, seed=42, quiet=True, snapshots={"year1": 365})
    if hand_down:
        Cartridge.open(tmp / "desk_student_year1").handoff("the next keeper")
    sounds = []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=Cartridge.open(tmp / "desk_student_year1"), learn=learn)
    b.now = datetime.now().replace(hour=10, minute=1, second=0, microsecond=0)
    return b, sounds


def dialect(b):
    return next(w for w in b.wear if w.name == "dialect")


def wave_id(b):
    return b.moment


def page_rec(b, mid):
    return b.cartridge.read_page(b.cartridge.active.id, "dialect").get(mid)


# ---------------------------------------------------------------------------------------------

@check("learning off: the family chirp plays exactly as stored, and nothing drifts")
def _(tmp):
    b, sounds = worn(tmp, learn=False)
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    assert sounds[-1] == f"m:{mid}", sounds
    b.pass_time(1.0)
    b.handle(Event("good", source="hands"))
    assert "drift" not in page_rec(b, mid)


@check("learning on: each play is a slightly varied version of the family chirp")
def _(tmp):
    b, sounds = worn(tmp)
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    assert sounds[-1] == f"m:{mid}~", sounds
    played = G.capture(f"m:{mid}~")
    stored = page_rec(b, mid)["notes"]
    assert len(played) == len(stored) and 0.96 < played[0]["f0"] / stored[0]["f0"] < 1.04


@check("a thumbs up nudges the chirp toward the version that played. Identity stays locked")
def _(tmp):
    b, _ = worn(tmp)
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    before = [dict(n) for n in page_rec(b, mid)["notes"]]
    jitter = b._decided[b.rewards.open.decision_id]["chirp"][1]
    b.pass_time(1.0)
    b.handle(Event("good", source="hands"))
    rec = page_rec(b, mid)
    after = rec["notes"]
    assert rec["drift"]["steps"] == 1, rec
    moved, wanted = after[0]["f0"] / before[0]["f0"], jitter["pitch"]
    assert (moved - 1) * (wanted - 1) > 0 and abs(moved - 1) < abs(wanted - 1), (moved, wanted)
    assert [G.direction(n) for n in after] == [G.direction(n) for n in before] and len(after) == len(before)


@check("silence and a \"no\" don't move it")
def _(tmp):
    b, _ = worn(tmp)
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    b.pass_time(10.0)
    b.handle(Event("wave", source="hands"))
    b.pass_time(1.0)
    b.handle(Event("scold", source="voice"))
    assert "drift" not in page_rec(b, mid)


@check("drift is capped, and it never drifts into another chirp (homonym filter)")
def _(tmp):
    b, _ = worn(tmp)
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    d = dialect(b)
    origin = [dict(n) for n in page_rec(b, mid)["notes"]]
    for _ in range(300):
        d.nudge(mid, {"pitch": 1.03, "len": [1.08] * len(origin), "wobble": 1.2})
    rec = page_rec(b, mid)
    assert rec["notes"][0]["f0"] / origin[0]["f0"] <= 1 + CAP_PITCH + 1e-9, rec["drift"]
    others = [G.capture(n) for n in C.CHIRPS if not n.startswith("m:")]
    others += [c["notes"] for k, c in d.chirps.items() if k != mid]
    assert min(G.distance(rec["notes"], o) for o in others) >= G.MIN_DIST


@check("passed down: drift changes the new keeper's copy, the old keeper's chirp stays as it was")
def _(tmp):
    b, _ = worn(tmp, hand_down=True)
    old = [dict(n) for n in b.cartridge.read_page("L1", "dialect")["L1.m03"]["notes"]]
    b.handle(Event("wave", source="hands"))
    mid = wave_id(b)
    assert mid.startswith("L2."), mid
    for _ in range(5):
        b.pass_time(1.0)
        b.handle(Event("good", source="hands"))
        b.pass_time(10.0)
        b.handle(Event("wave", source="hands"))
    assert page_rec(b, mid)["drift"]["steps"] >= 1
    assert b.cartridge.read_page("L1", "dialect")["L1.m03"]["notes"] == old


@check("it follows taste: a home that warms to higher versions drifts higher than one that doesn't care")
def _(tmp):
    def household(folder, likes_high: bool, seed: int) -> float:
        b, _ = worn(folder)
        rng = random.Random(seed)
        mid = None
        for _ in range(90):
            b.handle(Event("wave", source="hands"))
            mid = mid or wave_id(b)
            jitter = b._decided[b.rewards.open.decision_id]["chirp"][1]["pitch"]
            b.pass_time(1.0)
            if (jitter > 1.0) if likes_high else (rng.random() < 0.5):
                b.handle(Event("good", source="hands"))
            b.pass_time(300.0)
        return page_rec(b, mid).get("drift", {}).get("pitch", 1.0)

    high = [household(tmp / f"h{i}", True, i) for i in range(4)]
    meh = [household(tmp / f"m{i}", False, i) for i in range(4)]
    assert min(high) > 1.015, high
    assert sum(abs(x - 1) for x in meh) / 4 < sum(x - 1 for x in high) / 4, (high, meh)


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
