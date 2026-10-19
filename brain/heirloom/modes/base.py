"""A mode is behaviour with its own timeline: sulking, sleeping, giving you space, listening.

Reactions (reactions/*.json) decide WHEN a mode starts. The mode decides HOW it looks while it lasts.
To add one, make a new file in this folder with a Mode subclass. The brain finds it by `name`.
"""
from __future__ import annotations


class Mode:
    name = ""
    duration: float | None = None   # seconds, None = until a reaction ends it
    blocks_by_default = False       # True: only reactions that list this mode can fire while it's on
    ends_on_any_event = False       # True: any new event ends it (listening)
    attentive = True                # False: stops looking at you while the mode is on
    ease_in = 3.0                   # how fast it blends in and out (higher = faster)
    ease_out = 2.0
    offsets: dict[str, float] = {}  # added to the pose while active, scaled by the blend

    def __init__(self) -> None:
        self.left = 0.0

    def enter(self) -> None:
        """Called every time the mode starts, including restarting it while it's already on."""
        self.left = self.duration or 0.0

    def step(self, dt: float) -> bool:
        """Advance time. Return False when the mode is over."""
        if self.duration is None:
            return True
        self.left -= dt
        return self.left > 0

    def target(self) -> float:
        """How strongly to show the mode right now (0..1). Override for things like a peek."""
        return 1.0

    def apply(self, ch: dict[str, float], blend: float) -> None:
        """Change the pose. Default: add the offsets, scaled by blend."""
        for k, v in self.offsets.items():
            ch[k] += v * blend

    def health(self) -> tuple[bool, str]:
        """Self-check hook for the future self-maintenance feature."""
        return True, "ok"
