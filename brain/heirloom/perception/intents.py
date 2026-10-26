"""What Heirloom understands when you talk to it (Talk and Gesture v0).

Each brain event is triggered by several everyday phrases, so you never have to memorise
magic words. Edit this table freely. Every word has to exist in the speech model's vocabulary,
and the voice listener warns you on startup if one doesn't.

v0 = this fixed table, heard by Vosk (only these phrases can be heard).
v1 = Whisper hears every word, and EXTRA adds everyday ways of saying the same thing (D63).
v2 = learn the owner's own words (a Wear System feature, see docs/wear-system.md).
"""
from __future__ import annotations

# Saying any of these opens a short listening window. "air loom" is a backup in case the
# model hears "heirloom" as two words.
WAKE_WORDS = ["heirloom", "air loom"]
# Whisper spells the name all sorts of ways. These count too (only used by the Whisper listener).
WAKE_VARIANTS = ["heir loom", "hair loom", "airloom", "hairloom", "heirlooms", "air loom", "heirloom"]

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
    "shh":     ["be quiet", "quiet", "hush"],
    "show_memory": ["remember", "show me", "memory"],
    "record":  ["record this", "record", "remember this"],
    "take_photo": ["take a picture", "take a photo", "picture", "cheese"],
    "go_home": ["go back", "go home"],
    "play_memory": ["play it back", "play it", "play back"],
}


# More ways of saying each thing. Whisper can hear any word, so these work there (not in Vosk).
EXTRA: dict[str, list[str]] = {
    "wave":    ["hiya", "howdy", "hi there", "hey there", "hello there", "good to see you", "what's up",
                "whats up", "sup", "yo", "hey buddy", "hi buddy", "how are you", "i'm back", "im back"],
    "good":    ["good boy", "good girl", "well done", "great job", "nice job", "awesome", "perfect",
                "thanks", "you're the best", "youre the best", "that's it", "atta boy", "attaboy",
                "amazing", "you're amazing", "youre amazing", "good robot", "smart", "so smart", "clever",
                "you're so cute", "youre so cute", "so cute", "cutie", "proud of you", "love that"],
    "offended": ["fuck off", "fuck you", "screw you", "get lost", "buzz off", "piss off", "i hate you", "hate you", "you suck", "shut up",
                 "you're annoying", "youre annoying", "so annoying", "stupid", "idiot", "dumb robot",
                 "useless", "you're useless", "youre useless", "go to hell"],
    "scold":   ["bad boy", "bad girl", "don't do that", "dont do that", "hey stop", "cut it out", "knock it off",
                "stop", "stop that", "no no no", "quit it"],
    "not_now": ["not right now", "i'm busy", "im busy", "leave me alone", "back off", "one sec", "hold on"],
    "sleep":   ["night night", "go to bed", "bedtime", "time to sleep", "rest now"],
    "wake":    ["rise and shine", "wakey wakey", "time to get up", "get up"],
    "curious": ["come over here", "come look", "look over here", "check this out", "look at this",
                "look what i've got", "look what i have", "come see"],
    "sorry":   ["my bad", "i apologize", "forgive me", "so sorry"],
    "heart":   ["love ya", "i love ya", "love you so much", "you're my favorite", "youre my favorite",
                "you mean the world to me", "you mean everything to me", "i adore you"],
    "shh":     ["shh", "shush", "shhh", "quiet please", "keep it down", "be quiet please"],
    "show_memory": ["show me a memory", "what do you remember", "do you remember", "show me something",
                    "show me a picture", "show me a photo", "memories", "a memory", "remember when"],
    "go_home": ["back to your spot", "go back to your spot", "back you go", "go to your spot", "return"],
    "take_photo": ["take a pic", "snap a photo", "snap a picture", "say cheese", "take our picture",
                   "take my picture", "take a picture of this", "photo time", "picture time", "take a photo of this"],
    "record":  ["record a message", "record something", "record me", "take a note", "save this",
                "keep this", "remember this for me", "start recording"],
    "play_memory": ["play the recording", "play a recording", "play my message", "play the message",
                    "play that back", "let me hear it", "play the one", "play my recording", "play it again"],
}


SOLO_MAX = 3   # one-word keywords only count in sentences this short ("no!", "good job", "nice one buddy")
NEGATIONS = {"not", "don't", "dont", "never", "isn't", "isnt", "aren't", "doesn't", "didn't", "won't", "can't", "cannot"}
NEGATIVE_EVENTS = {"scold", "not_now", "shh", "offended"}     # their phrases already contain "no" / "not"


def normalize(text: str) -> str:
    """Lowercase, keep letters, digits and apostrophes, everything else becomes a space.
    "Hi!  Heirloom." -> "hi heirloom" """
    import re
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", text.lower()).split())


def all_phrases() -> list[str]:
    return WAKE_WORDS + [p for phrases in INTENTS.values() for p in phrases]


def can_act_early(text: str) -> bool:
    """While someone is still talking: is what we have so far safe to act on right now?
    Yes if no other command starts with the same letters. "hi" is safe. "good" is not ("good
    night" means sleep), and neither is "no", because a live guess of "no" can turn into "not now".
    Those wait for the end of the sentence."""
    woke, event = match(text)
    if event is None:
        return False
    words = [w for w in text.split() if w not in " ".join(WAKE_WORDS).split()]
    tail = " ".join(words)
    for other, phrases in INTENTS.items():
        if other == event:
            continue
        for p in phrases:
            if p != tail and p.startswith(tail):
                return False
    return True


def match(text: str, loose: bool = False) -> tuple[bool, str | None]:
    """Read one heard utterance. Returns (wake word heard?, brain event or None).

    The longest matching phrase wins, so "good night" means sleep, not praise.
    loose=True (Whisper) also accepts EXTRA phrases and spellings of the name.
    """
    padded = f" {normalize(text)} "
    wakes = sorted(set(WAKE_WORDS + (WAKE_VARIANTS if loose else [])), key=len, reverse=True)
    woke = any(f" {w} " in padded for w in wakes)
    for w in wakes:
        padded = padded.replace(f" {w} ", " ")

    best, best_len, best_phrase = None, 0, ""
    tables = [INTENTS, EXTRA] if loose else [INTENTS]
    words = len(padded.split())
    for table in tables:
        for event, phrases in table.items():
            for p in phrases:
                if " " not in p and words > SOLO_MAX:   # a lone keyword inside a long sentence ("long time NO see")
                    continue                           # isn't trusted. Meaning reads the whole sentence instead
                if f" {p} " in padded and len(p) > best_len:
                    best, best_len, best_phrase = event, len(p), p
    if best and best not in NEGATIVE_EVENTS:
        before = padded[:padded.index(f" {best_phrase} ")].split()[-3:]
        if NEGATIONS & set(before):           # "I don't love you" is not a heart. Better a "huh?" than a wrong one
            return woke, None
    return woke, best
