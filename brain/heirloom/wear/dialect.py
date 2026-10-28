"""Dialect wear (v0): every moment gets its own chirp, and the chirps pass down (proposed D85 to D87).

The core chirps (hello, happy, sleepy...) are fixed and readable by anyone. On top of them each
household grows a few family chirps: when the droid answers a moment (the 10 am hello, the 3:30
break), it uses a chirp bred from its usual sound for that reaction. So the 10 am hello still
reads as a hello, in the family's own accent. Strangers hear "hello". The family hears "our hello".

    minted     the first time it answers that moment, bred from the reaction's usual chirp
    distinct   always differs from every other chirp in note count or direction (genome.MIN_DIST)
    kept       one page per layer, so the chirps travel in the cartridge
    passed on  a woken moment (moments wear, "from") speaks with the old keeper's chirp

    drifts     (learning loop on) each play is a slightly varied version. A warm reaction within
               6 s nudges the stored chirp a small step toward the version that just played (proposed D86, D88).
               Identity is locked: note count and each note's direction never change, so the hello stays
               a hello. Only the accent moves: pitch, note lengths, wobble. Capped from where it started
               (origin), and never allowed within MIN_DIST of another chirp (homonym filter).
               Passed down, drift writes only to the new keeper's copy. The old keeper's stays as it was.

Page per layer (layers/L1/dialect.json):
    {"L1.m01": {"parent": "hello", "notes": [...], "minted": "2026-10-25", "from": null,
                "origin": [...notes before any drift...], "drift": {"steps": 3, "pitch": 1.021, "length": 0.97}}}
"""
from __future__ import annotations

import random
from datetime import date

from ..sound import chirps as C
from ..sound import genome as G
from .base import Wear

PREFIX = "m:"        # moment chirps are played by name as "m:L1.m01"
TRY = "~"            # a varied play is registered as "m:L1.m01~"

# Drift (design numbers: the report found no sourced drift rate or annoyance threshold. Tune in playtest)
JITTER_PITCH = 0.03  # each play: whole chirp up to 3% higher or lower
JITTER_LEN = 0.08    # each note up to 8% longer or shorter
JITTER_WOBBLE = 0.2  # wobble depth up to 20% more or less
STEP = 0.10          # a warm reaction moves the chirp a tenth of the way toward what just played.
                     # Oct 27: 0.25 hit the 12% pitch cap after ~27 warm mornings (a month). Too fast for
                     # "wears in over years". At 0.10, a home that always warms to higher versions moves
                     # roughly 0.15% per warm reaction. No sourced rate exists (spine report): tune in playtest.
                     # If it's still too fast, the next knob is a per-day limit
CAP_PITCH = 0.12     # never more than 12% higher or lower than where it started
CAP_LEN = 0.20       # notes never more than 20% longer or shorter than where they started


