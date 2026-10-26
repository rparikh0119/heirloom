"""Understanding by meaning (voice v1, D73). Whisper hears every word; this finds which command
a sentence MEANS, so "you're such a good little guy" is praise without anyone listing it.

How: a small sentence model (all-MiniLM-L6-v2 through fastembed, about 90 MB, runs on the CPU,
nothing leaves the computer) turns every example phrase in intents.py into a vector once. A new
sentence is turned into a vector too, and the closest command wins, but only if it's clearly
closer than the runner-up. Otherwise it's "not sure" and the droid tilts its head ("huh?").

It never generates words and never talks. It only picks from the commands it already has.

Thresholds are design values, tuned by ear on Riya's machine with scripts/meaning_check.py.
"""
from __future__ import annotations

import numpy as np

from .intents import EXTRA, INTENTS, NEGATIONS, NEGATIVE_EVENTS, normalize

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ACCEPT = 0.50       # how close (cosine, 0..1) a sentence must be to a command's examples.
                    # Oct 25 check on Riya's PC: "give me a minute" scored 0.53, things it should NOT
                    # understand topped out at 0.40, so 0.50 sits between them
MARGIN = 0.05       # and how much closer than the second-best command
NOT_BY_MEANING = {"record"}   # needs the listener to arm the mic, so only the exact words start it


class Meaning:
    def __init__(self, embed=None) -> None:
        """embed(list of str) -> array of vectors. Default: fastembed's MiniLM (downloads once)."""
        self._embed = embed or _fastembed()
        self.examples: list[tuple[str, str]] = []          # (event, phrase)
        for table in (INTENTS, EXTRA):
            for event, phrases in table.items():
                if event in NOT_BY_MEANING:
                    continue
                self.examples += [(event, p) for p in phrases if len(p.split()) >= 1]
        self._vectors = self._unit(self._embed([p for _, p in self.examples]))
        self._extra: list[tuple[str, str]] = []
        self._extra_vectors = np.zeros((0, self._vectors.shape[1]))

    @staticmethod
    def _unit(v) -> np.ndarray:
        v = np.asarray(v, dtype=np.float32)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)

    def teach(self, phrase: str, event: str) -> None:
        """Add a learned phrase as an example too, so close variations of it land as well."""
        self._extra.append((event, phrase))
        self._extra_vectors = np.vstack([self._extra_vectors, self._unit(self._embed([phrase]))])

    def scores(self, text: str) -> list[tuple[str, float]]:
        """Every command and how close the sentence is to its nearest example, best first."""
        v = self._unit(self._embed([normalize(text)]))[0]
        best: dict[str, float] = {}
        for (event, _), s in zip(self.examples + self._extra,
                                 np.concatenate([self._vectors @ v, self._extra_vectors @ v])):
            best[event] = max(best.get(event, -1.0), float(s))
        return sorted(best.items(), key=lambda kv: -kv[1])

    def understand(self, text: str) -> tuple[str | None, float]:
        """(command, how sure), or (None, best score) when it isn't clear enough."""
        ranked = self.scores(text)
        if not ranked:
            return None, 0.0
        (event, s1), s2 = ranked[0], (ranked[1][1] if len(ranked) > 1 else -1.0)
        if s1 >= ACCEPT and s1 - s2 >= MARGIN:
            if event not in NEGATIVE_EVENTS and NEGATIONS & set(normalize(text).split()):
                return None, s1          # these models miss "not": "I don't love you" scores as love. Ask instead
            return event, s1
        return None, s1


def _fastembed():
    from fastembed import TextEmbedding           # pip install fastembed (only needed with --voice)
    model = TextEmbedding(MODEL)

    def embed(texts: list[str]) -> np.ndarray:
        return np.array(list(model.embed(texts)))
    return embed
