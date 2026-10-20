from .base import Gesture

STILL_SPEED = 0.25   # m/s. The hand must be held about this still, so a wave isn't read as "stop"


class PalmOut(Gesture):
    """Open hand, palm facing the robot, held still: "not now"."""
    name = "palm_out"
    event = "not_now"

    def check(self, hand, memory, ctx):
        return hand.open and hand.toward_robot > 0.6 and memory.palm_speed() < STILL_SPEED
