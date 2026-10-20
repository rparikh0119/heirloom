from .base import Mode


class Quiet(Mode):
    """Shushed: no chirps for a minute. Still moves and looks at you, just silently."""
    name = "quiet"
    duration = 60.0
    silent = True
    ease_in, ease_out = 3.0, 2.0
    offsets = {"antenna_left": -15, "antenna_right": -15, "light": -0.2}
