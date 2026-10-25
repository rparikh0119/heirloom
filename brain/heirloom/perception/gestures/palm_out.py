import numpy as np

from .base import Gesture

STILL_SPEED = 0.25    # m/s. The hand must be held about this still, so a wave isn't read as "stop"
FACING = 0.75         # how squarely the palm faces the robot (1 = straight at it)
FINGERS_UP = 0.5      # how upright the fingers are (1 = straight up). A stop sign, not a reach
NOT_TOUCHING = 0.20   # metres. Closer than this to the robot's head is petting or reaching, not "stop"


class PalmOut(Gesture):
    """Open hand held up like a stop sign, palm facing the robot, held still: "not now".

    Tightened Oct 25 (D65): it used to fire on any open palm toward the robot, so reaching out
    to touch it or the end of a wave knocked it into giving you space. Now the fingers must point
    up, the hand must be away from its head, and it must be held a little longer.
    """
    name = "palm_out"
    event = "not_now"
    hold = 0.6

    def check(self, hand, memory, ctx):
        return (hand.open
                and hand.toward_robot > FACING
                and hand.middle_dir[1] > FINGERS_UP
                and float(np.linalg.norm(hand.palm)) > NOT_TOUCHING
                and memory.palm_speed() < STILL_SPEED)
