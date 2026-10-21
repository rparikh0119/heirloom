"""Time skip: let synthetic households live with Heirloom for years, in seconds (D46).

    python scripts/time_skip.py                          # every household, 12 years
    python scripts/time_skip.py --profile loud_family    # just one
    python scripts/time_skip.py --years 5 --seed 7

Writes worn cartridges to brain/cartridges/sim/, e.g. loud_family_day1, _year1, _year12.
Run one in Unity with:  python scripts/run.py --body unity --cartridge cartridges/sim/loud_family_year12

Households live in brain/sim/households/. Add a JSON file to make a new one.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.sim import HOUSEHOLDS_DIR, time_skip  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "cartridges" / "sim"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=None, help="one household (default: all of them)")
    parser.add_argument("--years", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    profiles = [args.profile] if args.profile else sorted(p.stem for p in HOUSEHOLDS_DIR.glob("*.json"))
    base = {"sass": 0.5, "boldness": 0.5, "energy": 0.5, "curiosity": 0.5}
    print(f"Out of the box: " + "  ".join(f"{k} {v:.3f}" for k, v in base.items()) + "\n")
    for p in profiles:
        t0 = time.perf_counter()
        print(f"{p}  ({args.years} years, seed {args.seed})")
        r = time_skip(p, OUT, years=args.years, seed=args.seed)
        last = r[f"year{args.years}"]
        print(f"  -> sulks {last['sulk_s']:.1f} s (new: 6.0 s), notices you at {last['notice_m']:.2f} m (new: 2.50 m)"
              f"   [{time.perf_counter() - t0:.1f} s]\n")
    print(f"Cartridges written to {OUT}")


if __name__ == "__main__":
    main()
