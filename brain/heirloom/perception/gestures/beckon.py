from .base import Gesture

DEPTH = 0.10       # how far index straightness must dip and recover to count as one curl
CURLS = 2          # curls needed
WINDOW = 2.5       # seconds
STILL_SPEED = 0.25


class Beckon(Gesture):
    """Palm up, index finger curling in and out ("come here").

    Measured as relative dips, not fixed thresholds: a real beckon only hooks the finger
    partway (straightness ~0.95 -> ~0.75 in testing). It rarely fully curls.
    """
    name = "beckon"
    event = "curious"
    kind = "motion"
    priority = 10

    def check(self, hand, memory, ctx):
        recent = memory.recent(WINDOW)
        if not recent or min(h.palm_normal[1] for h in recent) <= 0.4:   # palm must stay up
            return False
        if memory.palm_speed() >= STILL_SPEED:
            return False
        cycles, peak, trough, dipping = 0, None, None, False
        for h in recent:
            s = h.fingers["index"]
            if peak is None:
                peak = s
            elif not dipping:
                peak = max(peak, s)
                if s < peak - DEPTH:
                    dipping, trough = True, s
            else:
                trough = min(trough, s)
                if s > trough + DEPTH:
                    cycles += 1
                    dipping, peak = False, s
        return cycles >= CURLS
