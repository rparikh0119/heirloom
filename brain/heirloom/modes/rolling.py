from .base import Mode


class Rolling(Mode):
    """On its way: keeps looking at you, antennas swept back a little, eye bright. The brain ends
    it when it arrives (or after 8 seconds)."""
    name = "rolling"
    duration = 8.0
    ease_in, ease_out = 4.0, 2.0
    offsets = {"antenna_left": -14, "antenna_right": -14, "head_pitch": -3, "iris": 0.1}
