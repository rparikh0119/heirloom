"""Checks the learning loop v0: the learner, the reward interpreter, the guards and passing down.
Run:  python tests/test_learning.py
"""
import json
import random
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.reactions import load_reactions  # noqa: E402
from heirloom.wear.responses import INHERIT_CAP  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def droid(tmp: Path, at="10:00", learn=True, name="c"):
    folder = tmp / name
    cart = Cartridge.open(folder) if (folder / "cartridge.json").exists() else Cartridge.create(folder)
    b = HeirloomBrain(play_sound=lambda n: None, cartridge=cart, learn=learn)
    h, m = (int(x) for x in at.split(":"))
    b.now = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
    return b


def wave(b) -> str:
    """Wave at it, return the move it answered with."""
    b.handle(Event("wave", source="hands"))
    b.pass_time(1.0)
    return b.expr.last if hasattr(b.expr, "last") else b.decisions.lines[-1].get("chosen")


def owner(b, likes: str, n: int, rng: random.Random, cold=True) -> list[str]:
    """A fake owner who gives a thumbs up when it answers a wave with `likes`, and says "no" otherwise."""
    picks = []
    for _ in range(n):
        b.handle(Event("wave", source="hands"))
        chosen = [l for l in b.decisions.lines if "chosen" in l][-1]["chosen"]
        picks.append(chosen)
        b.pass_time(1.5)
        if chosen == likes:
            if rng.random() < 0.9:
                b.handle(Event("good", source="hands"))
        elif cold and rng.random() < 0.7:
            b.handle(Event("scold", source="voice"))
        b.pass_time(200.0)               # time passes before the next wave (quiet mask over)
    return picks


# ---------------------------------------------------------------------------------------------

@check("off by default: no --learn, it always answers a wave with hello and logs nothing")
def _(tmp):
    b = droid(tmp, learn=False)
    for _ in range(20):
        b.handle(Event("wave", source="hands"))
        assert b.expr.name == "hello"
        b.pass_time(10)
    assert b.decisions.lines == [] and b.cartridge.read_page("L1", "responses") == {}


@check("a fresh droid mostly does what it was designed to do (hello), and sometimes tries another move")
def _(tmp):
    b = droid(tmp)
    picks = []
    for _ in range(100):
        b.handle(Event("wave", source="hands"))
        picks.append(b.decisions.lines[-1]["chosen"])
        b.pass_time(10)
    share = picks.count("hello") / len(picks)
    assert 0.45 <= share <= 0.85, share          # about 60% with HEAD 1.5 (see responses.py)
    assert len(set(picks)) > 1, picks


@check("silence teaches nothing: no reaction, no change to the tallies")
def _(tmp):
    b = droid(tmp)
    for _ in range(10):
        b.handle(Event("wave", source="hands"))
        b.pass_time(10)
    assert b.cartridge.read_page("L1", "responses") == {}
    assert not any("reward" in l for l in b.decisions.lines)


@check("an owner who loves the happy wiggle in the morning gets it most of the time within 30 waves")
def _(tmp):
    b = droid(tmp)
    picks = owner(b, "happy", 30, random.Random(1))
    assert picks[-10:].count("happy") >= 8, picks


@check("an owner who wants quiet gets the quiet listen")
def _(tmp):
    b = droid(tmp)
    picks = owner(b, "listen", 40, random.Random(2))
    assert picks[-10:].count("listen") >= 7, picks


@check("times of day share a lean, but an evening that wants something else gets it")
def _(tmp):
    b = droid(tmp)
    owner(b, "happy", 25, random.Random(3))           # mornings: loves the wiggle
    b.now = b.now.replace(hour=19)
    b.handle(Event("wave", source="hands"))
    first = [l for l in b.decisions.lines if "chosen" in l][-1]
    assert first["context"]["tod"] == "evening"
    b.pass_time(300)
    picks = owner(b, "listen", 40, random.Random(4))  # evenings: wants quiet
    assert picks[-10:].count("listen") >= 7, picks


