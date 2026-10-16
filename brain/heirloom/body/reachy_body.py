"""Reachy Mini adapter (simulator or lab robot). The ONLY file that imports reachy_mini.

Reachy Mini is a test body. Reachy has no iris, light or projector, so those channels are ignored here
and drawn in MR by Unity instead.
"""
from __future__ import annotations

import math

from .base import Body, Pose

# Sign flips from Heirloom convention to Reachy convention.
# TODO(week 6): confirm each sign in the simulator and flip any that move the wrong way.
PITCH_SIGN = -1.0   # Heirloom + = look up
YAW_SIGN = 1.0
ROLL_SIGN = 1.0
BASE_YAW_SIGN = 1.0
ANTENNA_SIGN = 1.0


class ReachyBody(Body):
    supports = frozenset({"head_pitch", "head_yaw", "head_roll", "base_yaw", "antenna_left", "antenna_right"})

    def __init__(self) -> None:
        self._mini = None
        self._last = Pose(0, 0, 0, 0, 0, 0)

    def connect(self) -> None:
        from reachy_mini import ReachyMini  # imported here only
        self._mini = ReachyMini(media_backend="no_media")
        self._mini.__enter__()

    def disconnect(self) -> None:
        if self._mini is not None:
            self._mini.__exit__(None, None, None)
            self._mini = None

    def move(self, pose: Pose, duration: float = 0.5) -> None:
        from reachy_mini.utils import create_head_pose

        # Fill unset channels from the last commanded pose so partial poses work.
        merged = Pose(**{**self._last.channels(), **pose.channels()})
        self._last = merged

        head = create_head_pose(
            pitch=PITCH_SIGN * merged.head_pitch,
            yaw=YAW_SIGN * merged.head_yaw,
            roll=ROLL_SIGN * merged.head_roll,
            degrees=True,
        )
        # Reachy antennas: [right, left] in radians.
        antennas = [
            ANTENNA_SIGN * math.radians(merged.antenna_right),
            ANTENNA_SIGN * math.radians(merged.antenna_left),
        ]
        self._mini.goto_target(
            head=head,
            antennas=antennas,
            body_yaw=BASE_YAW_SIGN * math.radians(merged.base_yaw),
            duration=max(duration, 0.05),
        )
