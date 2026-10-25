from .base import Mode

# When each beep happens, in seconds from "take a picture". The last one is the shutter.
CUES = [(0.5, "tick"), (1.3, "tick"), (2.1, "tick"), (2.9, "snap")]
SNAP_AT = 2.9


class Shooting(Mode):
    """'Take a picture': looks at you, three countdown beeps, then the iris snaps shut and opens
    with a shutter chirp. Never automatic (D02). The brain plays the beeps and asks the body to
    capture on 'snap'."""
    name = "shooting"
    duration = 3.6
    blocks_by_default = True
    ease_in, ease_out = 6.0, 3.0
    offsets = {"antenna_left": 15, "antenna_right": 15, "light": 0.3}

    def enter(self) -> None:
        super().enter()
        self.t = 0.0
        self._cues = list(CUES)
        self._due: list[str] = []

    def step(self, dt: float) -> bool:
        self.t = getattr(self, "t", 0.0) + dt
        while getattr(self, "_cues", None) and self._cues[0][0] <= self.t:
            self._due.append(self._cues.pop(0)[1])
        return super().step(dt)

    def pop_cues(self) -> list[str]:
        due, self._due = getattr(self, "_due", []), []
        return due

    def apply(self, ch: dict[str, float], blend: float) -> None:
        super().apply(ch, blend)
        t = getattr(self, "t", 0.0)
        if SNAP_AT <= t < SNAP_AT + 0.25:            # the iris snaps shut and opens: the shutter
            ch["iris"] = 0.05
        elif t < SNAP_AT:                          # narrows a little with each beep, focusing
            ch["iris"] += -0.1 * blend * (t / SNAP_AT)
