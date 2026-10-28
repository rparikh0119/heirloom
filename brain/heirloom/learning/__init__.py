"""Learning loop v0: which authored move lands, per situation (proposed D74, D75, D77 to D79, D81).

    reward.py   reads warm / cold / nothing in the seconds after it answers (the reward interpreter)
    log.py      every decision and its reward, one JSON line each (the decision record)
    ../wear/responses.py   the learner itself: "worked X of Y times" tallies kept in the cartridge

Only reactions with "choices" learn, and only when the brain runs with learn=True (run.py --learn).
"""
from .log import DecisionLog
from .reward import COLD, WARM, RewardInterpreter

__all__ = ["DecisionLog", "RewardInterpreter", "WARM", "COLD"]
