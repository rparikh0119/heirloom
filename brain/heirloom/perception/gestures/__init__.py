"""Hand gestures, read from hand joints. One plug-in file per gesture in this folder.

No Meta code: the same logic works on Quest hands now and the robot's own camera later.
To add a gesture, add a file with a Gesture subclass (see base.py and thumbs_up.py), then a
reaction file in brain/reactions/ for its event.

Input: one "hands" message from Unity (or, in winter, from the robot's camera through MediaPipe):
    {"type": "hands", "left_tracked": bool, "left": [x,y,z]*26, "right_tracked": bool, "right": [...]}
"""
from __future__ import annotations

import importlib
import pkgutil

import numpy as np

from .base import Gesture
from .hand import FINGERS, HandState, straightness
from .memory import HandMemory

COOLDOWN_SAME = 2.5    # seconds before the same gesture can fire again
COOLDOWN_ANY = 1.0     # seconds after any gesture before another can fire


def load_gestures() -> list[Gesture]:
    for info in pkgutil.iter_modules(__path__):
        if info.name not in ("base", "hand", "memory"):
            importlib.import_module(f"{__name__}.{info.name}")
    found, stack = [], list(Gesture.__subclasses__())
    while stack:
        cls = stack.pop()
        stack += cls.__subclasses__()
        if cls.name:
            found.append(cls())
    return sorted(found, key=lambda g: -g.priority)


class GestureDetector:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        self.gestures = load_gestures()
        self._t = 0.0
        self._mem = {"left": HandMemory(), "right": HandMemory()}
        self._both = HandMemory()          # hold and latch state for two-hand gestures
        self._last_fired: dict[str, float] = {}
        self._last_any = -99.0
        self._next_debug = 0.0

    def step(self, dt: float, msg: dict | None, head=None) -> list[str]:
        """Feed the newest hands message (or None) and the person's head position (or None).
        Returns the brain events that fired this tick."""
        self._t += dt
        ctx = {"head": None if head is None else np.asarray(head, dtype=float), "t": self._t}
        states: dict[str, HandState] = {}
        for side in self._mem:
            joints = None
            if msg and msg.get(f"{side}_tracked"):
                arr = np.asarray(msg.get(side) or [], dtype=float)
                if arr.size == 78 and np.all(np.isfinite(arr)):
                    joints = arr.reshape(26, 3)
            if joints is None:
                self._mem[side] = HandMemory()      # lost the hand: forget its history
                continue
            states[side] = HandState(joints, side)
            self._mem[side].add(self._t, states[side])

        fired: list[str] = []
        ready: list[tuple[Gesture, str]] = []

        # Two-hand gestures. While one is happening, one-hand gestures are ignored.
        two_hand_on = False
        for g in (g for g in self.gestures if g.hands == 2):
            on = "left" in states and "right" in states and g.check_both(states["left"], states["right"], ctx)
            two_hand_on |= on
            if self._update(g, on, self._both, dt):
                ready.append((g, "both"))

        if not two_hand_on:
            for side, hand in states.items():
                for g in (g for g in self.gestures if g.hands == 1):
                    if self._update(g, g.check(hand, self._mem[side], ctx), self._mem[side], dt):
                        ready.append((g, side))

        for g, side in ready:      # already in priority order
            if self._can_fire(g.name):
                self._last_fired[g.name] = self._last_any = self._t
                mem = self._both if side == "both" else self._mem[side]
                if g.kind == "pose":
                    mem.latched.add(g.name)       # holding a pose fires it once
                else:
                    mem.clear_motion()            # one wave can't fire twice
                print(f"[gesture] {side} {g.name} -> {g.event}")
                fired.append(g.event)
                break

        if self.debug and self._t >= self._next_debug:
            self._next_debug = self._t + 0.5
            lines = [h.summary() for h in states.values()]
            print("[hands] " + ("   |   ".join(lines) if lines else "no hands"))
        return fired

    @staticmethod
    def _update(g: Gesture, on: bool, mem: HandMemory, dt: float) -> bool:
        """Track holding and latching. Returns True if this gesture is ready to fire."""
        if g.kind == "motion":
            return bool(on)
        mem.held[g.name] = mem.held.get(g.name, 0.0) + dt if on else 0.0
        if not on:
            mem.latched.discard(g.name)       # let go of the pose, so it can fire again next time
            return False
        return mem.held[g.name] >= g.hold and g.name not in mem.latched

    def _can_fire(self, name: str) -> bool:
        if self._t - self._last_any < COOLDOWN_ANY:
            return False
        return self._t - self._last_fired.get(name, -99.0) >= COOLDOWN_SAME


__all__ = ["FINGERS", "Gesture", "GestureDetector", "HandState", "straightness"]
