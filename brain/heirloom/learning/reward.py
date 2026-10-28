"""The reward interpreter: after the droid answers, did it land? (proposed D77, D48 warm/cold)

A window opens when the droid answers with a learnable move and closes after WINDOW seconds,
at the next thing it decides, or at the first clear reaction:

    warm  1     thumbs up / "good", a heart
    cold  0     "no", "not now", "shh", the middle finger
    skip        nothing, or any other command. Silence is NOT a zero: if it were, the most common
                case would teach it that everything is meh (Song et al. 2026, research report)

Guards (the report's push back on "learns what lands"): nothing here rewards you staying close,
staying longer or coming back. Only explicit reactions to the move it just made count.
Every cue is weighted 1.0 for now: they're all explicit. Implicit cues (a laugh, leaning in) would
come in around 0.3 to 0.5 later.
"""
from __future__ import annotations

from dataclasses import dataclass

WINDOW = 6.0                     # seconds. Design guess (the report: 5 to 8 s, no sourced number)
WARM = {"good": "thumbs up", "heart": "heart"}
COLD = {"scold": "\"no\"", "not_now": "not now", "shh": "shh", "offended": "middle finger"}
PASS_THROUGH = {"hearing", "listen", "unknown"}   # reflexes and "huh?" don't close the window


@dataclass
class Open:
    decision_id: str
    t: float


class RewardInterpreter:
    def __init__(self) -> None:
        self.open: Open | None = None

    def start(self, decision_id: str, t: float) -> None:
        self.open = Open(decision_id, t)

    def observe(self, event_name: str, t: float) -> tuple[str, int, str] | None:
        """An event arrived. Returns (decision_id, reward 1 or 0, cue) if it judged the last move,
        else None. Any other command closes the window without a reward."""
        if self.open is None or event_name in PASS_THROUGH:
            return None
        o, self.open = self.open, None
        if t - o.t > WINDOW:
            return None
        if event_name in WARM:
            return o.decision_id, 1, WARM[event_name]
        if event_name in COLD:
            return o.decision_id, 0, COLD[event_name]
        return None

    def expire(self, t: float) -> None:
        if self.open is not None and t - self.open.t > WINDOW:
            self.open = None
