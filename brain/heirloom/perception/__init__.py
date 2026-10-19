"""Perception: turning the world (voice, hands, later the robot's camera and touch) into brain events."""
from .gestures import GestureDetector
from .intents import INTENTS, WAKE_WORDS, match

__all__ = ["GestureDetector", "INTENTS", "WAKE_WORDS", "match"]
