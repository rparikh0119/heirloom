"""Dialect wear (v0): every moment gets its own chirp, and the chirps pass down (proposed D85 to D87).

The core chirps (hello, happy, sleepy...) are fixed and readable by anyone. On top of them each
household grows a few family chirps: when the droid answers a moment (the 10 am hello, the 3:30
break), it uses a chirp bred from its usual sound for that reaction. So the 10 am hello still
reads as a hello, in the family's own accent. Strangers hear "hello". The family hears "our hello".

    minted     the first time it answers that moment, bred from the reaction's usual chirp
    distinct   always differs from every other chirp in note count or direction (genome.MIN_DIST)
    kept       one page per layer, so the chirps travel in the cartridge
    passed on  a woken moment (moments wear, "from") speaks with the old keeper's chirp

Not yet (next): drift, where the accent bends toward the versions the family reacts warmly to.

Page per layer (layers/L1/dialect.json):
    {"L1.m01": {"parent": "hello", "notes": [...], "minted": "2026-10-25", "from": null}}
"""
from __future__ import annotations

from datetime import date

from ..sound import chirps as C
from ..sound import genome as G
from .base import Wear

PREFIX = "m:"        # moment chirps are played by name as "m:L1.m01"


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
            others += [c["notes"] for c in self.chirps.values()]
            notes = G.breed(G.capture(parent), others, seed=f"{self._droid()}:{moment_id}")
            rec = {"parent": parent, "notes": notes, "minted": self._today(), "from": None}
            print(f"[dialect] new family chirp for {moment_id}, bred from \"{parent}\"")
        page = self.cart.read_page(lid, self.name)
        page[moment_id] = rec
        self.cart.write_page(lid, self.name, page)
        self.chirps[moment_id] = {**rec, "layer": lid}
        G.register(PREFIX + moment_id, rec["notes"])
        return PREFIX + moment_id

    def _today(self) -> str:
        b = self.brain
        now = getattr(b, "now", None)
        return (now.date() if now else (b.today if b and b.today else date.today())).isoformat()

    def _droid(self) -> str:
        """Each droid breeds its own chirps: two families with a 10 am hello get different ones."""
        return str(getattr(self.cart, "droid", {}).get("id", "")) or str(self.cart.folder.name)
