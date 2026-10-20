"""A gesture plug-in. One file per gesture in this folder, found automatically.

    class ThumbsUp(Gesture):
        name = "thumbs_up"
        event = "good"                  # the brain event it sends (needs a reaction file)
        def check(self, hand, memory, ctx):
            return all(hand.curl(f) for f in FINGERS) and hand.thumb_dir[1] > 0.7

kind = "pose"    held for HOLD seconds, fires once per hold (let go to repeat)
kind = "motion"  fires the moment check() is True, then motion history is cleared
hands = 2        check_both(left, right, ctx) instead of check()

ctx has "head": where the person's head is (robot space, or None) and "t": time in seconds.
"""
from __future__ import annotations

HOLD = 0.30   # seconds a pose must be held before it counts


class Gesture:
    name = ""
    event = ""
    kind = "pose"      # "pose" or "motion"
    hands = 1          # 1 or 2
    priority = 0       # higher is checked first (two-hand and motion gestures beat poses)
    hold = HOLD

    def check(self, hand, memory, ctx) -> bool:
        """One-hand gestures: is it happening in this frame?"""
        return False

    def check_both(self, left, right, ctx) -> bool:
        """Two-hand gestures."""
        return False

    def health(self) -> tuple[bool, str]:
        return True, "ok"
