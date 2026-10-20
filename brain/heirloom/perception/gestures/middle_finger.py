from .base import Gesture


class MiddleFinger(Gesture):
    """Middle finger straight, index, ring and little curled. Heirloom's favourite thing to be offended by."""
    name = "middle_finger"
    event = "offended"

    def check(self, hand, memory, ctx):
        return hand.ext("middle") and all(hand.curl(f) for f in ("index", "ring", "little"))
