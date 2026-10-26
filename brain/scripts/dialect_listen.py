"""Hear a droid's family chirps next to the core chirps they came from. Run on your PC (no headset):

    python scripts/dialect_listen.py                                   # the simulated desk student, year 1
    python scripts/dialect_listen.py --cartridge cartridges/sim/desk_student_month1

Writes WAV files into <cartridge>/dialect_listen/ and one file that plays them all in a row:
core hello, then the family hello for the 10 am moment, and so on. Open them and listen.

Run the time skip first if the sim cartridges aren't there:  python scripts/time_skip.py --profile desk_student
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.sound.chirps import SR, render, to_wav_bytes  # noqa: E402

DEFAULT = Path(__file__).resolve().parents[1] / "cartridges" / "sim" / "desk_student_year1"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartridge", default=str(DEFAULT))
    args = ap.parse_args()
    folder = Path(args.cartridge)
    if not (folder / "cartridge.json").exists():
        print(f"No cartridge at {folder}. Run:  python scripts/time_skip.py --profile desk_student")
        return
    cart = Cartridge.open(folder)
    brain = HeirloomBrain(play_sound=lambda n: None, cartridge=cart)
    dialect = next(w for w in brain.wear if w.name == "dialect")
    moments = getattr(brain, "moments", {}) or {}
    if not moments:
        print("This droid hasn't noticed any habits yet, so it has no family chirps.")
        return

    out = folder / "dialect_listen"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.wav"):
        old.unlink()
    row, gap = [], np.zeros(int(SR * 0.6))
    for i, (mid, m) in enumerate(sorted(moments.items(), key=lambda kv: kv[1]["at"]), 1):
        parent = next((r.sound for r in brain.reactions if m["cue"] in r.when and r.sound and not r.only_while), None)
        if parent is None:
            continue
        name = dialect.voice(mid, parent)
        label = (m.get("tag") or m["name"]).replace(":", "-").replace(" ", "_")
        core, family = render(parent, variation=0.0), render(name, variation=0.0)
        (out / f"{i:02d}_{label}_A_core_{parent}.wav").write_bytes(to_wav_bytes(core))
        (out / f"{i:02d}_{label}_B_family.wav").write_bytes(to_wav_bytes(family))
        row += [core, gap * 0.5, family, gap * 1.5]
        print(f"  {i:02d}  {m['name']:24s}  core \"{parent}\"  ->  family chirp {name}")
    (out / "00_all_in_a_row.wav").write_bytes(to_wav_bytes(np.concatenate(row)))
    print(f"\nWrote them to {out}\nStart with 00_all_in_a_row.wav: each pair is core first, then the family version.")


if __name__ == "__main__":
    main()
