"""Reactions: what Heirloom does when an event arrives. One JSON file each, in brain/reactions/.

    {
      "note": "Thumbs up or 'good job': a happy wiggle.",
      "when": "good",                 a brain event, or a list of them
      "motion": "happy",              an expression (optional)
      "sound": "happy",               a chirp (optional)
      "mode": "sulk",                 start a mode, or "awake" to end the current one (optional)
      "only_while": ["sulk"],         only fires in these modes (optional)
      "works_while": ["sulk"],        still fires during a mode that normally blocks reactions (optional)
      "ignored_while": ["back_off"]   never fires in these modes (optional)
      "choices": ["hello", "happy"]   other authored moves it may learn to answer with (optional,
                                      only with --learn). "motion" stays the default it starts from
    }

Which reaction wins for an event:
    1. one whose "only_while" lists the current mode
    2. otherwise a general one (no "only_while"), unless the current mode blocks it
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REACTIONS_DIR = Path(__file__).resolve().parents[1] / "reactions"
KEYS = {"note", "when", "motion", "sound", "mode", "only_while", "works_while", "ignored_while", "choices"}


@dataclass
class Reaction:
    file: str
    when: list[str]
    motion: str | None = None
    sound: str | None = None
    mode: str | None = None
    only_while: list[str] = field(default_factory=list)
    works_while: list[str] = field(default_factory=list)
    ignored_while: list[str] = field(default_factory=list)
    note: str = ""
    choices: list[str] = field(default_factory=list)


class ReactionError(ValueError):
    pass


def _as_list(v) -> list[str]:
    return [v] if isinstance(v, str) else list(v or [])


def load_reactions(folder: Path = REACTIONS_DIR, motions=None, sounds=None, modes=None) -> list[Reaction]:
    """Read every reaction file. Mistakes stop the brain with a message naming the file,
    so a typo never fails silently."""
    out = []
    for path in sorted(folder.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ReactionError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None
        unknown = set(raw) - KEYS
        if unknown:
            raise ReactionError(f"{path.name}: unknown field(s) {sorted(unknown)}. Allowed: {sorted(KEYS)}")
        if not raw.get("when"):
            raise ReactionError(f"{path.name}: needs a \"when\" (which event it reacts to)")
        r = Reaction(file=path.name, when=_as_list(raw["when"]), motion=raw.get("motion"),
                     sound=raw.get("sound"), mode=raw.get("mode"),
                     only_while=_as_list(raw.get("only_while")), works_while=_as_list(raw.get("works_while")),
                     ignored_while=_as_list(raw.get("ignored_while")), note=raw.get("note", ""),
                     choices=_as_list(raw.get("choices")))
        if motions is not None and r.motion and r.motion not in motions:
            raise ReactionError(f"{path.name}: no motion called {r.motion!r}. Known: {sorted(motions)}")
        if r.choices and not r.motion:
            raise ReactionError(f"{path.name}: \"choices\" needs a \"motion\" too (the move it starts from)")
        if motions is not None:
            for c in r.choices:
                if c not in motions:
                    raise ReactionError(f"{path.name}: choice {c!r} isn't a motion. Known: {sorted(motions)}")
        if sounds is not None and r.sound and r.sound not in sounds:
            raise ReactionError(f"{path.name}: no sound called {r.sound!r}. Known: {sorted(sounds)}")
        if modes is not None:
            for m in [r.mode] * bool(r.mode) + r.only_while + r.works_while + r.ignored_while:
                if m != "awake" and m not in modes:
                    raise ReactionError(f"{path.name}: no mode called {m!r}. Known: awake, {', '.join(sorted(modes))}")
        out.append(r)
    return out


def choose(reactions: list[Reaction], event: str, mode: str, mode_blocks: bool) -> Reaction | None:
    """Pick the reaction for this event in this mode, or None if it's ignored."""
    candidates = [r for r in reactions if event in r.when]
    for r in candidates:
        if mode in r.only_while:
            return r
    for r in candidates:
        if r.only_while or mode in r.ignored_while:
            continue
        if mode_blocks and mode not in r.works_while:
            continue
        return r
    return None
