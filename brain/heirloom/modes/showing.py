from .base import Mode

HOLD = {"head_pitch": -18.0, "head_yaw": 0.0, "head_roll": 0.0}   # looks down at the desk and holds still


class Showing(Mode):
    """Showing a memory: head tilted down at the desk, held steady (a projector has to be still),
    iris narrowed, light up. Lasts about 9 seconds. "Not now" ends it and retires the photo (D45)."""
    name = "showing"
    duration = 9.0
    attentive = False
    ease_in, ease_out = 2.5, 1.5

    def apply(self, ch: dict[str, float], blend: float) -> None:
        for k, v in HOLD.items():                       # overrides glances and breathing on the head
            ch[k] = ch[k] * (1 - blend) + v * blend
        ch["iris"] += -0.15 * blend
        ch["light"] += 0.3 * blend