@check("only a reaction in the next 6 s counts. Later, or after another command, it's no reward")
def _(tmp):
    b = droid(tmp)
    b.handle(Event("wave", source="hands"))
    b.pass_time(7.0)
    b.handle(Event("good", source="hands"))          # too late
    b.handle(Event("wave", source="hands"))
    b.pass_time(1.0)
    b.handle(Event("sleep", source="voice"))          # another command closes the window
    b.handle(Event("good", source="hands"))
    assert not any("reward" in l and l["decision_id"] in ("d_0001", "d_0003") for l in b.decisions.lines), b.decisions.lines


@check("quiet mask: right after a \"no\", it can only answer with a quiet move")
def _(tmp):
    b = droid(tmp)
    b.handle(Event("wave", source="hands"))
    b.pass_time(1.0)
    b.handle(Event("scold", source="voice"))
    b.pass_time(5.0)
    b.handle(Event("wave", source="hands"))
    d = [l for l in b.decisions.lines if "chosen" in l][-1]
    assert d["chosen"] == "listen" and set(d["masked"]) == {"hello", "happy", "curious"}, d
    b.pass_time(130.0)
    b.handle(Event("wave", source="hands"))
    assert [l for l in b.decisions.lines if "chosen" in l][-1]["masked"] == []


@check("goodbyes and commands never learn: only wave, good and heart have choices")
def _(tmp):
    learnable = sorted(r.file for r in load_reactions() if r.choices)
    assert learnable == ["good.json", "heart.json", "wave.json"], learnable


@check("the decision record: context, candidates, odds that add up, choice, seed, and the reward line")
def _(tmp):
    b = droid(tmp)
    b.handle(Event("wave", source="hands"))
    b.pass_time(2.0)
    b.handle(Event("heart", source="hands"))
    lines = [json.loads(x) for x in (tmp / "c" / "logs" / "decisions.jsonl").read_text().splitlines()]
    d, r = lines[0], lines[1]
    assert d["context"] == {"cue": "wave", "tod": "morning", "mode": "awake"}, d
    assert d["chosen"] in d["candidates"] and abs(sum(d["probs"]) - 1) < 0.01 and d["seed"], d
    assert r == {"decision_id": d["decision_id"], "reward": 1, "cue": "heart", "delay_s": 2.0}, r


@check("the overlay line says what it did and how often it worked")
def _(tmp):
    b = droid(tmp)
    owner(b, "happy", 12, random.Random(4))
    b.handle(Event("wave", source="hands"))
    ws = b.wear_state()
    assert ws["learn_on"] and ws["learn_line"].startswith("wave · morning -> "), ws["learn_line"]
    json.dumps(ws)


@check("passed down: the old keeper's lean is capped, and the new keeper overrides it")
def _(tmp):
    a = droid(tmp, name="x")
    owner(a, "happy", 40, random.Random(5))
    a.cartridge.handoff("the next keeper")
    b = droid(tmp, name="x")
    resp = next(w for w in b.wear if w.name == "responses")
    t = resp.tallies("wave|morning", ["hello", "happy", "curious", "listen"], "hello")
    assert sum(t["happy"]["inherited"]) <= INHERIT_CAP + 1e-6 and t["happy"]["from"] == ["L1"], t["happy"]
    assert "from L1" in resp.explain("wave|morning", "happy", "hello", ["hello", "happy", "curious", "listen"])
    picks = owner(b, "listen", 40, random.Random(6))
    assert picks[-10:].count("listen") >= 7, picks


@check("a broken responses page is refused with a clear message")
def _(tmp):
    cart = Cartridge.create(tmp / "bad")
    cart.write_page("L1", "responses", {"schema": "heirloom.wear.responses/1", "buckets": {"wave|morning": {"happy": [1]}}})
    try:
        HeirloomBrain(play_sound=lambda n: None, cartridge=Cartridge.open(tmp / "bad"), learn=True)
    except Exception as e:  # noqa: BLE001
        assert "[worked, didn't]" in str(e), e
        return
    raise AssertionError("accepted a broken page")


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
