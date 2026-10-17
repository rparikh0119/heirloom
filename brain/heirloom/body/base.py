"""The Heirloom body interface. Everything here is in Heirloom units (see docs/architecture.md)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields


@dataclass
class Pose:
    """A target pose. None means 'leave this channel as it is'."""
    head_pitch: float | None = None     # degrees, + looks up
    head_yaw: float | None = None       # degrees, + looks left
    head_roll: float | None = None      # degrees, + tilts left
    base_yaw: float | None = None       # degrees, + turns left
    antenna_left: float | None = None   # degrees, 0 upright
    antenna_right: float | None = None  # degrees, 0 upright
    iris: float | None = None           # 0 closed .. 1 wide
    light: float | None = None          # 0 off .. 1 full

    def channels(self) -> dict[str, float]:
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}


REST = Pose(0, 0, 0, 0, 0, 0, 0.6, 0.5)


class Body(ABC):
    """A robot (real, simulated or virtual) the brain can drive."""

    #: Channels this body physically has. Others are accepted and ignored.
    supports: frozenset[str] = frozenset()

    def __enter__(self) -> "Body":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()

    def connect(self) -> None:  # noqa: B027
        """Open the connection. Optional."""

    def disconnect(self) -> None:  # noqa: B027
        """Close the connection. Optional."""

    @abstractmethod
    def move(self, pose: Pose, duration: float = 0.5) -> None:
        """Move smoothly to a pose over `duration` seconds. Blocks until done."""

    def set_target(self, pose: Pose) -> None:
        """Jump to a pose right now, without interpolation. For continuous control loops
        (the caller does the smoothing). Default: a very short move."""
        self.move(pose, 0.02)

    def rest(self, duration: float = 1.0) -> None:
        self.move(REST, duration)
