"""Checks the time skip, especially that no number can sneak in without a source.
Run:  python tests/test_time_skip.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.sim import HOUSEHOLDS_DIR, load_household, sweep, time_skip  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def broken(tmp: Path, change) -> Path:
    """A copy of quiet_solo with one thing broken, in a temp folder."""
    raw = json.loads((HOUSEHOLDS_DIR / "quiet_solo.json").read_text(encoding="utf-8"))
    change(raw)
    (tmp / "bad.json").write_text(json.dumps(raw), encoding="utf-8")
    return tmp


def refuses(tmp, change) -> str:
    try:
        load_household("bad", broken(tmp, change))
    except ValueError as e:
        return str(e)
    raise AssertionError("accepted a household it should refuse")


# ---------------------------------------------------------------------------------------------

@check("every real household passes the provenance check")
def _(tmp):
    for p in sorted(HOUSEHOLDS_DIR.glob("*.json")):
        load_household(p.stem)


@check("a number with no provenance is refused")
def _(tmp):
    assert "no provenance" in refuses(tmp, lambda r: r["provenance"].pop("weekend"))


@check("an unknown written as a single number is refused (it must be a range)")
def _(tmp):
    def change(r):
        r["novelty"]["peak"] = 2.0
    assert "must be a range" in refuses(tmp, change)


@check("'data' without a derivation is refused")
def _(tmp):
    assert "derivation" in refuses(tmp, lambda r: r["provenance"]["weekend"].pop("derivation"))


@check("a mix not declared as a scenario is refused")
def _(tmp):
    assert "scenario" in refuses(tmp, lambda r: r["provenance"].pop("mix"))


@check("same household + same seed = the same droid")
def _(tmp):
    a = time_skip("quiet_solo", tmp / "a", years=1, seed=7, quiet=True)
    b = time_skip("quiet_solo", tmp / "b", years=1, seed=7, quiet=True)
    assert a["year1"]["dials"] == b["year1"]["dials"]


@check("the worn cartridge records the profile, seed and every value used (D46)")
def _(tmp):
    time_skip("loud_family", tmp, years=1, seed=3, quiet=True)
    src = Cartridge.open(tmp / "loud_family_year1").active.source
    assert src["type"] == "simulated" and src["profile"] == "loud_family" and src["seed"] == 3
    assert "novelty.peak" in src["params"] and "weekend" in src["params"]


@check("a sweep reports lowest <= median <= highest for every dial")
def _(tmp):
    stats = sweep("quiet_solo", runs=3, years=1, seed=2)
    for snap in stats.values():
        for lo, mid, hi in snap.values():
            assert lo <= mid <= hi


@check("with a routine, the time skip finds the household's habits and nothing else")
def _(tmp):
    r = time_skip("desk_student", tmp, years=1, seed=5, quiet=True,
                  snapshots={"month1": 30, "year1": 365})
    found = sorted(n.split(" around ")[0] for n in r["year1"]["found"].values())
    assert found == ["curious", "good", "sleep", "wave"], r["year1"]["found"]


@check("without a routine there's no clock, so no moments (old households unchanged)")
def _(tmp):
    r = time_skip("quiet_solo", tmp, years=1, seed=5, quiet=True, snapshots={"year1": 365})
    assert r["year1"]["found"] == {}


@check("a routine not declared as a scenario is refused")
def _(tmp):
    raw = json.loads((HOUSEHOLDS_DIR / "desk_student.json").read_text(encoding="utf-8"))
    raw["provenance"].pop("routine")
    (tmp / "bad.json").write_text(json.dumps(raw), encoding="utf-8")
    try:
        load_household("bad", tmp)
    except ValueError as e:
        assert "routine must be declared" in str(e)
        return
    raise AssertionError("accepted an undeclared routine")


@check("a snapshot put on the desk today keeps its moments awake (dates shifted like patina)")
def _(tmp):
    from datetime import date
    time_skip("desk_student", tmp, years=2, seed=5, quiet=True, snapshots={"year1": 365, "year2": 730})
    page = Cartridge.open(tmp / "desk_student_year1").read_page("L1", "moments")
    last = max(m["last"] for m in page["moments"].values())
    assert (date.today() - date.fromisoformat(last)).days <= 3, last


@check("taste: the loud family's droid learns the happy wiggle for waves, and keeper habits make it quicker and bigger")
def _(tmp):
    time_skip("loud_family", tmp, years=1, seed=3, quiet=True, snapshots={"year1": 365})
    cart = Cartridge.open(tmp / "loud_family_year1")
    arms = cart.read_page("L1", "responses")["buckets"]["wave|anytime"]
    rate = {a: (ev[0] + 1) / (sum(ev) + 2) for a, ev in arms.items()}
    assert max(rate, key=rate.get) == "happy", arms
    style = cart.read_page("L1", "habits")["style"]
    assert style["tempo"] > 1.0 and style["amplitude"] > 0.18, style


@check("taste: the desk student's routine chirps drift lower, the way it likes them")
def _(tmp):
    time_skip("desk_student", tmp, years=1, seed=42, quiet=True, snapshots={"year1": 365})
    cart = Cartridge.open(tmp / "desk_student_year1")
    moments = cart.read_page("L1", "moments")["moments"]
    dialect = cart.read_page("L1", "dialect")
    hello = next(mid for mid, m in moments.items() if m["cue"] == "wave")
    assert dialect[hello]["drift"]["pitch"] < 0.98, dialect[hello]["drift"]


@check("a household with no taste or keeper runs exactly as before: no learning pages")
def _(tmp):
    time_skip("quiet_solo", tmp, years=1, seed=1, quiet=True, snapshots={"year1": 365})
    cart = Cartridge.open(tmp / "quiet_solo_year1")
    assert cart.read_page("L1", "responses") == {} and cart.read_page("L1", "habits") == {}


@check("a taste must be a declared scenario and only name real choices")
def _(tmp):
    def change(r):
        r["taste"] = {"favourite": {"wave": "dance"}, "praise": 0.5, "says_no": 0.1}
        r["provenance"]["taste"] = {"kind": "scenario", "source": "test"}
    assert "isn't a choice" in refuses(tmp, change)

    def undeclared(r):
        r["taste"] = {"favourite": {"wave": "happy"}, "praise": 0.5, "says_no": 0.1}
    assert "scenario" in refuses(tmp, undeclared)


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
