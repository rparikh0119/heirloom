"""Dials wear: the five temperament dials drift with how the owner treats it (D37, D41).

What nudges which dial lives in brain/wear/dials.json, so it can change without code:

    {"when": "offended", "dial": "sass", "nudge": 1}
    {"when": "heart", "while": "sulk", "dial": "sass", "nudge": -1}
    {"when": "good", "after": "curious", "within": 5, "dial": "curiosity", "nudge": 1}

    when     the event that nudges (one name or a list)
    while    only counts in this mode (optional)
    after    only counts if this event happened in the last `within` seconds (optional)
    dial     which of the five dials
    nudge    +1 or -1 (times "step", e.g. 0.001)

Page per layer (layers/L1/dials.json):  {"sass": 0.012, "energy": -0.004}   drift from character.json

Blend: every layer's drift x its weight, added up, then capped at +-wear_limit (D41). Praise can
never push it further than that, however many years it lasts.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from ..character import DIALS
from .base import Wear

RULES_FILE = Path(__file__).resolve().parents[2] / "wear" / "dials.json"
RULE_KEYS = {"note", "when", "while", "after", "within", "dial", "nudge"}


def _as_list(v) -> list[str]:
    return [v] if isinstance(v, str) else list(v or [])


def load_rules(path: Path = RULES_FILE) -> tuple[float, list[dict]]:
    """Read the rules. Mistakes stop the brain with a message, like reaction files."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None
    step = float(raw.get("step", 0.001))
    rules = []
    for i, r in enumerate(raw.get("rules", [])):
        where = f"{path.name} rule {i + 1}"
        unknown = set(r) - RULE_KEYS
        if unknown:
            raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}. Allowed: {sorted(RULE_KEYS)}")
        if r.get("dial") not in DIALS:
            raise ValueError(f"{where}: dial {r.get('dial')!r}. Known: {list(DIALS)}")
        if not r.get("when"):
            raise ValueError(f"{where}: needs a \"when\" (which event nudges it)")
        if not isinstance(r.get("nudge"), (int, float)):
            raise ValueError(f"{where}: needs a number for \"nudge\", like 1 or -1")
        if r.get("after") and not isinstance(r.get("within"), (int, float)):
            raise ValueError(f"{where}: \"after\" needs \"within\" (seconds)")
        rules.append({**r, "when": _as_list(r["when"]), "after": _as_list(r.get("after"))})
    return step, rules


class DialsWear(Wear):
    name = "dials"

    def __init__(self, rules_file: Path = RULES_FILE) -> None:
        self.step, self.rules = load_rules(rules_file)
        self._recent: deque[tuple[str, float]] = deque(maxlen=20)   # what happened lately, for "after"

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.base = dict(brain.character.dials)          # character.json: the out-of-the-box droid
        self.limit = brain.character.wear_limit

    # ---- learning ----

    def record(self, event, mode: str, t: float) -> bool:
        page = self.cart.read_page(self.cart.active.id, self.name)
        changed = False
        for r in self.rules:
            if event.name not in r["when"]:
                continue
            if r.get("while") and r["while"] != mode:
                continue
            if r["after"] and not any(n in r["after"] and t - when <= r["within"] for n, when in self._recent):
                continue
            d = r["dial"]
            # Each layer's own drift is capped too, so one owner can't bank more than the limit.
            page[d] = max(-self.limit, min(self.limit, page.get(d, 0.0) + r["nudge"] * self.step))
            changed = True
        self._recent.append((event.name, t))
        if changed:
            self.cart.write_page(self.cart.active.id, self.name, {k: round(v, 6) for k, v in page.items()})
        return changed

    # ---- blending ----

    def effective(self, on=None) -> dict[str, float]:
        """The dials it has today: character.json + every layer's drift x weight, capped (D41)."""
        weights = self.cart.weights(on)
        out = {}
        for d in DIALS:
            drift = sum(w * self.cart.read_page(lid, self.name).get(d, 0.0) for lid, w in weights.items())
            drift = max(-self.limit, min(self.limit, drift))
            out[d] = max(0.0, min(1.0, self.base[d] + drift))
        return out

    def apply(self, brain) -> None:
        brain.character.dials.update(self.effective(brain.today))

    def validate(self, data: dict, where: str) -> None:
        for k, v in data.items():
            if k not in DIALS:
                raise ValueError(f"{where}: unknown dial {k!r}. Known: {list(DIALS)}")
            if not isinstance(v, (int, float)):
                raise ValueError(f"{where}: {k} must be a number, got {v!r}")
