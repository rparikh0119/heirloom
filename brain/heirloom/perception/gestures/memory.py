"""Per-hand memory: the last few seconds of HandStates, for gestures that are motions (wave, beckon)."""
from __future__ import annotations

from collections import deque

import numpy as np

KEEP = 3.0   # seconds of history


class HandMemory:
    def __init__(self) -> None:
        self.frames: deque[tuple[float, object]] = deque()   # (time, HandState)
        self.held: dict[str, float] = {}                      # pose gestures: how long held
        self.latched: set[str] = set()                        # pose gestures that fired and are still held

    def add(self, t: float, hand) -> None:
        self.frames.append((t, hand))
        while self.frames and t - self.frames[0][0] > KEEP:
            self.frames.popleft()

    def recent(self, seconds: float) -> list:
        """HandStates from the last `seconds`, oldest first."""
        if not self.frames:
            return []
        now = self.frames[-1][0]
        return [h for t, h in self.frames if now - t <= seconds]

    def palm_speed(self, seconds: float = 0.3) -> float:
        """How fast the palm moved over the last `seconds`, in metres per second."""
        recent = [(t, h) for t, h in self.frames if self.frames[-1][0] - t <= seconds]
        if len(recent) < 2:
            return 0.0
        (t0, h0), (t1, h1) = recent[0], recent[-1]
        return float(np.linalg.norm(h1.palm - h0.palm) / max(1e-3, t1 - t0))

    def clear_motion(self) -> None:
        """Forget recent motion, so one wave can't fire twice."""
        if self.frames:
            self.frames = deque([self.frames[-1]])
