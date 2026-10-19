from .base import Mode


class BackOff(Mode):
    """Told "not now": looks away to its left and dims, ignores you for a while."""
    name = "back_off"
    duration = 20.0
    attentive = False
    ease_in, ease_out = 3.0, 2.0
    offsets = {"head_pitch": -8, "head_yaw": 25, "iris": -0.2, "light": -0.25}
