"""Checks that a moment can be filmed: the demo clock, the family chirp, and what the overlay gets.
Run:  python tests/test_demo_moment.py
"""
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.sim import time_skip  # noqa: E402
from run import _clock_offset  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def worn(tmp: Path, at: str):
    """The desk student after a year, on the desk with the clock reading `at` today."""
    time_skip("desk_student", tmp, years=1, seed=42, quiet=True, snapshots={"year1": 365})
    sounds = []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=Cartridge.open(tmp / "desk_student_year1"),
                      wear_ignores={"unity"})
    h, m = (int(x) for x in at.split(":"))
    b.now = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
    return b, sounds


def wave_moment(b) -> str:
    return next(mid for mid, m in b.moments.items() if m["cue"] == "wave")


# ---------------------------------------------------------------------------------------------

@check("a real wave at 10:01 is the 10 am moment and answers in the family chirp")
def _(tmp):
    b, sounds = worn(tmp, "10:01")
    b.handle(Event("wave", source="hands"))
    mid = wave_moment(b)
    assert b.moment == mid, b.moment
    assert sounds[-1] == f"m:{mid}", sounds


@check("the same wave at 14:00 is just a hello, in the core chirp")
def _(tmp):
    b, sounds = worn(tmp, "14:00")
    b.handle(Event("wave", source="hands"))
    assert b.moment is None
    assert sounds[-1] == "hello", sounds


@check("a Unity key press doesn't count as the moment (keys never leave wear)")
def _(tmp):
    b, sounds = worn(tmp, "10:01")
    b.handle(Event("wave", source="unity"))
    assert b.moment is None
    assert sounds[-1] == "hello", sounds


@check("the overlay gets the moment, its line, the chirp, every habit and the clock")
def _(tmp):
    b, _ = worn(tmp, "10:01")
    b.demo_clock = True
    b.handle(Event("wave", source="hands"))
    ws = b.wear_state()
    assert ws["moment"].startswith("wave around 10:"), ws["moment"]
    assert "days since" in ws["moment_detail"], ws["moment_detail"]
    assert ws["moment_chirp"] == "family chirp", ws["moment_chirp"]
    assert ws["moment_lines"][0].startswith("seen on ") and "keeper L1" in ws["moment_lines"][1], ws["moment_lines"]
    assert len(ws["habits"]) == 4 and ws["habits"][0].startswith("wave around 10:"), ws["habits"]
    assert ws["habit_now"] == 0
    assert ws["clock"] == "10:01" and ws["clock_demo"] is True
    json.dumps(ws)      # plain JSON, so Unity's JsonUtility can read it


@check("passed down: a new keeper's 10 am wave wakes the old moment, with the old chirp and its lineage")
def _(tmp):
    b, _ = worn(tmp, "10:01")
    cart = b.cartridge
    cart.handoff("the next keeper")
    sounds = []
    b2 = HeirloomBrain(play_sound=sounds.append, cartridge=Cartridge.open(tmp / "desk_student_year1"))
    b2.now = b.now
    b2.handle(Event("wave", source="hands"))
    ws = b2.wear_state()
    assert ws["moment_chirp"] == "family chirp, passed down", ws
    assert any(l.startswith("passed down from keeper L1") for l in ws["moment_lines"]), ws["moment_lines"]
    assert ws["habits"].count("wave around 10:03") == 1 and ws["habit_now"] == 0, ws["habits"]
    assert ws["habits"][1].endswith(" · L1"), ws["habits"]       # the 3:30 break is still the old keeper's


@check("the moment lets go after 90 s and the overlay clears it")
def _(tmp):
    b, _ = worn(tmp, "10:01")
    b.handle(Event("wave", source="hands"))
    for _ in range(160):              # released on the next once-a-minute tick after 90 s
        b.now += timedelta(seconds=1)
        b.step(1.0, None)
    assert b.moment is None
    assert b.wear_state()["moment"] == ""


@check("without a cartridge the overlay fields are there and empty")
def _(tmp):
    ws = HeirloomBrain(play_sound=lambda n: None).wear_state()
    assert ws["moment"] == "" and ws["habits"] == [] and ws["clock_demo"] is False


@check("--clock 9:58 moves the clock to 9:58 today, and bad times are refused")
def _(tmp):
    offset = _clock_offset("9:58")
    t = datetime.now() + offset
    assert (t.hour, t.minute) == (9, 58) and t.date() == datetime.now().date()
    for bad in ("25:00", "9", "nine"):
        try:
            _clock_offset(bad)
        except SystemExit:
            continue
        raise AssertionError(f"accepted {bad!r}")


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
