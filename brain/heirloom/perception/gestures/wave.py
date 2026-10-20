import numpy as np

from .base import Gesture
from .hand import unit

SWING = 0.03       # metres the fingertips must travel before a change of direction counts
REVERSALS = 3      # direction changes needed
WINDOW = 1.2       # seconds of motion to look at


class Wave(Gesture):
    """Open hand, fingers up, swinging side to side."""
    name = "wave"
    event = "wave"
    kind = "motion"
    priority = 10      # checked before palm_out, so a waving hand isn't "stop"

    def check(self, hand, memory, ctx):
        if not (hand.open and hand.middle_dir[1] > 0.3):
            return False
        recent = memory.recent(WINDOW)
        if len(recent) < 8:
            return False
        pts = np.array([h.middle_tip for h in recent])
        # "Side to side" from the person's point of view: horizontal, across the line to the robot.
        to_robot = unit(np.array([-pts[-1][0], 0.0, -pts[-1][2]]))
        across = np.array([to_robot[2], 0.0, -to_robot[0]])
        x = pts @ across
        reversals, direction, anchor = 0, 0, x[0]
        for v in x[1:]:
            if direction >= 0 and v < anchor - SWING:
                reversals += direction > 0
                direction, anchor = -1, v
            elif direction <= 0 and v > anchor + SWING:
                reversals += direction < 0
                direction, anchor = 1, v
            elif (direction > 0 and v > anchor) or (direction < 0 and v < anchor):
                anchor = v
        return reversals >= REVERSALS
