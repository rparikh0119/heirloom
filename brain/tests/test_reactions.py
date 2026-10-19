"""Checks the reaction files. Run:  python tests/test_reactions.py

It tells you which events still have no reaction file, then plays a short scenario.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.brain import HeirloomBrain  # noqa: E402
from heirloom.reactions import ReactionError  # noqa: E402

# Every event a sense can send today, and what should happen.
EXPECTED = {
    "listen":   "heard its name: perks up (motion listen, sound listen), starts the 'listening' mode",
    "wave":     "hello wiggle + hello chirp, and ends any mode it's in (\"mode\": \"awake\")",
    "good":     "happy wiggle + happy chirp",
    "heart":    "love motion + love chirp",
    "scold":    "sheepish motion + 'no' chirp",
    "not_now":  "sheepish motion + sad chirp, starts 'back_off'",
    "offended": "offended motion + grumble, starts 'sulk' (works during a sulk too)",
    "sleep":    "sleepy chirp, starts 'sleep'",
    "curious":  "curious motion + curious chirp",
    "sorry":    "only while sulking: curious motion + notice chirp, back to awake",
    "wake":     "only while asleep: stretch + wake chirp, back to awake",
}


def main() -> None:
    try:
        brain = HeirloomBrain(play_sound=lambda name: None)
    except ReactionError as e:
        print(f"Problem in a reaction file:\n  {e}")
        return
    general = {e for r in brain.reactions if not r.only_while for e in r.when}
    special = {(e, m) for r in brain.reactions for m in r.only_while for e in r.when}
    have = general | {e for e, m in special if (e, m) in (("sorry", "sulk"), ("wake", "sleep"))}
    print(f"Loaded {len(brain.reactions)} reaction files.\n")
    missing = [e for e in EXPECTED if e not in have]
    for e in EXPECTED:
        print(f"  {'OK     ' if e in have else 'MISSING'} {e:9s} {EXPECTED[e]}")
    if missing:
        print(f"\n{len(missing)} to go: {', '.join(missing)}")
        return

    # Short scenario: offend it, try to cheer it up (ignored), then make up with a heart.
    for event, expect in [("offended", "sulk"), ("good", "sulk"), ("heart", "awake"),
                          ("sleep", "sleep"), ("good", "sleep"), ("wake", "awake")]:
        brain.handle(event)
        assert brain.mode == expect, f"after {event!r} expected mode {expect!r}, got {brain.mode!r}"
    print("\nScenario passed: sulk ignores praise, a heart ends it, sleep ignores praise, 'wake up' wakes it.")


if __name__ == "__main__":
    main()
