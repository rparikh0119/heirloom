"""Drive several bodies at once, e.g. the Reachy sim and Unity together."""
from __future__ import annotations

import threading

from .base import Body, Pose


class MultiBody(Body):
    def __init__(self, bodies: list[Body]) -> None:
        self.bodies = bodies
        self.supports = frozenset().union(*(b.supports for b in bodies))

    def connect(self) -> None:
        for b in self.bodies:
            b.connect()

    def disconnect(self) -> None:
        for b in self.bodies:
            b.disconnect()

    def move(self, pose: Pose, duration: float = 0.5) -> None:
        threads = [threading.Thread(target=b.move, args=(pose, duration)) for b in self.bodies]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def set_target(self, pose: Pose) -> None:
        for b in self.bodies:
            b.set_target(pose)

    def play_sound(self, name: str) -> None:
        for b in self.bodies:
            b.play_sound(name)
