"""Patina wear: moves wear in with use (D55, D56, D59, D60).

Every expression keeps its own count of how often it has played. Three things happen with use:

1. Settling (weeks). A new move hesitates: a beat of pause, a wobble, stiff and a little small.
   With use the pause goes, it gets quicker, bigger and eased. A worn move keeps a little
   looseness, so it never turns machine-perfect (Okada's weak robots, R51).
       settle = 1 - exp(-uses / uses_to_settle)

2. Character (years). The moves a home uses most slowly take on that home's dials: a bold home's
   droid leans in, a sassy one flicks its antennas at the end, a calm one stays small and slow.
   Two droids that start identical end up moving differently (経年変化, R67; wenwan, R54).
       depth = 1 - exp(-uses / uses_to_deepen)
       effect = (dial - 0.5) x per_dial value x depth

3. Variation (every play). No two plays are exactly the same: speed and size shift a few
   percent each time. Repetition is why people returned Hyodol (R59).

And rust (Rule 5, D19): after days with no moments at all, settling slips partly back, so it's
stiff and shy when you return. Each move it plays loosens it again, so it warms back up within a
few moments. Rust is never written to the cartridge, it comes from the date of the last moment.

Every number lives in brain/wear/patina.json. They are design values for Riya to tune, not research.

Page per layer (layers/L1/patina.json):  {"hello": {"uses": 120, "last": "2026-10-23"}}
Blend: uses from every layer x its weight (Wear System v0), so a kept past keeps its worn moves.
"""
from __future__ import annotations

import json
import math
import random
from datetime import date
from pathlib import Path

from ..behavior.expressions import EXPRESSIONS, ExpressionPlayer
from ..character import DIALS
from .base import Wear

SETTINGS_FILE = Path(__file__).resolve().parents[2] / "wear" / "patina.json"
SETTLE_KEYS = {"hesitate_s", "wobble_deg", "speed", "size", "smooth"}
CHARACTER_KEYS = set(ExpressionPlayer.PLAIN)          # settle keys + lean_deg, flick_deg, tilt_deg
SETTINGS_KEYS = {"note", "uses_to_settle", "fresh", "worn", "character", "vary", "rust"}


def _need(cond: bool, where: str, msg: str) -> None:
    if not cond:
        raise ValueError(f"{where}: {msg}")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None
    n = path.name
    unknown = set(raw) - SETTINGS_KEYS
    _need(not unknown, n, f"unknown field(s) {sorted(unknown)}. Allowed: {sorted(SETTINGS_KEYS)}")
    _need(_num(raw.get("uses_to_settle")) and raw["uses_to_settle"] > 0, n, "needs \"uses_to_settle\" (a number above 0)")
    for end in ("fresh", "worn"):
        style = raw.get(end)
        _need(isinstance(style, dict), n, f"needs a \"{end}\" style")
        missing, extra = SETTLE_KEYS - set(style), set(style) - SETTLE_KEYS
        _need(not missing and not extra, n, f"\"{end}\" must have exactly {sorted(SETTLE_KEYS)}"
              + (f", missing {sorted(missing)}" if missing else "") + (f", unknown {sorted(extra)}" if extra else ""))
    ch = raw.get("character")
    _need(isinstance(ch, dict), n, "needs a \"character\" section")
    _need(_num(ch.get("uses_to_deepen")) and ch["uses_to_deepen"] > 0, n, "character needs \"uses_to_deepen\" (a number above 0)")
    for dial, effects in ch.get("per_dial", {}).items():
        _need(dial in DIALS, n, f"character.per_dial: unknown dial {dial!r}. Known: {list(DIALS)}")
        bad = set(effects) - CHARACTER_KEYS
        _need(not bad, n, f"character.per_dial.{dial}: unknown effect(s) {sorted(bad)}. Known: {sorted(CHARACTER_KEYS)}")
    _need(_num(raw.get("vary")) and 0 <= raw["vary"] < 0.5, n, "needs \"vary\" (0 to 0.5, e.g. 0.06)")
    rust = raw.get("rust")
    _need(isinstance(rust, dict) and set(rust) == {"after_days", "full_days", "most", "loosen"}, n,
          "\"rust\" must have exactly after_days, full_days, most, loosen")
    _need(0 <= rust["after_days"] < rust["full_days"], n, "rust: after_days must be below full_days")
    _need(0 <= rust["most"] <= 1 and 0 <= rust["loosen"] <= 1, n, "rust: most and loosen go from 0 to 1")
    return raw


