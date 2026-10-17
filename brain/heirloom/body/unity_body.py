"""A body that lives in Unity. Interpolates moves and streams every frame over the link."""
from __future__ import annotations

import time

from ..link import LinkServer
from .base import REST, Body, Pose

FPS = 60


def min_jerk(s: float) -> float:
    """Smooth 0..1 easing with zero velocity and acceleration at both ends."""
    return s * s * s * (10 - 15 * s + 6 * s * s)


class UnityBody(Body):
    supports = frozenset(Pose().__dataclass_fields__)

    def __init__(self) -> None:
        self._pose = Pose(**REST.channels())
        self._link: LinkServer | None = None

    def connect(self) -> None:
        self._link = LinkServer.get()

    def move(self, pose: Pose, duration: float = 0.5) -> None:
        start = self._pose.channels()
        target = {**start, **pose.channels()}
        frames = max(1, int(duration * FPS))
        t0 = time.perf_counter()
        for i in range(1, frames + 1):
            s = min_jerk(i / frames)
            current = {k: start[k] + (target[k] - start[k]) * s for k in target}
            self._link.broadcast({"type": "pose", "ch": current})
            delay = t0 + i / FPS - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
        self._pose = Pose(**target)
