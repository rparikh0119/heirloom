"""Words wear: Heirloom learns your words for things (D73).

Say something it doesn't know ("hey little dude") and it tilts its head. If within a few seconds
you show it what you meant (wave, a heart, "not now", any command), it learns that phrase means
that. Next time it just answers. The phrases live in the cartridge, so the next owner's droid still
answers to the last family's pet names. It keeps only the short phrase as text, never the audio,
and only when you teach it (D43).

Page per layer (layers/L1/words.json):
    {"hey little dude": {"event": "wave", "learned": "2026-10-25", "uses": 3}}

Blend: phrases from layers that still count (weight 0.5 or more) are known. If two owners taught
the same phrase different things, the newer owner's meaning wins.
"""
from __future__ import annotations

from datetime import date

from ..perception.intents import normalize
from .base import Wear

LEARN_WINDOW = 6.0       # seconds after "huh?" to show it what you meant
MAX_WORDS = 6            # only short phrases are learned, never whole sentences
LEARNABLE = {"wave", "good", "heart", "not_now", "shh", "sleep", "wake", "curious", "offended",
             "scold", "sorry", "show_memory", "take_photo", "go_home", "play_memory"}
COUNTS_FROM = 0.5        # a layer must weigh at least this for its words to be known


class WordsWear(Wear):
    name = "words"

    def __init__(self) -> None:
        self._pending: tuple[str, float] | None = None
        self.known: dict[str, str] = {}
        self.just_learned: tuple[str, str] | None = None

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain

    def record(self, event, mode: str, t: float) -> bool:
        self.just_learned = None
        if event.name == "unknown":
            phrase = normalize(event.data.get("said", ""))
            n = len(phrase.split())
            self._pending = (phrase, t) if 0 < n <= MAX_WORDS else None
            return False
        if self._pending and event.name in LEARNABLE and not event.data.get("understood"):
            phrase, when = self._pending
            self._pending = None
            if t - when <= LEARN_WINDOW:
                page = self.cart.read_page(self.cart.active.id, self.name)
                old = page.get(phrase, {})
                page[phrase] = {"event": event.name, "learned": self._today().isoformat(),
                                "uses": old.get("uses", 0) if old.get("event") == event.name else 0}
                self.cart.write_page(self.cart.active.id, self.name, page)
                self.just_learned = (phrase, event.name)
                return True
        return False

    def used(self, phrase: str) -> None:
        """A learned phrase was understood again. Counted in the layer that has it, if it's the owner's own."""
        page = self.cart.read_page(self.cart.active.id, self.name)
        if phrase in page:
            page[phrase]["uses"] = page[phrase].get("uses", 0) + 1
            self.cart.write_page(self.cart.active.id, self.name, page)

    def _today(self) -> date:
        b = getattr(self, "brain", None)
        return (b.today if b is not None and b.today else None) or date.today()

    def apply(self, brain) -> None:
        known: dict[str, str] = {}
        weights = self.cart.weights(brain.today)
        for layer in self.cart.layers:                      # oldest first, so a newer owner's meaning wins
            if weights.get(layer.id, 0.0) < COUNTS_FROM:
                continue
            for phrase, rec in self.cart.read_page(layer.id, self.name).items():
                known[phrase] = rec["event"]
        self.known = known
        brain.vocabulary = dict(known)

    def validate(self, data: dict, where: str) -> None:
        for phrase, rec in data.items():
            if not isinstance(rec, dict) or not isinstance(rec.get("event"), str):
                raise ValueError(f"{where}: {phrase!r} needs {{\"event\": a command name}}")