class PatinaWear(Wear):
    name = "patina"

    def __init__(self, settings_file: Path = SETTINGS_FILE, seed: int | None = None) -> None:
        self.settings = load_settings(settings_file)
        self.settle: dict[str, float] = {}
        self.depth: dict[str, float] = {}
        self.rust = 0.0                       # 0 = in practice, up to rust.most after a long time apart
        self.rng = random.Random(seed)
        self.brain = None
        self._last: date | None = None        # the last day it did anything, across every layer

    @property
    def wear(self) -> dict[str, float]:       # kept for the time skip and older callers
        return self.settle

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain
        brain.expr.style = self.style
        days = [date.fromisoformat(rec["last"]) for layer in cartridge.layers
                for rec in cartridge.read_page(layer.id, self.name).values() if "last" in rec]
        self._last = max(days) if days else None
        self._check_absence()                      # waking up after time apart starts it rusty

    def _today(self) -> date:
        return (self.brain.today if self.brain and self.brain.today else None) or date.today()

    # ---- rust (Rule 5) ----

    def rust_on(self, day: date) -> float:
        """How rusty it would be if it woke up on `day`, from the last moment's date."""
        if self._last is None:
            return 0.0
        r = self.settings["rust"]
        gap = (day - self._last).days
        if gap <= r["after_days"]:
            return 0.0
        return r["most"] * min(1.0, (gap - r["after_days"]) / (r["full_days"] - r["after_days"]))

    def _check_absence(self) -> None:
        self.rust = max(self.rust, self.rust_on(self._today()))

    # ---- learning ----

    def played(self, kind: str, name: str, t: float) -> bool:
        if kind != "motion":
            return False
        today = self._today()
        self._check_absence()
        self.rust *= 1.0 - self.settings["rust"]["loosen"]          # each move warms it back up
        self._last = today
        page = self.cart.read_page(self.cart.active.id, self.name)
        page[name] = {"uses": page.get(name, {}).get("uses", 0) + 1, "last": today.isoformat()}
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
        k1, k2 = self.settings["uses_to_settle"], self.settings["character"]["uses_to_deepen"]
        u = self.uses(brain.today)
        self.settle = {m: 1.0 - math.exp(-x / k1) for m, x in u.items()}
        self.depth = {m: 1.0 - math.exp(-x / k2) for m, x in u.items()}

    # ---- how a move plays right now ----

    def base_style(self, move: str) -> dict[str, float]:
        """Settling (with rust) plus this home's character. No per-play variation."""
        if self.brain is not None:
            self._check_absence()
        s = self.settle.get(move, 0.0) * (1.0 - self.rust)
        fresh, worn = self.settings["fresh"], self.settings["worn"]
        out = dict(ExpressionPlayer.PLAIN)
        out.update({k: fresh[k] + (worn[k] - fresh[k]) * s for k in SETTLE_KEYS})
        d = self.depth.get(move, 0.0)
        if d and self.brain is not None:
            dials = self.brain.character.dials
            for dial, effects in self.settings["character"].get("per_dial", {}).items():
                lean = dials[dial] - 0.5
                for k, v in effects.items():
                    out[k] += lean * v * d
        out["speed"] = max(0.3, out["speed"])
        out["size"] = max(0.3, out["size"])
        return out

    def style(self, move: str) -> dict[str, float]:
        """What the expression player asks for at the start of every play."""
        out = self.base_style(move)
        v = self.settings["vary"]
        out["speed"] *= 1.0 + self.rng.uniform(-v, v)
        out["size"] *= 1.0 + self.rng.uniform(-v, v)
        return out

    def validate(self, data: dict, where: str) -> None:
        for move, rec in data.items():
            if move not in EXPRESSIONS:
                raise ValueError(f"{where}: no expression called {move!r}")
            if not isinstance(rec, dict) or not isinstance(rec.get("uses"), int):
                raise ValueError(f"{where}: {move} needs {{\"uses\": a whole number}}")
            if "last" in rec:
                try:
                    date.fromisoformat(rec["last"])
                except (TypeError, ValueError):
                    raise ValueError(f"{where}: {move} \"last\" must be a date like 2026-10-23") from None
