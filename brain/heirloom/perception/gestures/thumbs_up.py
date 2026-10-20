from .base import Gesture
from .hand import FINGERS


class ThumbsUp(Gesture):
    """Four fingers curled, thumb pointing up."""
    name = "thumbs_up"
    event = "good"

    def check(self, hand, memory, ctx):
        return all(hand.curl(f) for f in FINGERS) and hand.thumb_dir[1] > 0.7
