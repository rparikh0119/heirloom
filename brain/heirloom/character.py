"""Character: the five temperament dials (D22), read from brain/character.json.

Every Heirloom starts from the same dials (D37). Later the Wear System nudges them with its owner,
never further than wear_limit from where they started. Learned values go in the cartridge, not here.

What each dial does today (0..1, 0.5 = the original behaviour):
    curiosity     how often it glances around when alone
    sass          how long it sulks
    boldness      how far away it notices you
    energy        how big and fast its expressions are
    warmth_speed  how fast it warms up to you (used by the Wear System, not yet)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CHARACTER_FILE = Path(__file__).resolve().parents[1] / "character.json"
DIALS = ("curiosity", "sass", "boldness", "energy", "warmth_speed")


@dataclass
class Character:
    dials: dict[str, float] = field(default_factory=lambda: {d: 0.5 for d in DIALS})
    wear_limit: float = 0.25

    def __getattr__(self, name: str) -> float:
        if name in DIALS:
            return self.dials[name]
        raise AttributeError(name)

    # ---- what the dials mean in behaviour ----
    @property
    def sulk_seconds(self) -> float:
        return 3.0 + 6.0 * self.sass                 # 3 s (agreeable) .. 9 s (holds a grudge)

    @property
    def notice_distance(self) -> float:
        return 1.5 + 2.0 * self.boldness             # 1.5 m (shy) .. 3.5 m (forward)

    @property
    def motion_scale(self) -> float:
        return 0.7 + 0.6 * self.energy               # 0.7x (calm) .. 1.3x (bouncy), size and speed

    @property
    def glance_gap(self) -> float:
        return 1.5 - self.curiosity                  # 1.5x slower (uninterested) .. 0.5x (investigates everything)


def load_character(path: Path = CHARACTER_FILE) -> Character:
    if not path.exists():
        return Character()
    raw = json.loads(path.read_text(encoding="utf-8"))
    dials = {d: 0.5 for d in DIALS}
    for k, v in raw.get("dials", {}).items():
        if k not in DIALS:
            raise ValueError(f"character.json: unknown dial {k!r}. Known: {list(DIALS)}")
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"character.json: {k} must be between 0 and 1, got {v}")
        dials[k] = float(v)
    return Character(dials=dials, wear_limit=float(raw.get("wear_limit", 0.25)))
