"""Checks the journal and the projector: asked for a memory, it shows a photo, then stops.
Run:  python tests/test_journal.py
"""
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.journal import SAMPLES, Journal  # noqa: E402
from heirloom.perception.intents import match  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def brain(cart=None):
    shown = []
    b = HeirloomBrain(play_sound=lambda name: None, cartridge=cart, show_photo=shown.append)
    return b, shown


def with_photos(tmp, names):
    cart = Cartridge.create(tmp / "c", on=date.today())
    (cart.folder / "journal").mkdir()
    for n in names:
        shutil.copy(next(SAMPLES.glob("*.jpg")), cart.folder / "journal" / n)
    return cart


@check("asked for a memory: it projects a photo and looks down at the desk")
def _(tmp):
    b, shown = brain()
    b.handle("show_memory")
    assert b.mode == "showing" and len(shown) == 1 and shown[0].exists(), shown
    pitch = [b.step(1 / 30, None)[0].head_pitch for _ in range(60)][-1]
    assert pitch < -12, pitch


@check("after about 9 seconds it stops projecting by itself")
def _(tmp):
    b, shown = brain()
    b.handle("show_memory")
    for _ in range(int(10 * 30)):
        b.step(1 / 30, None)
    assert b.mode != "showing" and shown[-1] is None, shown


@check("the cartridge's own photos come first, samples only when it has none")
def _(tmp):
    b, shown = brain(with_photos(tmp, ["grandma.jpg"]))
    b.handle("show_memory")
    assert shown[0].name == "grandma.jpg", shown


@check("'not now' during a memory stops it and retires that photo for good (D45)")
def _(tmp):
    cart = with_photos(tmp, ["a.jpg", "b.jpg"])
    b, shown = brain(cart)
    b.handle("show_memory")
    first = shown[0].name
    b.handle("not_now")
    assert b.mode != "back_off" and b.mode != "showing" and shown[-1] is None   # quietly stops, doesn't sulk
    retired = json.loads((cart.folder / "journal" / "retired.json").read_text())["retired"]
    assert retired == [first], retired
    for _ in range(6):
        b.handle("show_memory")
        b.handle("wake")
        assert b.showing is None or b.showing.name != first
    assert all(p is None or p.name != first for p in shown[2:])


@check("when every photo is retired it shows nothing (never falls back to samples)")
def _(tmp):
    cart = with_photos(tmp, ["a.jpg"])
    (cart.folder / "journal" / "retired.json").write_text(json.dumps({"retired": ["a.jpg"]}))
    b, shown = brain(cart)
    b.handle("show_memory")
    assert shown == [] and b.mode != "showing", (shown, b.mode)


@check("it doesn't show the same photo twice in a row")
def _(tmp):
    j = Journal(None)
    picks = [j.pick().name for _ in range(9)]
    assert all(a != b for a, b in zip(picks, picks[1:])), picks


@check("asleep or sulking, it won't show memories")
def _(tmp):
    b, shown = brain()
    b.handle("sleep")
    b.handle("show_memory")
    assert shown == []


@check("everyday ways of asking all land")
def _(tmp):
    got = [match(t, loose=True)[1] for t in ["Show me a memory.", "What do you remember?", "Remember when?",
                                              "Show me a picture!", "Do you remember?"]]
    assert got == ["show_memory"] * 5, got


@check("bodies without a projector just skip it")
def _(tmp):
    from heirloom.body.null_body import NullBody
    NullBody().show_photo(next(SAMPLES.glob("*.jpg")))
    NullBody().show_photo(None)


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
