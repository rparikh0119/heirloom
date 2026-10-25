"""Checks photo taking: 'take a picture', a countdown, the shutter, and the photo kept in the journal.
Run:  python tests/test_photos.py
"""
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.journal import SAMPLES, Journal  # noqa: E402
from heirloom.perception.intents import match  # noqa: E402

CHECKS = []
JPEG = next(SAMPLES.glob("*.jpg")).read_bytes()


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def brain(cart=None):
    sounds, shots = [], []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=cart, take_photo=lambda: shots.append(b.t))
    return b, sounds, shots


def run(b, seconds):
    irises = []
    for _ in range(int(seconds * 30)):
        irises.append(b.step(1 / 30, (0, 0, 0.6))[0].iris)
    return irises


@check("'take a picture': three beeps, then the shutter, then the camera is asked once")
def _(tmp):
    b, sounds, shots = brain()
    b.handle("take_photo")
    assert b.mode == "shooting"
    run(b, 4)
    assert [s for s in sounds if s != "notice"] == ["tick", "tick", "tick", "shutter"], sounds
    assert len(shots) == 1 and 2.8 < shots[0] < 3.1, shots
    assert b.mode != "shooting"


@check("the iris snaps shut at the shutter (you can see it take the picture)")
def _(tmp):
    b, _, _ = brain()
    b.handle("take_photo")
    irises = run(b, 4)
    assert min(irises[80:100]) < 0.1 < max(irises[:60]), (min(irises[80:100]), max(irises[:60]))


@check("the photo comes back and is kept in the cartridge journal, with a saved chirp")
def _(tmp):
    cart = Cartridge.create(tmp / "c", on=date.today())
    b, sounds, _ = brain(cart)
    b.handle("take_photo")
    run(b, 3.0)
    b.handle(Event("photo_taken", source="camera", data={"jpeg": JPEG}))   # arrives while still in the countdown mode
    run(b, 1)
    saved = sorted((cart.folder / "journal").glob("*.jpg"))
    assert len(saved) == 1 and saved[0].read_bytes() == JPEG, saved
    assert "saved" in sounds, sounds


@check("then 'show me a memory' projects the photo it just took")
def _(tmp):
    cart = Cartridge.create(tmp / "c", on=date.today())
    shown = []
    b = HeirloomBrain(play_sound=lambda n: None, cartridge=cart, show_photo=shown.append)
    b.handle(Event("photo_taken", data={"jpeg": JPEG}))
    b.handle("show_memory")
    assert shown and shown[0].parent == cart.folder / "journal", shown


@check("nothing else interrupts the countdown, and asleep it won't take one")
def _(tmp):
    b, sounds, shots = brain()
    b.handle("take_photo")
    b.handle("good")
    assert b.mode == "shooting"
    s, _, sh = brain()
    s.handle("sleep")
    s.handle("take_photo")
    run(s, 4)
    assert sh == []


@check("without a cartridge the photo isn't kept anywhere (and it says so)")
def _(tmp):
    b, sounds, _ = brain()
    b.handle(Event("photo_taken", data={"jpeg": JPEG}))
    assert "saved" not in sounds and Journal(None).save_photo(JPEG) is None


@check("the words: 'take a picture', 'say cheese' take one, 'show me a photo' still shows one")
def _(tmp):
    got = [match(t, loose=True)[1] for t in ["Take a picture!", "Say cheese.", "Snap a photo.", "Show me a photo."]]
    assert got == ["take_photo", "take_photo", "take_photo", "show_memory"], got


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
