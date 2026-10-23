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
