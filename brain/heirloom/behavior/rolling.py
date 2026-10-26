"""Rolling: Heirloom drives across the desk (D23, it rolls). Beckon it and it comes to you.

The brain keeps track of where it is: drive = (x right, z forward) in metres from where it started,
in its own starting frame. Bodies that can roll move there (Unity slides the droid on the real desk,
the custom droid drives its wheels). The lab Reachy can't roll and ignores it.

Design values (tune by feel):
"""
from __future__ import annotations

import math

SPEED = 0.12          # metres per second at full speed. A calm desk droid, not a toy car
STOP_AT = 0.45        # stops this far from you (horizontal metres, head to head)
MIN_TRIP = 0.05       # closer than this to where it would stop: doesn't bother moving
MAX_ROAM = 0.35       # never further than this from its starting spot. No cliff sensors in MR yet,
                      # so this keeps it on the desk. The custom droid gets cliff sensors in winter
EASE = 0.12           # metres over which it slows down as it arrives


class Roller:
    def __init__(self) -> None:
        self.x = 0.0
        self.z = 0.0
        self.target: tuple[float, float] | None = None

    @property
    def moving(self) -> bool:
        return self.target is not None

    def toward(self, user_head) -> bool:
        """Plan a trip to a comfortable distance from the person. user_head is where they are
        relative to the droid's head right now (x right, y up, z forward). Returns False if
        it's already close enough or there's nobody."""
        if user_head is None:
            return False
        ux, _, uz = user_head
        d = math.hypot(ux, uz)
        if d - STOP_AT < MIN_TRIP:
            return False
        go = d - STOP_AT
        tx, tz = self.x + ux / d * go, self.z + uz / d * go
        r = math.hypot(tx, tz)
        if r > MAX_ROAM:                                   # stay on the desk
            tx, tz = tx / r * MAX_ROAM, tz / r * MAX_ROAM
        if math.hypot(tx - self.x, tz - self.z) < MIN_TRIP:
            return False
        self.target = (tx, tz)
        return True

    def home(self) -> bool:
        if math.hypot(self.x, self.z) < 0.01:
            return False
        self.target = (0.0, 0.0)
        return True

    def step(self, dt: float) -> bool:
        """Roll a little. Returns True on the frame it arrives."""
        if self.target is None:
            return False
        tx, tz = self.target
        dx, dz = tx - self.x, tz - self.z
        dist = math.hypot(dx, dz)
        speed = SPEED * min(1.0, max(0.15, dist / EASE))   # slows down as it arrives
        stepd = speed * dt
        if dist <= stepd or dist < 0.002:
            self.x, self.z, self.target = tx, tz, None
            return True
        self.x += dx / dist * stepd
        self.z += dz / dist * stepd
        return False
