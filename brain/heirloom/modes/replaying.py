from .base import Mode


class Replaying(Mode):
    """Playing back a voice memory: head tilted as if listening along, antennas lowered, quiet.
    The brain sets the duration to the recording's length."""
    name = "replaying"
    duration = 5.0
    silent = True
    ease_in, ease_out = 3.0, 1.5
    offsets = {"head_roll": 9, "head_pitch": -5, "antenna_left": -12, "antenna_right": -12, "light": 0.15}
