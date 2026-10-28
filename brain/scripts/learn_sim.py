"""Fake owners teach the learning loop, in seconds. No headset (terminal B-roll for the video).

    python scripts/learn_sim.py               # 30 fake owners each, every scenario
    python scripts/learn_sim.py --owners 100

Scenarios (a fake owner waves every morning and reacts to the move it answers with):
    loves the wiggle    thumbs up 90% of the time for "happy", "no" 70% of the time for anything else
    wants quiet         the same, for "listen"
    only praises        thumbs up for "happy", never says no (silence is no reward, so it's slower)
    passed down         keeper A taught "happy" for 40 mornings, then keeper B wants "listen".
                        How fast B takes over, compared with a fresh droid

Prints how often it picks the owner's favourite in each block of 10 waves, as the median and the
range across owners. A fake owner is a scripted guess at people, not data: it shows the loop
works and how fast it can move, not how real people react.
"""
import argparse
import random
import statistics
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402

BLOCKS = 6           # 6 blocks of 10 waves = 60 mornings


def brain(folder: Path) -> HeirloomBrain:
    cart = Cartridge.open(folder) if (folder / "cartridge.json").exists() else Cartridge.create(folder)
    b = HeirloomBrain(play_sound=lambda n: None, cartridge=cart, learn=True)
    b.now = datetime.now().replace(hour=10, minute=0)
    return b


def mornings(b, likes: str, n: int, rng: random.Random, says_no=True) -> list[str]:
    picks = []
    for _ in range(n):
        b.handle(Event("wave", source="hands"))
        chosen = [l for l in b.decisions.lines if "chosen" in l][-1]["chosen"]
        picks.append(chosen)
        b.pass_time(1.5)
        if chosen == likes:
            if rng.random() < 0.9:
                b.handle(Event("good", source="hands"))
        elif says_no and rng.random() < 0.7:
            b.handle(Event("scold", source="voice"))
        b.pass_time(300.0)
    return picks


def curve(runs: list[list[str]], likes: str) -> str:
    cells = []
    for k in range(len(runs[0]) // 10):
        shares = [r[k * 10:(k + 1) * 10].count(likes) / 10 for r in runs]
        lo, mid, hi = min(shares), statistics.median(shares), max(shares)
        cells.append(f"{mid * 100:3.0f}% ({lo * 100:.0f}-{hi * 100:.0f})")
    return "  ".join(cells)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owners", type=int, default=30)
    args = ap.parse_args()
    n = BLOCKS * 10
    print(f"How often it answers the morning wave with the owner's favourite, per 10 waves "
          f"(median, lowest-highest of {args.owners} fake owners)")
    print(f"{'':20s}" + "  ".join(f"waves {k * 10 + 1:>2}-{k * 10 + 10:<3}  " for k in range(BLOCKS)))
    for label, likes, says_no in (("loves the wiggle", "happy", True), ("wants quiet", "listen", True),
                                  ("only praises", "happy", False)):
        runs = []
        for i in range(args.owners):
            with tempfile.TemporaryDirectory() as d:
                runs.append(mornings(brain(Path(d)), likes, n, random.Random(i), says_no))
        print(f"{label:20s}" + curve(runs, likes))

    fresh, inherited = [], []
    for i in range(args.owners):
        with tempfile.TemporaryDirectory() as d:
            fresh.append(mornings(brain(Path(d) / "fresh"), "listen", n, random.Random(1000 + i)))
            a = brain(Path(d) / "old")
            mornings(a, "happy", 40, random.Random(i))
            a.cartridge.handoff("keeper B")
            inherited.append(mornings(brain(Path(d) / "old"), "listen", n, random.Random(1000 + i)))
    print("\nPassed down: keeper B wants quiet, after keeper A taught the wiggle for 40 mornings")
    print(f"{'fresh droid':20s}" + curve(fresh, "listen"))
    print(f"{'A\'s droid':20s}" + curve(inherited, "listen"))
    print(f"{'  still wiggling':20s}" + curve(inherited, "happy"))
    print("\nFake owners are scripted guesses, not people. This shows the loop works and how fast it can move.")


if __name__ == "__main__":
    main()
