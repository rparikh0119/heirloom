"""Checks the dials wear: how it treats you changes its temperament, slowly and within a limit.
Run:  python tests/test_wear_dials.py

Uses throwaway cartridges in a temp folder. Your real ones are never touched.
"""
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge, FADE_DAYS  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.wear.dials import load_rules  # noqa: E402

DAY = date(2026, 10, 21)
CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def brain_with(cart):
    return HeirloomBrain(play_sound=lambda name: None, cartridge=cart)


def wait(brain, secs):
    for _ in range(int(secs * 30)):
        brain.step(1 / 30, None)


# ---------------------------------------------------------------------------------------------

@check("no cartridge: the out-of-the-box droid, nothing learned")
def _(tmp):
    b = HeirloomBrain(play_sound=lambda name: None)
    assert b.wear == [] and b.character.sass == 0.5


@check("flipped off 10 times: sass creeps up (0.50 -> 0.51)")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    for _ in range(10):
        b.handle("offended")
        wait(b, 10)                     # let the sulk finish
    assert abs(b.character.sass - 0.51) < 1e-6, b.character.sass
    assert cart.read_page("L1", "dials")["sass"] == 0.01


@check("grumpier means longer sulks")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    cart.write_page("L1", "dials", {"sass": 0.2})
    b = brain_with(cart)
    assert b.character.sulk_seconds > 3.0 + 6.0 * 0.5


@check("making up with a heart during a sulk softens it")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    b.handle("offended")                 # +1
    b.handle("heart")                    # while sulking: -1
    assert cart.read_page("L1", "dials")["sass"] == 0.0


@check("a heart outside a sulk doesn't touch sass")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    b.handle("heart")
    assert "sass" not in cart.read_page("L1", "dials")


@check("praise right after curious: curiosity up. Praise out of nowhere: no change")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    b.handle("good")
    assert "curiosity" not in cart.read_page("L1", "dials")
    b.handle("curious")
    wait(b, 2)
    b.handle("good")
    assert cart.read_page("L1", "dials")["curiosity"] == 0.001


@check("praise too long after curious doesn't count")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    b.handle("curious")
    wait(b, 7)
    b.handle("good")
    assert "curiosity" not in cart.read_page("L1", "dials")


@check("the cap (D41): 1000 offences still stop at +0.25")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    b = brain_with(cart)
    for _ in range(1000):
        b.handle(Event("offended"))
    assert cart.read_page("L1", "dials")["sass"] == 0.25
    assert b.character.sass == 0.75


@check("layers blend: a kept grumpy past still shows, blended counts half, faded disappears")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    cart.write_page("L1", "dials", {"sass": 0.2})
    cart.handoff("second home", on=DAY)
    dials = brain_with(cart).wear[0]
    assert abs(dials.effective(DAY)["sass"] - 0.7) < 1e-9
    cart.set_weight("L1", "blend", on=DAY)
    assert abs(dials.effective(DAY)["sass"] - 0.6) < 1e-9
    cart.set_weight("L1", "fade", on=DAY)
    assert abs(dials.effective(DAY + timedelta(days=FADE_DAYS))["sass"] - 0.5) < 1e-9


@check("two grumpy owners can't stack past the cap")
def _(tmp):
    cart = Cartridge.create(tmp, on=DAY)
    cart.write_page("L1", "dials", {"sass": 0.25})
    cart.handoff("second home", on=DAY)
    cart.write_page("L2", "dials", {"sass": 0.25})
    assert brain_with(cart).character.sass == 0.75


@check("the rules file loads, and a typo stops with a clear message")
def _(tmp):
    step, rules = load_rules()
    assert step > 0 and rules
    bad = tmp / "dials.json"
    bad.write_text(json.dumps({"rules": [{"when": "good", "dial": "sasss", "nudge": 1}]}))
    try:
        load_rules(bad)
        raise AssertionError("accepted a typo")
    except ValueError as e:
        assert "sasss" in str(e)


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
