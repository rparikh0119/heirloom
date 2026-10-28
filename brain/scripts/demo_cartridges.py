"""Build every cartridge the demo footage needs, fresh, in one go. Run it right before filming,
so the simulated years end today and nothing reads as months on a shelf.

    python scripts/demo_cartridges.py

Writes brain/cartridges/demo/:
    fresh                    out of the box: stiff, hesitant, no habits, no family chirps
    desk_student_year1       a year at a student's desk: worn moves, 4 habits (10 am wave, 3:30 break, 11:30 pm sleep)
    desk_student_passed_on   the same droid handed to a new keeper today. Wave at 10 and the old habit wakes up,
                             speaking with the first keeper's chirp
    loud_family_year12       12 years in a loud house: the most worn droid (no clock routine, so no habits)

Then, for example:
    python scripts/run.py --body unity --voice --mic 2 --cartridge cartridges/demo/desk_student_year1 --clock 9:58

Only folders this script made (they hold a .demo file) are ever deleted.
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.sim import time_skip  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "cartridges" / "demo"
MARK = ".demo"


def _clear(folder: Path) -> None:
    if not folder.exists():
        return
    if not (folder / MARK).exists():
        raise SystemExit(f"{folder} exists but this script didn't make it. Not touching it. Move it and run again")
    shutil.rmtree(folder)


def _mark(folder: Path, what: str) -> None:
    (folder / MARK).write_text(what + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = ("fresh", "desk_student_year1", "desk_student_passed_on", "loud_family_year12")
    for name in names:
        _clear(OUT / name)

    Cartridge.create(OUT / "fresh", label="fresh")
    _mark(OUT / "fresh", "out of the box")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        time_skip("desk_student", tmp, years=1, quiet=True, snapshots={"year1": 365})
        shutil.copytree(tmp / "desk_student_year1", OUT / "desk_student_year1")
        time_skip("loud_family", tmp, years=12, quiet=True, snapshots={"year12": 12 * 365})
        shutil.copytree(tmp / "loud_family_year12", OUT / "loud_family_year12")
    _mark(OUT / "desk_student_year1", "time skip: desk_student, 1 year")
    _mark(OUT / "loud_family_year12", "time skip: loud_family, 12 years")

    shutil.copytree(OUT / "desk_student_year1", OUT / "desk_student_passed_on")
    passed = Cartridge.open(OUT / "desk_student_passed_on")
    new = passed.handoff("the next keeper")
    _mark(OUT / "desk_student_passed_on", f"desk_student_year1, handed to a new keeper ({new.id}) today")

    print(f"Demo cartridges in {OUT}:")
    for name in names:
        cart = Cartridge.open(OUT / name)
        moments = sum(len(cart.read_page(l.id, "moments").get("moments", {})) for l in cart.layers)
        print(f"  {name:24s} {len(cart.layers)} keeper(s), {moments} routine(s)")


if __name__ == "__main__":
    main()
