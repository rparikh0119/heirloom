from .base import Mode

PEEK_SECONDS = 1.8   # the last part of the sulk: half turns back to check on you


class Sulk(Mode):
    """Offended: back turned, chin up, antennas pinned. Peeks at you near the end, then forgives."""
    name = "sulk"
    duration = 6.0
    blocks_by_default = True        # ignores you. It isn't built to please you (Rule 7)
    attentive = False
    ease_in, ease_out = 4.0, 1.2
    offsets = {"base_yaw": 70, "head_yaw": 20, "head_pitch": 6, "head_roll": -4,
               "antenna_left": -45, "antenna_right": -45, "iris": -0.3, "light": -0.2}

    def target(self) -> float:
        return 0.45 if self.left < PEEK_SECONDS else 1.0
