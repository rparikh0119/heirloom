from .base import Mode


class Recording(Mode):
    """'Record this': listening hard, so it's obvious it's recording (D43). Antennas up and still,
    eye wide, light full. Other reactions wait. Ends when the recording is saved, cancelled with
    'not now', or after 15 seconds of nothing said."""
    name = "recording"
    duration = 15.0
    blocks_by_default = True
    silent = True                  # no chirps over your voice
    ease_in, ease_out = 5.0, 2.0
    offsets = {"antenna_left": 25, "antenna_right": 25, "iris": 0.3, "light": 0.5, "head_pitch": 4}
