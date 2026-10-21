"""Checks the cartridge core (the binder). Run:  python tests/test_cartridge.py

Every check makes a throwaway cartridge in a temp folder, so your real ones are never touched.
"""
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.cartridge import Cartridge, CartridgeError, FADE_DAYS  # noqa: E402

DAY = date(2026, 10, 21)
CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


# ---------------------------------------------------------------------------------------------

@check("a new cartridge has one active layer, nothing learned")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    assert [l.id for l in c.layers] == ["L1"]
    assert c.active.id == "L1" and c.active.source == {"type": "lived"}
    assert c.read_page("L1", "patina") == {}          # missing page = nothing learned yet


@check("save, then open again: everything comes back")
def _(tmp):
    c = Cartridge.create(tmp, label="Riya's desk", on=DAY)
    c.write_page("L1", "patina", {"wave": {"uses": 12}})
    again = Cartridge.open(tmp)
    assert again.droid == c.droid
    assert again.active.label == "Riya's desk"
    assert again.read_page("L1", "patina") == {"wave": {"uses": 12}}


@check("handoff: old layer closes and is kept, new owner gets an active layer")
def _(tmp):
    c = Cartridge.create(tmp, label="first home", on=DAY)
    new = c.handoff("second home", on=DAY + timedelta(days=365))
    c = Cartridge.open(tmp)
    old = c.layer("L1")
    assert new.id == "L2" and c.active.id == "L2"
    assert old.weight == "keep" and old.until == "2027-10-21"
    assert c.history["handoffs"][0]["choices"] == {"L1": "keep"}


@check("handoff with a choice: the new owner fades the old layer")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.handoff("second home", choices={"L1": "fade"}, on=DAY)
    assert Cartridge.open(tmp).layer("L1").weight == "fade"


@check("weights: active 1, keep 1, blend 0.5")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.handoff("two", on=DAY)
    c.handoff("three", choices={"L2": "blend"}, on=DAY)
    assert c.weights(DAY) == {"L1": 1.0, "L2": 0.5, "L3": 1.0}


@check(f"fade shrinks from 0.5 to 0 over {FADE_DAYS} days")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.handoff("two", choices={"L1": "fade"}, on=DAY)
    assert c.weights(DAY)["L1"] == 0.5
    assert abs(c.weights(DAY + timedelta(days=FADE_DAYS // 2))["L1"] - 0.25) < 0.01
    assert c.weights(DAY + timedelta(days=FADE_DAYS + 30))["L1"] == 0.0


@check("resting a layer: memories on request, wear still counts")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.handoff("grandchild", on=DAY)
    c.set_memories("L1", "on_request")
    c.save()
    c = Cartridge.open(tmp)
    assert c.layer("L1").memories == "on_request" and c.weights(DAY)["L1"] == 1.0


@check("a simulated layer says so (D46)")
def _(tmp):
    src = {"type": "simulated", "profile": "loud_family", "seed": 42}
    Cartridge.create(tmp, source=src, on=DAY)
    assert Cartridge.open(tmp).active.source == src


@check("seating in a body is logged (transfer proof)")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.seat("unity:reachy_a")
    c.seat("unity:reachy_b")
    bodies = [s["body"] for s in Cartridge.open(tmp).history["seated_in"]]
    assert bodies == ["unity:reachy_a", "unity:reachy_b"]


@check("unknown files and fields survive a save (old and new brains share cartridges)")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    (tmp / "layers" / "L1" / "smell.json").write_text('{"from": "a 2040 brain"}')
    raw = json.loads((tmp / "cartridge.json").read_text())
    raw["future_thing"] = 7
    raw["layers"][0]["colour"] = "oxblood"
    (tmp / "cartridge.json").write_text(json.dumps(raw))
    c = Cartridge.open(tmp)
    c.handoff("two", on=DAY)
    raw = json.loads((tmp / "cartridge.json").read_text())
    assert raw["future_thing"] == 7 and raw["layers"][0]["colour"] == "oxblood"
    assert (tmp / "layers" / "L1" / "smell.json").exists()


@check("a cartridge from a newer brain opens, but won't save over itself")
def _(tmp):
    Cartridge.create(tmp, on=DAY)
    raw = json.loads((tmp / "cartridge.json").read_text())
    raw["format_version"] = 99
    (tmp / "cartridge.json").write_text(json.dumps(raw))
    c = Cartridge.open(tmp)
    assert c.health()[0] is False
    try:
        c.save()
        raise AssertionError("saved a newer cartridge")
    except CartridgeError:
        pass


@check("mistakes stop with a clear message")
def _(tmp):
    Cartridge.create(tmp, on=DAY)
    raw = json.loads((tmp / "cartridge.json").read_text())
    raw["layers"][0]["weight"] = "keepp"
    (tmp / "cartridge.json").write_text(json.dumps(raw))
    try:
        Cartridge.open(tmp)
        raise AssertionError("opened a broken cartridge")
    except CartridgeError as e:
        assert "keepp" in str(e)


@check("only one layer can be active")
def _(tmp):
    c = Cartridge.create(tmp, on=DAY)
    c.handoff("two", on=DAY)
    try:
        c.set_weight("L2", "keep")
        raise AssertionError("closed the current owner's layer without a handoff")
    except CartridgeError:
        pass


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
