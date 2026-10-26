"""Checks understanding and word learning (D73), with a stand-in for the sentence model (no download).
Real accuracy is measured on Riya's machine with scripts/meaning_check.py.
Run:  python tests/test_understanding.py
"""
import hashlib
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.cartridge import Cartridge  # noqa: E402
from heirloom.events import Event  # noqa: E402
from heirloom.perception.intents import match  # noqa: E402
from heirloom.perception.meaning import Meaning  # noqa: E402

CHECKS = []


def check(label):
    def wrap(fn):
        CHECKS.append((label, fn))
        return fn
    return wrap


def fake_embed(texts):
    """Stand-in model: a sentence is the average of its words' fixed random vectors, so sentences that
    share words are close. Crude, but enough to test the plumbing."""
    out = []
    for t in texts:
        vs = [np.random.default_rng(int(hashlib.md5(w.encode()).hexdigest()[:8], 16)).normal(size=64)
              for w in t.lower().replace("'", "").split()] or [np.zeros(64)]
        out.append(np.mean(vs, axis=0))
    return np.array(out)


def brain(cart=None, meaning=True):
    sounds = []
    b = HeirloomBrain(play_sound=sounds.append, cartridge=cart, meaning=Meaning(fake_embed) if meaning else None)
    return b, sounds


def said(text):
    return Event("unknown", source="voice", data={"said": text})


def cart(tmp):
    return Cartridge.create(tmp / "c", on=date.today())


@check("words it doesn't know: it tilts its head and asks 'huh?'")
def _(tmp):
    b, sounds = brain(meaning=False)
    b.handle(said("pass me the remote"))
    assert sounds == ["huh"] and b.expr.name == "curious", (sounds, b.expr.name)


@check("it doesn't ask over and over (background chatter): one 'huh?' per 8 s")
def _(tmp):
    b, sounds = brain(meaning=False)
    b.handle(said("pass me the remote"))
    b.pass_time(2)
    b.handle(said("what time is it"))
    assert sounds.count("huh") == 1
    b.pass_time(9)
    b.handle(said("what time is it"))
    assert sounds.count("huh") == 2


@check("teach it: say something new, then wave within a few seconds, and it learns the words")
def _(tmp):
    c = cart(tmp)
    b, sounds = brain(c, meaning=False)
    b.handle(said("hey little dude"))
    b.pass_time(2)
    b.handle(Event("wave", source="hands"))
    assert sounds[-1] == "learned", sounds
    assert c.read_page("L1", "words")["hey little dude"]["event"] == "wave"
    sounds.clear()
    b.pass_time(10)
    b.handle(said("hey little dude"))                     # next time it just answers
    assert "huh" not in sounds and b.expr.name == "hello", (sounds, b.expr.name)


@check("too slow to show it (more than 6 s): nothing learned")
def _(tmp):
    c = cart(tmp)
    b, _ = brain(c, meaning=False)
    b.handle(said("hey little dude"))
    b.pass_time(8)
    b.handle(Event("wave", source="hands"))
    assert c.read_page("L1", "words") == {}


@check("long sentences are never learned, only short phrases")
def _(tmp):
    c = cart(tmp)
    b, _ = brain(c, meaning=False)
    b.handle(said("so anyway I was telling her about the thing at work today"))
    b.pass_time(1)
    b.handle(Event("good", source="hands"))
    assert c.read_page("L1", "words") == {}


@check("learned words pass down: the next owner's droid still answers to them")
def _(tmp):
    c = cart(tmp)
    b, _ = brain(c, meaning=False)
    b.handle(said("who's my little bean"))
    b.pass_time(1)
    b.handle(Event("heart", source="hands"))
    c.handoff("granddaughter", on=date.today())
    b2, sounds = brain(c, meaning=False)
    b2.handle(said("who's my little bean"))
    assert "huh" not in sounds and b2.expr.name == "love", (sounds, b2.expr.name)


@check("a faded past forgets its words")
def _(tmp):
    c = cart(tmp)
    b, _ = brain(c, meaning=False)
    b.handle(said("who's my little bean"))
    b.pass_time(1)
    b.handle(Event("heart", source="hands"))
    c.handoff("new home", on=date.today())
    c.set_weight("L1", "fade", on=date.today())
    b2 = HeirloomBrain(play_sound=lambda n: None, cartridge=c)
    b2.today = date.today() + timedelta(days=60)
    for w in b2.wear:
        w.apply(b2)
    assert "who's my little bean" not in b2.vocabulary


@check("by meaning: a sentence close to known phrases is understood without exact words")
def _(tmp):
    b, sounds = brain()
    found = b._understand("great work, so well done")           # shares words with "great job", "well done"
    assert found and found[0] == "good", found


@check("by meaning, unsure: it asks instead of guessing")
def _(tmp):
    b, sounds = brain()
    b.handle(said("quantum spreadsheet invoice"))
    assert sounds == ["huh"], sounds


@check("'I don't love you' is not a heart (it asks instead)")
def _(tmp):
    assert match("I don't love you.", loose=True)[1] is None
    assert match("I love you.", loose=True)[1] == "heart"
    assert match("Not now.", loose=True)[1] == "not_now"
    assert match("No, stop it.", loose=True)[1] == "scold"


@check("long sentences: understood by meaning if it can, but never a 'huh?' (probably not meant for it)")
def _(tmp):
    b, sounds = brain()
    b.handle(said("so anyway quantum spreadsheet invoice tax refund was due last tuesday morning"))
    assert "huh" not in sounds
    b.vocabulary["little bean"] = "heart"                 # a phrase it was taught, inside a long sentence
    b.handle(said("good morning to my favourite little bean in the whole wide world"))
    assert b.expr.name == "love" and "huh" not in sounds, (b.expr.name, sounds)


@check("asleep, it doesn't ask 'huh?' at voices")
def _(tmp):
    b, sounds = brain(meaning=False)
    b.handle("sleep")
    sounds.clear()
    b.handle(said("pass me the remote"))
    assert "huh" not in sounds


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
