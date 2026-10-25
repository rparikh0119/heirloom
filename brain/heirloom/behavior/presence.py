"""Presence: breathe, notice the user, look at them, glance around when alone.

Pure logic. Feed it the user's head position each tick and it returns a Pose.
Units: metres in, Heirloom degrees out. User position is in the robot's space,
measured from its head at rest: x = robot's right, y = up, z = forward.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from ..body.base import Pose

CHANNELS = ("head_pitch", "head_yaw", "head_roll", "base_yaw", "antenna_left", "antenna_right", "iris", "light")


@dataclass
class PresenceConfig:
    notice_distance: float = 2.5   # metres. Further than this, it doesn't notice you
    head_yaw_limit: float = 40.0
    pitch_min: float = -20.0
    pitch_max: float = 25.0
    base_share: float = 0.6        # how much of a big turn the base takes over
    base_kicks_in: float = 25.0    # degrees off-centre before the base starts helping
    breath_period: float = 4.0
    attend_ease: float = 0.25      # seconds. Lower = snappier head
    idle_ease: float = 0.7
    base_ease: float = 1.5
    glance_gap: float = 1.0        # multiplies the wait between glances (character: curiosity)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _ease(current: float, target: float, dt: float, tau: float) -> float:
    return current + (target - current) * (1.0 - math.exp(-dt / max(tau, 1e-3)))


class Presence:
    def __init__(self, config: PresenceConfig | None = None) -> None:
        self.cfg = config or PresenceConfig()
        self.t = 0.0
        self.pose = {c: 0.0 for c in CHANNELS} | {"iris": 0.6, "light": 0.5}
        self.mode = "idle"
        self._perk = 0.0            # seconds left of the "oh, hi" reaction
        self._perk_lift = 30.0      # how far the antennas go up during it
        self._glance_yaw = 0.0
        self._next_glance = random.uniform(4, 8) * self.cfg.glance_gap
        self._glance_end = 0.0

    def perk(self, seconds: float, lift: float = 30.0) -> None:
        """A quick antenna lift: when it notices you, or hears you start talking."""
        if seconds >= self._perk:
            self._perk, self._perk_lift = seconds, lift

    def step(self, dt: float, user_head: tuple[float, float, float] | None) -> tuple[Pose, dict]:
        c = self.cfg
        self.t += dt
        breath = math.sin(2 * math.pi * self.t / c.breath_period)

        user_dist = None
        if user_head is not None:
            x, y, z = user_head
            user_dist = math.sqrt(x * x + y * y + z * z)
        present = user_dist is not None and user_dist < c.notice_distance

        if present and self.mode != "attend":
            self.perk(0.6, 30.0)    # just noticed you
        self.mode = "attend" if present else "idle"

        target = {k: 0.0 for k in CHANNELS}
        if present:
            x, y, z = user_head
            yaw = math.degrees(math.atan2(-x, z))                 # + = robot's left
            pitch = math.degrees(math.atan2(y, math.hypot(x, z)))  # + = up
            base_goal = c.base_share * yaw if abs(yaw) > c.base_kicks_in else 0.0
            target["base_yaw"] = base_goal
            target["head_yaw"] = _clamp(yaw - self.pose["base_yaw"], -c.head_yaw_limit, c.head_yaw_limit)
            target["head_pitch"] = _clamp(pitch, c.pitch_min, c.pitch_max)
            target["head_roll"] = _clamp(-0.08 * target["head_yaw"], -6, 6)   # slight curious tilt
            target["iris"], target["light"] = 0.85, 0.8
            head_tau = c.attend_ease
        else:
            # Alone: occasional glances.
            if self.t > self._next_glance:
                self._glance_yaw = random.choice([-1, 1]) * random.uniform(10, 22)
                self._glance_end = self.t + random.uniform(1.0, 2.0)
                self._next_glance = self._glance_end + random.uniform(4, 8) * c.glance_gap
            target["head_yaw"] = self._glance_yaw if self.t < self._glance_end else 0.0
            target["head_roll"] = -0.25 * target["head_yaw"]
            target["iris"], target["light"] = 0.6, 0.5
            head_tau = c.idle_ease

        # Breathing rides on top of everything.
        target["head_pitch"] += 2.0 * breath
        target["antenna_left"] += 6.0 * breath
        target["antenna_right"] += 6.0 * breath
        target["iris"] += 0.06 * breath

        # The "oh, hi" perk when it first notices you.
        if self._perk > 0:
            self._perk -= dt
            target["antenna_left"] += self._perk_lift
            target["antenna_right"] += self._perk_lift
            target["iris"] = max(target["iris"], 0.6 + self._perk_lift / 75)

        for k in CHANNELS:
            tau = c.base_ease if k == "base_yaw" else (0.12 if k in ("iris", "antenna_left", "antenna_right") else head_tau)
            self.pose[k] = _ease(self.pose[k], target[k], dt, tau)

        info = {"mode": self.mode, "user_distance": user_dist if user_dist is not None else -1}
        return Pose(**self.pose), info
