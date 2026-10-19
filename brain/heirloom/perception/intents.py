"""What Heirloom understands when you talk to it (Talk and Gesture v0).

Each brain event is triggered by several everyday phrases, so you never have to memorise
magic words. Edit this table freely. Every word has to exist in the speech model's vocabulary,
and the voice listener warns you on startup if one doesn't.

v0 = this fixed table. v1 = hear every word and match loosely. v2 = learn the owner's own words
(a Wear System feature, see docs/wear-system.md).
"""
from __future__ import annotations

# Saying any of these opens a short listening window. "air loom" is a backup in case the
# model hears "heirloom" as two words.
WAKE_WORDS = ["heirloom", "air loom"]

# brain event -> phrases that trigger it
INTENTS: dict[str, list[str]] = {
    "wave":    ["hi", "hey", "hello"],
    "good":    ["good", "good job", "nice", "yes", "thank you"],
    "scold":   ["no", "nope", "no no", "bad", "stop it",
                "now"],   # a lone "now" is almost always a misheard "no" ("not now" still wins)
    "not_now": ["not now", "go away", "later", "give me space"],
    "sleep":   ["go to sleep", "good night", "sleep"],
    "wake":    ["wake up", "good morning"],
    "curious": ["come here", "look at me", "over here"],
    "sorry":   ["sorry", "i'm sorry"],
    "heart":   ["i love you", "love you"],
}


def all_phrases() -> list[str]:
    return WAKE_WORDS + [p for phrases in INTENTS.values() for p in phrases]


def match(text: str) -> tuple[bool, str | None]:
    """Read one heard utterance. Returns (wake word heard?, brain event or None).

    The longest matching phrase wins, so "good night" means sleep, not praise.
    """
    words = text.split()
    padded = f" {' '.join(words)} "
    woke = any(f" {w} " in padded for w in WAKE_WORDS)
    for w in WAKE_WORDS:
        padded = padded.replace(f" {w} ", " ")

    best, best_len = None, 0
    for event, phrases in INTENTS.items():
        for p in phrases:
            if f" {p} " in padded and len(p) > best_len:
                best, best_len = event, len(p)
    return woke, best
