"""The decision record (proposed D79). One JSON line per decision, one per reward, in the shape of
Vowpal Wabbit's contextual-bandit logs (context, candidates, probability of each), without VW:

    {"decision_id": "d_0007", "t": 12.4, "when": "2026-10-28T10:01:12", "seed": "hl-57c9:7",
     "context": {"cue": "wave", "tod": "morning", "mode": "awake"}, "candidates": ["hello", ...],
     "masked": [], "probs": [0.71, ...], "chosen": "hello", "explored": false, "learner": "bucket_ts/1"}
    {"decision_id": "d_0007", "reward": 1, "cue": "thumbs up", "delay_s": 1.8}

Logging the probability is what lets a future learner be scored on old logs (Li et al. 2011).
Lives in <cartridge>/logs/. To decide: whether it stays with the owner at a handoff (proposed D81 says it does).
"""
from __future__ import annotations

import json
from pathlib import Path


class DecisionLog:
    def __init__(self, path: Path | None) -> None:
        self.path = Path(path) if path else None
        self.lines: list[dict] = []           # also kept in memory, for tests and the overlay
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def for_cartridge(cls, cartridge) -> "DecisionLog":
        return cls(cartridge.folder / "logs" / "decisions.jsonl" if cartridge is not None else None)

    def write(self, line: dict) -> None:
        self.lines.append(line)
        if len(self.lines) > 500:
            self.lines = self.lines[-500:]
        if self.path:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(line) + "\n")
