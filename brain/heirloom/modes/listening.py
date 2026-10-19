from .base import Mode


class Listening(Mode):
    """Heard its name: antennas up for a few seconds, waiting for what you say next."""
    name = "listening"
    duration = 5.0
    ends_on_any_event = True
    ease_in, ease_out = 6.0, 3.0
    offsets = {"antenna_left": 22, "antenna_right": 22, "head_pitch": 4, "iris": 0.15}
