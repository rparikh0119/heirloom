"""Events: everything Heirloom notices arrives as one of these, from any sense.

    Event("good", source="voice", data={"tone": "soft"})
    Event("offended", source="hands", data={"hand": "right"})

Senses can still send a plain string ("good"). as_event() turns it into an Event.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Event:
    name: str
    source: str = ""          # "voice", "hands", "keys", later "camera", "touch"...
    strength: float = 1.0     # how sure the sense is, 0..1
    data: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.name} ({self.source})" if self.source else self.name


def as_event(e: "Event | str", source: str = "") -> Event:
    return e if isinstance(e, Event) else Event(str(e), source=source)
