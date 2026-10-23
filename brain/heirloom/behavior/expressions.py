"""Expressions: short keyframed motions layered ON TOP of whatever the robot is doing.

Each expression is one JSON file in brain/expressions/, made by hand or with the pose recorder in Unity:

    {
      "note": "Praised: bouncy nods with antennas waving.",
      "keys": [
        {"t": 0.0,  "ch": {}},
        {"t": 0.12, "ch": {"head_pitch": 7, "antenna_left": 30, "iris": 0.35}},
        {"t": 0.95, "ch": {}}
      ]
    }

"t" is seconds from the start. "ch" holds OFFSETS added to the current pose (degrees, or 0..1 for
iris and light), so a happy wiggle works whether it's looking left, right or up. Start and end
with an empty "ch" so it blends in and out smoothly.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

EXPRESSIONS_DIR = Path(__file__).resolve().parents[2] / "expressions"
CHANNELS = ("head_pitch", "head_yaw", "head_roll", "base_yaw", "antenna_left", "antenna_right", "iris", "light")


class ExpressionError(ValueError):
    pass


def load_expressions(folder: Path = EXPRESSIONS_DIR) -> dict[str, list[tuple[float, dict]]]:
    """Read every expression file. Mistakes stop with a message naming the file."""
    out = {}
    for path in sorted(folder.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ExpressionError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None
        keys = raw.get("keys")
        if not isinstance(keys, list) or len(keys) < 2:
            raise ExpressionError(f"{path.name}: needs a \"keys\" list with at least 2 keyframes")
        frames, last_t = [], -1.0
        for i, k in enumerate(keys):
            t, ch = k.get("t"), k.get("ch", {})
            if not isinstance(t, (int, float)) or t <= last_t:
                raise ExpressionError(f"{path.name}: keyframe {i} needs a \"t\" larger than the one before")
            bad = set(ch) - set(CHANNELS)
            if bad:
                raise ExpressionError(f"{path.name}: keyframe {i} has unknown channel(s) {sorted(bad)}. Known: {list(CHANNELS)}")
            frames.append((float(t), {c: float(v) for c, v in ch.items()}))
            last_t = t
        out[path.stem] = frames
    return out


EXPRESSIONS = load_expressions()


def _smooth(s: float) -> float:
    return s * s * (3 - 2 * s)


class ExpressionPlayer:
    """Plays one expression at a time. A `style` hook (set by the patina wear plug-in) can make a
    move hesitant and stiff when it's new, or quick and confident when it's worn in. Without a
    style, every expression plays exactly as keyframed."""

    PLAIN = {"hesitate_s": 0.0, "wobble_deg": 0.0, "speed": 1.0, "size": 1.0, "smooth": 1.0}

    def __init__(self, scale: float = 1.0) -> None:
        self.name: str | None = None
        self._t = 0.0
        self.scale = scale     # character energy: >1 bigger and faster, <1 smaller and slower
        self.style = None      # callable(name) -> dict like PLAIN, or None
        self._st = dict(self.PLAIN)
        self._hold = 0.0
        self._clock = 0.0

    def play(self, name: str) -> None:
        if name not in EXPRESSIONS:
            raise KeyError(f"No expression called {name!r}")
        self.name, self._t, self._clock = name, 0.0, 0.0
        self._st = {**self.PLAIN, **(self.style(name) if self.style else {})}
        self._hold = self._st["hesitate_s"]

    def step(self, dt: float) -> dict[str, float]:
        """Advance time and return the offsets to add this frame (empty when nothing is playing)."""
        if self.name is None:
            return {}
        st = self._st
        self._clock += dt
        out: dict[str, float] = {}
        if self._hold > 0:                       # a beat of hesitation before it commits
            self._hold -= dt
        else:
            keys = EXPRESSIONS[self.name]
            self._t += dt * self.scale * st["speed"]
            if self._t >= keys[-1][0]:
                self.name = None
                return {}
            for (t0, a), (t1, b) in zip(keys, keys[1:]):
                if t0 <= self._t < t1:
                    u = (self._t - t0) / (t1 - t0)
                    s = u + (_smooth(u) - u) * st["smooth"]          # stiff (linear) .. smooth (eased)
                    gain = self.scale * st["size"]
                    out = {k: (a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * s) * gain for k in set(a) | set(b)}
                    break
        if st["wobble_deg"]:                     # a small unsteady tremor on the head (Okada's wobble)
            w = st["wobble_deg"]
            out["head_roll"] = out.get("head_roll", 0.0) + w * math.sin(2 * math.pi * 5.0 * self._clock)
            out["head_yaw"] = out.get("head_yaw", 0.0) + 0.6 * w * math.sin(2 * math.pi * 3.3 * self._clock + 1.0)
        return out
