"""Chirp genomes (dialect v0, proposed D86). A chirp written as data, so it can be bred, kept and passed on.

A genome is a list of notes. Each note glides from f0 to f1 Hz, with an optional pause after it:
    [{"f0": 900, "f1": 1800, "dur": 0.08, "gap": 0.03, "shape": "sine", "wobble": 0, "wobble_hz": 0, "amp": 0.5}, ...]

What tells chirps apart (identity): how many notes, and whether each goes up, down or stays flat.
Rhythm and note count are what people tell sounds apart by best. Pitch alone is weak
(Brewster et al. 1993, earcons). So a new family chirp always differs from every other chirp
in note count or in the direction of at least one note.

What gives the family accent: exact pitches, lengths, wobble. These can drift later.

The core chirps in chirps.py stay as they are, readable by anyone. capture() reads one of them as a
genome, so new chirps can be bred from it and still sound related.
"""
from __future__ import annotations

import math
import random

import numpy as np

from . import chirps as C

FLAT = 0.05          # a glide smaller than 5% counts as flat
MIN_DIST = 1.0       # new chirps must differ by at least one note or one direction from every other chirp
LOWEST, HIGHEST = 180.0, 3200.0   # Hz, keeps chirps inside what a small speaker plays well
LONGEST = 1.0        # seconds
SHORTEST_NOTE = 0.04 # seconds. Shorter than the 0.125 s Brewster suggests for earcons, but these
                     # are fast chirps like the core set, and identity rides on count and direction


def capture(name: str) -> list[dict]:
    """Read a core chirp from chirps.py as a genome by listening in on the notes it asks for."""
    notes: list[dict] = []

    def tone(f0, f1, dur, shape="sine", wobble=0.0, wobble_hz=0.0, amp=0.5):
        notes.append({"f0": float(f0), "f1": float(f1), "dur": float(dur), "gap": 0.0, "shape": shape,
                      "wobble": float(wobble), "wobble_hz": float(wobble_hz), "amp": float(amp)})
        return np.zeros(1)

    def rest(dur):
        if notes:
            notes[-1]["gap"] += float(dur)
        return np.zeros(1)

    real = C.tone, C.rest
    C.tone, C.rest = tone, rest
    try:
        C.CHIRPS[name](1.0, 1.0)
    finally:
        C.tone, C.rest = real
    return notes


def recipe(genome: list[dict]):
    """Turn a genome into a recipe like the ones in chirps.py: (pitch, speed) -> sound parts."""
    def make(p: float, s: float) -> list[np.ndarray]:
        parts = []
        for n in genome:
            parts.append(C.tone(n["f0"] * p, n["f1"] * p, n["dur"] * s, n.get("shape", "sine"),
                                wobble=n.get("wobble", 0.0), wobble_hz=n.get("wobble_hz", 0.0), amp=n.get("amp", 0.4)))
            if n.get("gap", 0.0) > 0:
                parts.append(C.rest(n["gap"] * s))
        return parts
    return make


def register(key: str, genome: list[dict]) -> None:
    """Make a genome playable by name everywhere, like a core chirp (bodies call chirps.render(name))."""
    C.CHIRPS[key] = recipe(genome)


def direction(n: dict) -> int:
    r = math.log(n["f1"] / n["f0"])
    return 0 if abs(r) < math.log(1 + FLAT) else (1 if r > 0 else -1)


def signature(genome: list[dict]) -> tuple:
    total = sum(n["dur"] + n.get("gap", 0.0) for n in genome) or 1.0
    return len(genome), tuple(direction(n) for n in genome), tuple(n["dur"] / total for n in genome)


def distance(a: list[dict], b: list[dict]) -> float:
    """How different two chirps sound, by what people actually tell apart: note count, direction, rhythm."""
    (na, da, ra), (nb, db, rb) = signature(a), signature(b)
    d = abs(na - nb) + sum(x != y for x, y in zip(da, db))
    d += min(0.5, sum(abs(x - y) for x, y in zip(ra, rb)))   # rhythm counts a little, never enough on its own
    return d


def length(genome: list[dict]) -> float:
    return sum(n["dur"] + n.get("gap", 0.0) for n in genome)


def _clamp(genome: list[dict]) -> list[dict]:
    for n in genome:
        n["f0"] = min(HIGHEST, max(LOWEST, n["f0"]))
        n["f1"] = min(HIGHEST, max(LOWEST, n["f1"]))
        n["dur"] = max(SHORTEST_NOTE, n["dur"])
        n["amp"] = min(0.45, max(0.2, n.get("amp", 0.4)))     # never louder than the core set
    return genome


def _mutate(parent: list[dict], rng: random.Random, changes: int = 1) -> list[dict]:
    """One family child: same parent, a new shape, its own accent. More changes = further from the parent,
    used only when the close relatives are already taken."""
    g = [dict(n) for n in parent]
    for _ in range(changes):
        g = _change(g, rng)
    accent = rng.uniform(0.88, 1.15)      # the family accent: a touch higher or lower, a touch faster or slower
    for n in g:
        n["f0"] *= accent
        n["f1"] *= accent
        n["dur"] *= rng.uniform(0.85, 1.2)
        n["gap"] = n.get("gap", 0.0) * rng.uniform(0.85, 1.2)
        if n.get("wobble"):
            n["wobble"] *= rng.uniform(0.7, 1.4)
    return _clamp(g)


