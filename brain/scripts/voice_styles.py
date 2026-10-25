"""Hear how your voice memories sound in each style, to pick one by ear.

    python scripts/voice_styles.py --cartridge cartridges/fresh_test

Takes the newest voice memory in that cartridge (say "record this" to the droid first) and writes
three versions next to it in journal/voice/styles/. Open them on your PC and listen. Then set STYLE
in brain/heirloom/sound/tape.py to the one you like.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.journal import Journal  # noqa: E402
from heirloom.sound.chirps import to_wav_bytes  # noqa: E402
from heirloom.sound.tape import STYLES, framed, tape  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartridge", required=True)
    args = ap.parse_args()
    journal = Journal(Path(args.cartridge) / "journal")
    found = journal.voices()
    if not found:
        print("No voice memories yet. Run the droid with this cartridge and say \"record this\" first.")
        return
    path, note = found[-1]
    samples, sr = journal.load_voice(path)
    out = path.parent / "styles"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.wav"):
        old.unlink()                                        # fresh set every time
    (out / "0_original.wav").write_bytes(to_wav_bytes(samples / max(1e-6, abs(samples).max()) * 0.8, sr))
    for i, name in enumerate(STYLES, 1):
        (out / f"{i}_{name}.wav").write_bytes(to_wav_bytes(framed(tape(samples, sr, style=name), sr), sr))
    print(f"From {path.name}: \"{note.get('said', '')}\"")
    print(f"Wrote 0_original, " + ", ".join(f"{i}_{k}" for i, k in enumerate(STYLES, 1)) + f" to {out}")


if __name__ == "__main__":
    main()
