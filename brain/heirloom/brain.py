"""Heirloom's brain core. It doesn't know any specific reaction or mode by name.

Every tick:  events -> reactions (reactions/*.json) -> modes (heirloom/modes/) -> one pose.

    awake      the default: presence runs (idle, or attending to you)
    any mode   loaded from heirloom/modes/, started and ended by reactions

To add behaviour, add a reaction file or a mode file. This file shouldn't need to change.

With a cartridge, wear plug-ins (heirloom/wear/) learn from every event and shape the character.
Without one, it behaves exactly like the out-of-the-box droid.
"""
from __future__ import annotations

from .behavior.expressions import EXPRESSIONS, ExpressionPlayer
from .behavior.presence import Presence, PresenceConfig
from .body.base import Pose
from .character import load_character
from .events import Event, as_event
from .modes import load_modes
from .reactions import choose, load_reactions
from .sound.chirps import CHIRPS
from .wear import load_wear

AWAKE = "awake"


class HeirloomBrain:
    def __init__(self, play_sound, reactions_dir=None, cartridge=None) -> None:
        """play_sound(name) is called whenever the brain wants to chirp.
        cartridge: an opened Cartridge, or None to run without learning."""
        self.character = load_character()
        c = self.character
        self.presence = Presence(PresenceConfig(notice_distance=c.notice_distance, glance_gap=c.glance_gap))
        self.expr = ExpressionPlayer(scale=c.motion_scale)
        self.play_sound = play_sound
        self.modes = load_modes()
        for mode in self.modes.values():
            mode.character = c
        kwargs = {"motions": EXPRESSIONS, "sounds": CHIRPS, "modes": self.modes}
        if reactions_dir is not None:
            kwargs["folder"] = reactions_dir
        self.reactions = load_reactions(**kwargs)
        self.mode = AWAKE
        self._blend = {name: 0.0 for name in self.modes}   # 0 = off .. 1 = fully in that mode
        self._last_attending = False
        self.t = 0.0                                         # seconds since it woke up

        # Wear: only with a cartridge. Each plug-in blends its layers into the brain.
        self.cartridge = cartridge
        self.wear = load_wear() if cartridge is not None else []
        for w in self.wear:
            w.attach(cartridge, self)
            w.apply(self)
        self._refresh_character()

    def _refresh_character(self) -> None:
        """Push the current dials into the parts that use them. Modes read them live."""
        c = self.character
        self.presence.cfg.notice_distance = c.notice_distance
        self.presence.cfg.glance_gap = c.glance_gap
        self.expr.scale = c.motion_scale

    # ---------- events ----------
    def handle(self, event: "Event | str") -> str | None:
        """React to one event. Returns the reaction file used, or None if it was ignored."""
        e = as_event(event)
        changed = [w for w in self.wear if w.record(e, self.mode, self.t)]
        for w in changed:
            w.apply(self)
        if changed:
            self._refresh_character()

        current = self.modes.get(self.mode)
        if current and current.ends_on_any_event and e.name != current.name:
            self.mode = AWAKE              # e.g. listening ends when you say the actual command
            current = None

        r = choose(self.reactions, e.name, self.mode, bool(current and current.blocks_by_default))
        if r is None:
            if not any(e.name in x.when for x in self.reactions):
                print(f"[brain] no reaction file for '{e.name}' (add one in brain/reactions/)")
            return None

        if r.mode:
            self._set_mode(r.mode)
        if r.motion:
            self.expr.play(r.motion)
        if r.sound:
            self._sound(r.sound)
        return r.file

    def _sound(self, name: str) -> None:
        current = self.modes.get(self.mode)
        if not (current and current.silent):
            self.play_sound(name)

    def _set_mode(self, name: str) -> None:
        self.mode = name
        if name != AWAKE:
            self.modes[name].enter()

    # ---------- every tick ----------
    def step(self, dt: float, user_head) -> tuple[Pose, dict]:
        self.t += dt
        current = self.modes.get(self.mode)
        if current and not current.step(dt):
            self.mode, current = AWAKE, None

        # Presence only follows you when the mode allows it (sulking, sleeping and backing off don't).
        attentive = current is None or current.attentive
        pose, info = self.presence.step(dt, user_head if attentive else None)
        ch = pose.channels()

        # Notice chirp the moment it starts attending.
        attending = info["mode"] == "attend"
        if attending and not self._last_attending:
            self._sound("notice")
        self._last_attending = attending

        # Ease every mode in or out, then let each one shape the pose.
        for name, mode in self.modes.items():
            target = mode.target() if name == self.mode else 0.0
            rate = mode.ease_in if target > self._blend[name] else mode.ease_out
            self._blend[name] += (target - self._blend[name]) * min(1.0, rate * dt)
            if self._blend[name] > 0.001:
                mode.apply(ch, self._blend[name])

        for k, v in self.expr.step(dt).items():
            ch[k] += v
        ch["iris"] = min(1.0, max(0.0, ch["iris"]))
        ch["light"] = min(1.0, max(0.0, ch["light"]))

        shown = self.mode if self.mode != AWAKE else info["mode"]
        return Pose(**ch), {**info, "mode": shown, "expression": self.expr.name or ""}
