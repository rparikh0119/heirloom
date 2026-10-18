"""Expressions: short keyframed motions layered ON TOP of whatever the robot is doing.

Each expression is a list of (time in seconds, offsets). Offsets are added to the current pose,
so a "happy wiggle" works whether it's looking left, right or up.
"""
from __future__ import annotations

EXPRESSIONS: dict[str, list[tuple[float, dict]]] = {
    "hello": [
        (0.00, {}),
        (0.15, {"antenna_left": 35, "antenna_right": 35, "head_pitch": 8, "iris": 0.3}),
        (0.35, {"antenna_left": 10, "antenna_right": 40, "head_roll": 7, "iris": 0.3}),
        (0.55, {"antenna_left": 40, "antenna_right": 10, "head_roll": -7, "iris": 0.3}),
        (0.80, {"antenna_left": 30, "antenna_right": 30, "head_pitch": 4, "iris": 0.2}),
        (1.10, {}),
    ],
    "happy": [
        (0.00, {}),
        (0.12, {"head_pitch": 7, "antenna_left": 30, "antenna_right": 30, "iris": 0.35, "light": 0.3}),
        (0.24, {"head_pitch": -2, "head_roll": 6, "antenna_left": 10, "antenna_right": 35, "iris": 0.35, "light": 0.3}),
        (0.36, {"head_pitch": 7, "antenna_left": 35, "antenna_right": 10, "iris": 0.35, "light": 0.3}),
        (0.48, {"head_pitch": -2, "head_roll": -6, "antenna_left": 10, "antenna_right": 35, "iris": 0.35, "light": 0.3}),
        (0.60, {"head_pitch": 6, "antenna_left": 30, "antenna_right": 30, "iris": 0.35, "light": 0.3}),
        (0.95, {}),
    ],
    "curious": [
        (0.00, {}),
        (0.25, {"head_roll": 15, "head_pitch": 5, "iris": 0.25}),
        (1.00, {"head_roll": 15, "head_pitch": 5, "iris": 0.25}),
        (1.35, {}),
    ],
    "sheepish": [   # plays when told "not now"
        (0.00, {}),
        (0.30, {"head_pitch": -10, "head_roll": -6, "antenna_left": -25, "antenna_right": -25, "iris": -0.3}),
        (0.80, {"head_pitch": -8, "head_roll": -4, "antenna_left": -20, "antenna_right": -20, "iris": -0.25}),
        (1.20, {}),
    ],
    "offended": [   # middle finger: recoils, antennas pinned flat (the sulk takes over after)
        (0.00, {}),
        (0.08, {"head_pitch": 14, "head_roll": -6, "antenna_left": -55, "antenna_right": -55, "iris": -0.4}),
        (0.30, {"head_pitch": 10, "head_roll": 5, "antenna_left": -50, "antenna_right": -50, "iris": -0.35}),
        (0.50, {"head_pitch": 12, "head_roll": -3, "antenna_left": -50, "antenna_right": -50, "iris": -0.35}),
        (0.90, {}),
    ],
    "listen": [     # heard its name: quick perk up (the listening hold takes over after)
        (0.00, {}),
        (0.12, {"antenna_left": 30, "antenna_right": 30, "head_pitch": 7, "iris": 0.3}),
        (0.40, {"antenna_left": 15, "antenna_right": 15, "head_pitch": 3, "iris": 0.15}),
        (0.60, {}),
    ],
    "stretch": [    # waking up
        (0.00, {}),
        (0.50, {"head_pitch": 22, "antenna_left": 50, "antenna_right": 50, "iris": 0.4}),
        (0.90, {"head_pitch": 18, "head_roll": 8, "antenna_left": 45, "antenna_right": 50, "iris": 0.4}),
        (1.15, {"head_pitch": 18, "head_roll": -8, "antenna_left": 50, "antenna_right": 45, "iris": 0.4}),
        (1.60, {}),
    ],
}


def _smooth(s: float) -> float:
    return s * s * (3 - 2 * s)


class ExpressionPlayer:
    def __init__(self) -> None:
        self.name: str | None = None
        self._t = 0.0

    def play(self, name: str) -> None:
        if name not in EXPRESSIONS:
            raise KeyError(f"No expression called {name!r}")
        self.name, self._t = name, 0.0

    def step(self, dt: float) -> dict[str, float]:
        """Advance time and return the offsets to add this frame (empty when nothing is playing)."""
        if self.name is None:
            return {}
        keys = EXPRESSIONS[self.name]
        self._t += dt
        if self._t >= keys[-1][0]:
            self.name = None
            return {}
        for (t0, a), (t1, b) in zip(keys, keys[1:]):
            if t0 <= self._t < t1:
                s = _smooth((self._t - t0) / (t1 - t0))
                return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * s for k in set(a) | set(b)}
        return {}
