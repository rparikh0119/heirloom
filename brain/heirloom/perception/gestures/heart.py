import numpy as np

from .base import Gesture

TOUCH = 0.045   # metres: index tips (and thumb tips) closer than this count as touching


class Heart(Gesture):
    """Both hands: index tips touching on top, thumb tips touching below."""
    name = "heart"
    event = "heart"
    hands = 2
    priority = 20      # two-hand gestures first. While it's on, one-hand gestures are ignored

    def check_both(self, left, right, ctx):
        return (np.linalg.norm(left.index_tip - right.index_tip) < TOUCH
                and np.linalg.norm(left.thumb_tip - right.thumb_tip) < TOUCH
                and (left.index_tip[1] + right.index_tip[1]) / 2 > (left.thumb_tip[1] + right.thumb_tip[1]) / 2 + 0.03
                and np.linalg.norm(left.wrist - right.wrist) > 0.08)
