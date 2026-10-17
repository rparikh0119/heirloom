"""Heirloom's brain: modes, reactions and presence, combined into one pose per tick.

Modes:
    awake     presence runs normally (idle or attending to you)
    back_off  told "not now": looks away, dims, ignores you for a while
    sleep     head down, iris closed, ignores you until woken
"""
from __future__ import annotations

from .behavior.expressions import ExpressionPlayer
from .behavior.presence import CHANNELS, Presence
from .body.base import Pose

SLEEP_POSE = {"head_pitch": -22, "head_yaw": 0, "head_roll": 4, "base_yaw": 0,
              "antenna_left": -40, "antenna_right": -40, "iris": 0.03, "light": 0.08}
BACK_OFF_SECONDS = 20.0


class HeirloomBrain:
    def __init__(self, play_sound) -> None:
        """play_sound(name) is called whenever the brain wants to chirp."""
        self.presence = Presence()
        self.expr = ExpressionPlayer()
        self.play_sound = play_sound
        self.mode = "awake"
        self._back_off_left = 0.0
        self._sleepiness = 0.0     # 0 awake .. 1 fully asleep, eased so it droops gradually
        self._last_attending = False

    # ---------- reactions to events ----------
    def handle(self, event: str) -> None:
        if self.mode == "sleep":
            if event in ("wave", "wake"):
                self.mode = "awake"
                self.expr.play("stretch")
                self.play_sound("wake")
            return  # asleep: ignores everything else

        if event == "wave":
            self._back_off_left = 0.0
            self.mode = "awake"
            self.expr.play("hello")
            self.play_sound("hello")
        elif event == "good":
            self.expr.play("happy")
            self.play_sound("happy")
        elif event == "not_now":
            self.mode = "back_off"
            self._back_off_left = BACK_OFF_SECONDS
            self.expr.play("sheepish")
            self.play_sound("sad")
        elif event == "sleep":
            self.mode = "sleep"
            self.play_sound("sleepy")
        elif event == "curious":
            self.expr.play("curious")
            self.play_sound("curious")

    # ---------- every tick ----------
    def step(self, dt: float, user_head) -> tuple[Pose, dict]:
        if self.mode == "back_off":
            self._back_off_left -= dt
            if self._back_off_left <= 0:
                self.mode = "awake"

        # Only pay attention to the user when awake.
        attending_input = user_head if self.mode == "awake" else None
        pose, info = self.presence.step(dt, attending_input)
        ch = pose.channels()

        # Notice chirp the moment it starts attending.
        attending = info["mode"] == "attend"
        if attending and not self._last_attending:
            self.play_sound("notice")
        self._last_attending = attending

        if self.mode == "back_off":
            ch["head_pitch"] -= 8
            ch["head_yaw"] += 25        # looks away to its left
            ch["iris"] -= 0.2
            ch["light"] -= 0.25

        # Drift toward or away from the sleep pose.
        target = 1.0 if self.mode == "sleep" else 0.0
        rate = 0.6 if target > self._sleepiness else 1.5   # falls asleep slowly, wakes quickly
        self._sleepiness += (target - self._sleepiness) * min(1.0, rate * dt)
        if self._sleepiness > 0.001:
            for k in CHANNELS:
                ch[k] += (SLEEP_POSE[k] - ch[k]) * self._sleepiness

        for k, v in self.expr.step(dt).items():
            ch[k] += v

        ch["iris"] = min(1.0, max(0.0, ch["iris"]))
        ch["light"] = min(1.0, max(0.0, ch["light"]))

        info = {**info, "mode": self.mode if self.mode != "awake" else info["mode"],
                "expression": self.expr.name or ""}
        return Pose(**ch), info
