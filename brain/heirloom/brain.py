"""Heirloom's brain: modes, reactions and presence, combined into one pose per tick.

Modes:
    awake     presence runs normally (idle or attending to you)
    back_off  told "not now": looks away, dims, ignores you for a while
    sulk      offended (middle finger): turns its back on you, then peeks and forgives
    sleep     head down, iris closed, ignores you until woken

On top of the mode, "listening" holds the antennas up for a few seconds after it hears its name.
Every mode eases in and out, because set_target sends poses straight to the body.
"""
from __future__ import annotations

from .behavior.expressions import ExpressionPlayer
from .behavior.presence import CHANNELS, Presence
from .body.base import Pose

SLEEP_POSE = {"head_pitch": -22, "head_yaw": 0, "head_roll": 4, "base_yaw": 0,
              "antenna_left": -40, "antenna_right": -40, "iris": 0.03, "light": 0.08}

# Offsets added on top of presence while a mode is active (scaled by how far it has eased in).
MODE_OFFSETS = {
    "back_off": {"head_pitch": -8, "head_yaw": 25, "iris": -0.2, "light": -0.25},
    "sulk":     {"base_yaw": 70, "head_yaw": 20, "head_pitch": 6, "head_roll": -4,   # back turned, chin up
                 "antenna_left": -45, "antenna_right": -45, "iris": -0.3, "light": -0.2},
    "listen":   {"antenna_left": 22, "antenna_right": 22, "head_pitch": 4, "iris": 0.15},
}
EASE_IN = {"back_off": 3.0, "sulk": 4.0, "listen": 6.0, "sleep": 0.6}
EASE_OUT = {"back_off": 2.0, "sulk": 1.2, "listen": 3.0, "sleep": 1.5}

BACK_OFF_SECONDS = 20.0
SULK_SECONDS = 6.0
PEEK_SECONDS = 1.8      # last part of the sulk: half turns back to check on you
LISTEN_SECONDS = 5.0


class HeirloomBrain:
    def __init__(self, play_sound) -> None:
        """play_sound(name) is called whenever the brain wants to chirp."""
        self.presence = Presence()
        self.expr = ExpressionPlayer()
        self.play_sound = play_sound
        self.mode = "awake"
        self._mode_left = 0.0       # seconds left in back_off or sulk
        self._listen_left = 0.0
        self._blend = {k: 0.0 for k in EASE_IN}   # 0 = off .. 1 = fully in that mode
        self._last_attending = False

    # ---------- reactions to events ----------
    def handle(self, event: str) -> None:
        if event != "listen":
            self._listen_left = 0.0   # any real command ends the listening window

        if self.mode == "sleep":
            if event in ("wave", "wake"):
                self.mode = "awake"
                self.expr.play("stretch")
                self.play_sound("wake")
            return  # asleep: ignores everything else, even its name

        if self.mode == "sulk":
            if event == "offended":           # doing it again: grumbles louder, sulks longer
                self._mode_left = SULK_SECONDS
                self.expr.play("offended")
                self.play_sound("grumble")
            elif event == "sorry":            # an apology ends it early
                self.mode = "awake"
                self.expr.play("curious")
                self.play_sound("notice")
            return  # otherwise ignores you. It isn't built to please you (Rule 7).

        if event == "listen":
            self._listen_left = LISTEN_SECONDS
            self.expr.play("listen")
            self.play_sound("listen")
        elif event == "wave":
            self.mode = "awake"
            self.expr.play("hello")
            self.play_sound("hello")
        elif event == "good":
            self.expr.play("happy")
            self.play_sound("happy")
        elif event == "scold":
            self.expr.play("sheepish")
            self.play_sound("no")
        elif event == "not_now":
            self.mode = "back_off"
            self._mode_left = BACK_OFF_SECONDS
            self.expr.play("sheepish")
            self.play_sound("sad")
        elif event == "offended":
            self.mode = "sulk"
            self._mode_left = SULK_SECONDS
            self.expr.play("offended")
            self.play_sound("grumble")
        elif event == "sleep":
            self.mode = "sleep"
            self.play_sound("sleepy")
        elif event == "curious":
            self.expr.play("curious")
            self.play_sound("curious")
        # "wake" and "sorry" while awake: nothing to do

    # ---------- every tick ----------
    def step(self, dt: float, user_head) -> tuple[Pose, dict]:
        if self.mode in ("back_off", "sulk"):
            self._mode_left -= dt
            if self._mode_left <= 0:
                self.mode = "awake"
        self._listen_left = max(0.0, self._listen_left - dt)

        # Only pay attention to the user when awake.
        attending_input = user_head if self.mode == "awake" else None
        pose, info = self.presence.step(dt, attending_input)
        ch = pose.channels()

        # Notice chirp the moment it starts attending.
        attending = info["mode"] == "attend"
        if attending and not self._last_attending:
            self.play_sound("notice")
        self._last_attending = attending

        # Ease every mode in or out.
        targets = {
            "back_off": 1.0 if self.mode == "back_off" else 0.0,
            "sulk": (0.0 if self.mode != "sulk" else 0.45 if self._mode_left < PEEK_SECONDS else 1.0),
            "listen": 1.0 if self._listen_left > 0 else 0.0,
            "sleep": 1.0 if self.mode == "sleep" else 0.0,
        }
        for k, target in targets.items():
            rate = EASE_IN[k] if target > self._blend[k] else EASE_OUT[k]
            self._blend[k] += (target - self._blend[k]) * min(1.0, rate * dt)

        for k, offsets in MODE_OFFSETS.items():
            if self._blend[k] > 0.001:
                for ch_name, v in offsets.items():
                    ch[ch_name] += v * self._blend[k]

        if self._blend["sleep"] > 0.001:
            for k in CHANNELS:
                ch[k] += (SLEEP_POSE[k] - ch[k]) * self._blend["sleep"]

        for k, v in self.expr.step(dt).items():
            ch[k] += v

        ch["iris"] = min(1.0, max(0.0, ch["iris"]))
        ch["light"] = min(1.0, max(0.0, ch["light"]))

        if self.mode != "awake":
            shown = self.mode
        elif self._listen_left > 0:
            shown = "listening"
        else:
            shown = info["mode"]
        info = {**info, "mode": shown, "expression": self.expr.name or ""}
        return Pose(**ch), info
