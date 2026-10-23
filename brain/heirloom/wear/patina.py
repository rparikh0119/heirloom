"""Patina wear: moves wear in with use (D55, D56).

Every expression keeps its own count of how often it has played. A move the droid has done a
thousand times is quick, confident and smooth. A move it has rarely done is still hesitant: a beat
of pause, a small wobble, stiff and a little small. So a fresh Heirloom hesitates before almost
everything, and a worn one answers instantly in the habits of its home, while the moves its home
never asked for stay shy.

How it feels at each end lives in brain/wear/patina.json (design values, tuned by Riya):

    "uses_to_wear": 40          about 40 uses = mostly worn, a few hundred = fully worn
    "fresh": {...}              how a never-used move plays
    "worn":  {...}              how a fully worn move plays

Wear for a move:  w = 1 - exp(-uses / uses_to_wear)   (0 = brand new, 1 = worn smooth)
Each style value slides from fresh to worn by w.

Page per layer (layers/L1/patina.json):  {"hello": {"uses": 120}, "happy": {"uses": 35}}
Blend: uses from every layer x its weight (Wear System v0), so a kept past keeps its worn moves.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from ..behavior.expressions import EXPRESSIONS, ExpressionPlayer
from .base import Wear

SETTINGS_FILE = Path(__file__).resolve().parents[2] / "wear" / "patina.json"
STYLE_KEYS = set(ExpressionPlayer.PLAIN)


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None
    if not isinstance(raw.get("uses_to_wear"), (int, float)) or raw["uses_to_wear"] <= 0:
        raise ValueError(f"{path.name}: needs \"uses_to_wear\" (a number above 0)")
    for end in ("fresh", "worn"):
        style = raw.get(end)
        if not isinstance(style, dict):
            raise ValueError(f"{path.name}: needs a \"{end}\" style")
        missing, unknown = STYLE_KEYS - set(style), set(style) - STYLE_KEYS
        if missing or unknown:
            raise ValueError(f"{path.name}: \"{end}\" must have exactly {sorted(STYLE_KEYS)}"
                             + (f", missing {sorted(missing)}" if missing else "")
                             + (f", unknown {sorted(unknown)}" if unknown else ""))
    return raw


class PatinaWear(Wear):
    name = "patina"

    def __init__(self, settings_file: Path = SETTINGS_FILE) -> None:
        self.settings = load_settings(settings_file)
        self.wear: dict[str, float] = {}

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        brain.expr.style = self.style

    # ---- learning ----

    def played(self, kind: str, name: str, t: float) -> bool:
        if kind != "motion":
            return False
        page = self.cart.read_page(self.cart.active.id, self.name)
        page[name] = {"uses": page.get(name, {}).get("uses", 0) + 1}
        self.cart.write_page(self.cart.active.id, self.name, page)
        return True

    # ---- blending ----

    def uses(self, on=None) -> dict[str, float]:
        """Effective uses per move: every layer's count x its weight."""
        out: dict[str, float] = {}
        for lid, w in self.cart.weights(on).items():
            for move, rec in self.cart.read_page(lid, self.name).items():
                out[move] = out.get(move, 0.0) + w * rec.get("uses", 0)
        return out

    def apply(self, brain) -> None:
        k = self.settings["uses_to_wear"]
        self.wear = {m: 1.0 - math.exp(-u / k) for m, u in self.uses(brain.today).items()}

    def style(self, move: str) -> dict[str, float]:
        """How this move plays right now, from fresh to worn."""
        w = self.wear.get(move, 0.0)
        fresh, worn = self.settings["fresh"], self.settings["worn"]
        return {key: fresh[key] + (worn[key] - fresh[key]) * w for key in STYLE_KEYS}

    def validate(self, data: dict, where: str) -> None:
        for move, rec in data.items():
            if move not in EXPRESSIONS:
                raise ValueError(f"{where}: no expression called {move!r}")
            if not isinstance(rec, dict) or not isinstance(rec.get("uses"), int):
                raise ValueError(f"{where}: {move} needs {{\"uses\": a whole number}}")
