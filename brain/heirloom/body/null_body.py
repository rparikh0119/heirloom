"""A body with no robot. Prints commands. Unity is the only visual."""
import time

from .base import Body, Pose


class NullBody(Body):
    supports = frozenset(Pose().__dataclass_fields__)

    def move(self, pose: Pose, duration: float = 0.5) -> None:
        print(f"[null] {duration:.2f}s -> {pose.channels()}")
        time.sleep(duration)

    def set_target(self, pose: Pose) -> None:
        pass  # called ~30x a second, so stay quiet

    def play_sound(self, name: str) -> None:
        print(f"[null] chirp: {name}")
