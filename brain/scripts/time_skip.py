"""Time skip: synthetic households live with Heirloom for years, in seconds (D46).

    python scripts/time_skip.py                          # every household, 12 years, one run each
    python scripts/time_skip.py --profile loud_family    # just one
    python scripts/time_skip.py --sweep 30               # 30 runs across every unknown range. Use this before claiming anything

Writes worn cartridges to brain/cartridges/sim/, e.g. loud_family_day1, _month1, _year1, _year12.
Run one in Unity:  python scripts/run.py --body unity --cartridge cartridges/sim/loud_family_year12

Every number in brain/sim/households/*.json is declared as data (with its derivation), unknown
(a range that gets swept) or scenario (what the household is). See docs/time-skip-provenance.md.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.sim import HOUSEHOLDS_DIR, PARAMS, load_household, sweep, time_skip  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "cartridges" / "sim"
SHOW = ("sass", "boldness", "energy", "curiosity", "sulk_s", "notice_m")
MOVES = ("worn_hello", "worn_happy", "worn_offended")     # patina: 0 = brand new, 1 = worn smooth


def provenance_line(profile: str) -> str:
    prov = load_household(profile)["provenance"]
    kinds = [prov[p]["kind"] for p in PARAMS]
    return f"  numbers: {kinds.count('data')} data, {kinds.count('unknown')} unknown (swept), mix = scenario"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=None, help="one household (default: all of them)")
    parser.add_argument("--years", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sweep", type=int, default=0, help="runs across every unknown range (e.g. 30)")
    args = parser.parse_args()

    profiles = [args.profile] if args.profile else sorted(p.stem for p in HOUSEHOLDS_DIR.glob("*.json"))
    print("Out of the box: every dial 0.500, sulks 6.0 s, notices you at 2.50 m, every move brand new (patina 0.00)\n")
    for p in profiles:
        t0 = time.perf_counter()
        print(f"{p}  ({args.years} years)")
        print(provenance_line(p))
        if args.sweep:
            stats = sweep(p, runs=args.sweep, years=args.years, seed=args.seed)
            for snap in ("month1", "year1", f"year{args.years}"):
                cells = [f"{k} {lo:.2f}-{hi:.2f}" for k, (lo, mid, hi) in
                         ((k, stats[snap][k]) for k in SHOW)]
                print(f"  {snap:7s} " + "   ".join(cells))
                moves = [f"{k[5:]} {stats[snap][k][0]:.2f}-{stats[snap][k][2]:.2f}" for k in MOVES]
                print(f"  {'':7s} patina: " + "   ".join(moves))
            print(f"  ranges = lowest to highest across {args.sweep} runs   [{time.perf_counter() - t0:.1f} s]\n")
        else:
            time_skip(p, OUT, years=args.years, seed=args.seed)
            print(f"  single run at the middle of every unknown range. Not a claim: use --sweep   "
                  f"[{time.perf_counter() - t0:.1f} s]\n")
    if not args.sweep:
        print(f"Cartridges written to {OUT}")


if __name__ == "__main__":
    main()