OPS = ("tail", "pickup", "stutter", "hold", "flip", "drop")
# tail     a little note at the end, up or down      (the only kind of change before Oct 27)
# pickup   a little note before the first one, like a breath in
# stutter  one note split in two with a tiny gap: "hel-lo" becomes "he-he-llo"
# hold     one note stops gliding and holds its pitch (flat), which no core chirp but tick does
# flip     one note turns around: up becomes down
# drop     one note goes (only for chirps with more than one)
# Oct 27: with only tail/drop/flip, 40 droids bred 2 different family hellos and 1 family curious,
# because the core set is crowded with 2-note shapes and "tail" almost always won. Families should
# sound different from each other, not just from their parent.


def _note(f0: float, f1: float, like: dict, dur: float, rng: random.Random) -> dict:
    return {"f0": f0, "f1": f1, "dur": dur, "gap": 0.0, "shape": like.get("shape", "sine"),
            "wobble": 0.0, "wobble_hz": 0.0, "amp": min(0.4, like.get("amp", 0.4))}


def _change(g: list[dict], rng: random.Random) -> list[dict]:
    g = [dict(n) for n in g]
    ops = [op for op in OPS if op != "drop" or len(g) > 1]
    op = rng.choice(ops)
    if op == "tail":
        last = g[-1]
        up = rng.random() < 0.5
        g[-1]["gap"] = max(last.get("gap", 0.0), 0.02)
        g.append(_note(last["f1"], last["f1"] * (rng.uniform(1.15, 1.45) if up else rng.uniform(0.7, 0.87)),
                       last, rng.uniform(0.05, 0.09), rng))
    elif op == "pickup":
        first = g[0]
        up = rng.random() < 0.5
        lead = _note(first["f0"] * (rng.uniform(0.7, 0.85) if up else rng.uniform(1.2, 1.4)), first["f0"],
                     first, rng.uniform(0.04, 0.07), rng)
        lead["gap"] = rng.uniform(0.015, 0.035)
        g.insert(0, lead)
    elif op == "stutter":
        i = rng.randrange(len(g))
        n = g[i]
        mid = math.sqrt(n["f0"] * n["f1"])           # halfway in pitch, so the glide keeps its direction
        a, b = dict(n), dict(n)
        a["f1"], a["dur"], a["gap"] = mid, n["dur"] * 0.5, rng.uniform(0.015, 0.03)
        b["f0"], b["dur"] = mid, n["dur"] * 0.5
        if direction(a) == 0 and direction(n) != 0:   # too small a glide to split: repeat the whole note instead
            a, b = dict(n), dict(n)
            a["dur"], a["gap"] = n["dur"] * 0.6, rng.uniform(0.015, 0.03)
            b["dur"] = n["dur"] * 0.6
        g[i:i + 1] = [a, b]
    elif op == "hold":
        i = rng.randrange(len(g))
        n = g[i]
        pitch = n["f1"] if rng.random() < 0.5 else n["f0"]
        n["f0"] = n["f1"] = pitch
    elif op == "drop":
        g.pop(rng.randrange(len(g)))
        g[-1]["gap"] = 0.0
    else:                                 # flip
        i = rng.randrange(len(g))
        n = g[i]
        if direction(n) == 0:
            n["f1"] = n["f0"] * rng.choice([1.35, 0.72])
        else:
            n["f0"], n["f1"] = n["f1"], n["f0"]
    return g


def breed(parent: list[dict], others: list[list[dict]], seed: str, tries: int = 200) -> list[dict]:
    """A new chirp related to `parent`, at least MIN_DIST from every chirp in `others` (which should
    include the parent and every core chirp). Same seed, same chirp."""
    rng = random.Random(seed)
    best, best_d = None, -1.0
    for i in range(tries):
        child = _mutate(parent, rng, changes=1 + 3 * i // tries)      # 1 change first, up to 3 if crowded
        if length(child) > LONGEST:
            continue
        d = min((distance(child, o) for o in others), default=99.0)
        if d >= MIN_DIST:
            return child
        if d > best_d:
            best, best_d = child, d
    if best is None:
        raise ValueError("couldn't breed a chirp short enough")
    return best      # the most distinct it found. Rare: only with a very crowded vocabulary


def check(genome, where: str) -> None:
    if not isinstance(genome, list) or not genome:
        raise ValueError(f"{where}: a chirp needs at least one note")
    for i, n in enumerate(genome):
        for key in ("f0", "f1", "dur"):
            if not isinstance(n.get(key), (int, float)) or n[key] <= 0:
                raise ValueError(f"{where}: note {i + 1} needs a positive number for {key!r}")