class DialectWear(Wear):
    name = "dialect"

    def __init__(self) -> None:
        self.brain = None
        self.chirps: dict[str, dict] = {}       # every moment chirp in every layer, with "layer" added

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain

    def apply(self, brain) -> None:
        self.chirps = {}
        for layer in self.cart.layers:            # memories, whatever the layer's weight: a chirp is never lost
            for mid, rec in self.cart.read_page(layer.id, self.name).items():
                self.chirps[mid] = {**rec, "layer": layer.id}
                G.register(PREFIX + mid, rec["notes"])

    def validate(self, data: dict, where: str) -> None:
        for mid, rec in data.items():
            if not isinstance(rec, dict) or "parent" not in rec:
                raise ValueError(f"{where}: {mid!r} needs a \"parent\" (the core chirp it came from)")
            G.check(rec.get("notes"), f"{where}: {mid!r}")

    def health(self) -> tuple[bool, str]:
        return True, f"{len(self.chirps)} family chirps"

    # ---------- used by the brain ----------
    def voice(self, moment_id: str, parent: str) -> str:
        """The chirp to play for this moment. Mints it the first time. Returns a playable name."""
        if moment_id in self.chirps:
            return PREFIX + moment_id
        moment = (getattr(self.brain, "moments", {}) or {}).get(moment_id, {})
        old = moment.get("from")
        lid = self.cart.active.id
        if old and old in self.chirps:                        # passed down: speak like the last keeper did
            rec = {"parent": self.chirps[old]["parent"], "notes": [dict(n) for n in self.chirps[old]["notes"]],
                   "minted": self._today(), "from": old}
            print(f"[dialect] {moment_id} speaks with {old}'s chirp (from {self.chirps[old]['layer']})")
        else:
            if parent not in C.CHIRPS:
                return parent
            others = [G.capture(n) for n in C.CHIRPS if not n.startswith(PREFIX)]
            others += [c["notes"] for c in self.chirps.values()]   # (varied plays are named m:...~, so already skipped)
            notes = G.breed(G.capture(parent), others, seed=f"{self._droid()}:{moment_id}")
            rec = {"parent": parent, "notes": notes, "minted": self._today(), "from": None}
            print(f"[dialect] new family chirp for {moment_id}, bred from \"{parent}\"")
        page = self.cart.read_page(lid, self.name)
        page[moment_id] = rec
        self.cart.write_page(lid, self.name, page)
        self.chirps[moment_id] = {**rec, "layer": lid}
        G.register(PREFIX + moment_id, rec["notes"])
        return PREFIX + moment_id

    # ---------- drift ----------
    def variant(self, moment_id: str, seed: str) -> tuple[str, dict]:
        """A slightly varied play of this moment's chirp (fresh each time, like Cozmo).
        Returns a playable name and the variation, so a warm reaction can drift toward it."""
        rec = self.chirps[moment_id]
        rng = random.Random(seed)
        jitter = {"pitch": 1 + rng.uniform(-JITTER_PITCH, JITTER_PITCH),
                  "len": [1 + rng.uniform(-JITTER_LEN, JITTER_LEN) for _ in rec["notes"]],
                  "wobble": 1 + rng.uniform(-JITTER_WOBBLE, JITTER_WOBBLE)}
        G.register(PREFIX + moment_id + TRY, self._shift(rec["notes"], jitter, 1.0))
        return PREFIX + moment_id + TRY, jitter

    def nudge(self, moment_id: str, jitter: dict) -> str | None:
        """It landed: move this keeper's chirp a STEP toward the version that played.
        Returns a short description of the change, or None if it couldn't move (cap or too close to another chirp)."""
        lid = self.cart.active.id
        page = self.cart.read_page(lid, self.name)
        rec = page.get(moment_id)
        if rec is None:                          # an old keeper's chirp: frozen, drift only touches the active layer
            return None
        origin = rec.get("origin") or [dict(n) for n in rec["notes"]]
        moved = self._shift(rec["notes"], jitter, STEP)
        moved = self._clamp_to(moved, origin)
        if G.length(moved) > G.LONGEST:
            return None
        if [G.direction(n) for n in moved] != [G.direction(n) for n in origin] or len(moved) != len(origin):
            return None                          # identity is locked
        family = self._lineage(moment_id)        # its own ancestors aren't "another chirp"
        others = [G.capture(n) for n in C.CHIRPS if not n.startswith(PREFIX) and not n.endswith(TRY)]
        others += [c["notes"] for mid, c in self.chirps.items() if mid not in family]
        if others:
            now_d = min(G.distance(rec["notes"], o) for o in others)
            new_d = min(G.distance(moved, o) for o in others)
            if new_d < min(G.MIN_DIST, now_d):
                return None                      # homonym filter: never drift closer to another chirp
                                                 # (a chirp bred in a crowded vocabulary may start a bit under MIN_DIST)
        pitch = moved[0]["f0"] / origin[0]["f0"]
        length = G.length(moved) / G.length(origin)
        drift = rec.get("drift", {"steps": 0})
        rec.update({"notes": moved, "origin": origin,
                    "drift": {"steps": drift.get("steps", 0) + 1, "pitch": round(pitch, 4), "length": round(length, 4)}})
        page[moment_id] = rec
        self.cart.write_page(lid, self.name, page)
        self.chirps[moment_id] = {**rec, "layer": lid}
        G.register(PREFIX + moment_id, moved)
        return f"{(pitch - 1) * 100:+.1f}% pitch, {(length - 1) * 100:+.1f}% length since minted"

    def _lineage(self, moment_id: str) -> set[str]:
        """This chirp and every chirp it was passed down from."""
        seen, mid = set(), moment_id
        while mid and mid not in seen:
            seen.add(mid)
            mid = (self.chirps.get(mid) or {}).get("from")
        return seen

    @staticmethod
    def _shift(notes: list[dict], jitter: dict, amount: float) -> list[dict]:
        """Apply `amount` of a variation (1 = all of it, STEP = a nudge). Directions can't flip:
        both ends of a glide move by the same ratio."""
        out = []
        p = jitter["pitch"] ** amount
        w = jitter["wobble"] ** amount
        for n, ln in zip(notes, jitter["len"]):
            m = dict(n)
            m["f0"], m["f1"] = n["f0"] * p, n["f1"] * p
            m["dur"] = n["dur"] * ln ** amount
            if m.get("wobble"):
                m["wobble"] = n["wobble"] * w
            out.append(m)
        return out

    @staticmethod
    def _clamp_to(notes: list[dict], origin: list[dict]) -> list[dict]:
        out = []
        for n, o in zip(notes, origin):
            m = dict(n)
            r = m["f0"] / o["f0"]
            r2 = min(1 + CAP_PITCH, max(1 - CAP_PITCH, r))
            m["f0"], m["f1"] = o["f0"] * r2, o["f1"] * r2
            m["f0"] = min(G.HIGHEST, max(G.LOWEST, m["f0"]))
            m["f1"] = min(G.HIGHEST, max(G.LOWEST, m["f1"]))
            m["dur"] = min(o["dur"] * (1 + CAP_LEN), max(o["dur"] * (1 - CAP_LEN), m["dur"], G.SHORTEST_NOTE))
            out.append(m)
        return out

    def _today(self) -> str:
        b = self.brain
        now = getattr(b, "now", None)
        return (now.date() if now else (b.today if b and b.today else date.today())).isoformat()

    def _droid(self) -> str:
        """Each droid breeds its own chirps: two families with a 10 am hello get different ones."""
        return str(getattr(self.cart, "droid", {}).get("id", "")) or str(self.cart.folder.name)
