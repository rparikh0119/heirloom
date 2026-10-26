import numpy as np

from .base import Gesture

THUMB_OUT = 0.80      # how straight the thumb must be (1 = perfectly straight)
SQUARE = 0.5          # index and thumb roughly at right angles: |cos(angle)| below this
APART_MIN = 0.12      # metres between the hands, so it's a frame (not a heart or a clap)
APART_MAX = 0.70


def l_shape(h) -> bool:
    """One hand making an L: index out, thumb out at roughly a right angle, other fingers curled."""
    return (h.ext("index") and h.curl("middle") and h.curl("ring") and h.curl("little")
            and h.thumb > THUMB_OUT
            and abs(float(np.dot(h.index_dir, h.thumb_dir))) < SQUARE)


class Frame(Gesture):
    """Both hands make an L and frame a picture, like a photographer: take a photo (D02, D72).
    Works silently, so photos don't need voice (a loud playtest room, or roommates watching TV)."""
    name = "frame"
    event = "take_photo"
    hands = 2
    priority = 15      # after the heart, before one-hand gestures
    hold = 0.4

    def check_both(self, left, right, ctx):
        apart = float(np.linalg.norm(left.palm - right.palm))
        return (l_shape(left) and l_shape(right)
                and APART_MIN < apart < APART_MAX
                and float(np.linalg.norm(left.index_tip - right.index_tip)) > 0.08)
