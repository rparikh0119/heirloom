"""Shh: index finger pressed to your lips. Heirloom goes quiet.  (Riya's first gesture module)

What you have to work with:
    hand.ext("index")      True if the index finger is extended  (also "middle", "ring", "little")
    hand.curl("middle")    True if that finger is curled
    hand.index_dir         unit vector, the way the index finger points. index_dir[1] is "how much up" (-1..1)
    hand.index_tip         where the index fingertip is (x, y, z metres, robot space)
    ctx["head"]            where the person's eyes are (x, y, z), or None if unknown
    np.linalg.norm(a - b)  distance between two points, in metres

Robot space: x right, y up, z forward (toward you). The robot's head is (0, 0, 0).
Your mouth is roughly MOUTH_BELOW_EYES below your eyes.

Test it without the headset:  python tests/test_shh.py
"""
import numpy as np

from .base import Gesture

MOUTH_BELOW_EYES = 0.09   # metres
NEAR_MOUTH = 0.08         # how close the fingertip has to be to count as "at your lips"
POINTS_UP = 0.6           # how vertical the finger has to be


class Shh(Gesture):
    name = "shh"
    event = "shh"

    def check(self, hand, memory, ctx):
        # TODO (Riya): return True only when ALL of these are true.
        #   1. We know where the head is (ctx["head"] is not None). If not, return False first.
        #   2. Index finger extended, middle / ring / little curled.
        #   3. The index finger points up (more than POINTS_UP).
        #   4. The fingertip is within NEAR_MOUTH of the mouth.
        #      Tip: mouth = ctx["head"] - np.array([0, MOUTH_BELOW_EYES, 0])
        return False
