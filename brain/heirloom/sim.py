"""The time skip (D46): a synthetic household lives with Heirloom for years, in seconds.

It drives the REAL brain with the REAL wear plug-ins. Only the household is synthetic.

THE RULE: no number without a source.
Every number that describes people lives in a household file (brain/sim/households/*.json) and
must be declared in that file's "provenance" as one of:

    data      measured in a cited study. "derivation" shows the arithmetic from the paper's numbers
    unknown   no study gives it. Written as {"range": [low, high]}, bounded by what IS known.
              A single run uses the middle. A sweep (--sweep) runs the whole range, and only
              results that hold across it may be claimed
    scenario  what the household IS (the mix of moments). A condition ("in a home where..."),
              never a claim about real homes

The loader refuses a household with an undeclared number, so nothing slips in as "assumed".

The cartridge it writes records the profile, seed and every value used (D46).
"""
from __future__ import annotations

import json
import math
import random
import shutil
import statistics
import tempfile
from datetime import date, timedelta
from pathlib import Path

from .brain import HeirloomBrain
from .cartridge import Cartridge, CartridgeError
from .events import Event

HOUSEHOLDS_DIR = Path(__file__).resolve().parents[1] / "sim" / "households"
HOUSEHOLD_KEYS = {"note", "label", "moments_per_day", "weekend", "novelty", "long_term", "mix", "provenance"}
KINDS = {"data", "unknown", "scenario"}

# Every number a household needs, as a path into the file.
PARAMS = ("moments_per_day", "weekend", "novelty.peak", "novelty.days",
          "long_term.floor", "long_term.from_day", "long_term.to_day")


def _get(raw: dict, path: str):
    node = raw
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def load_household(name: str, folder: Path = HOUSEHOLDS_DIR) -> dict:
    """Read a household and refuse it if any number lacks provenance."""
    path = folder / f"{name}.json"
    if not path.exists():
        known = sorted(p.stem for p in folder.glob("*.json"))
        raise ValueError(f"no household called {name!r}. Known: {known}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    unknown_keys = set(raw) - HOUSEHOLD_KEYS
    if unknown_keys:
        raise ValueError(f"{path.name}: unknown field(s) {sorted(unknown_keys)}. Allowed: {sorted(HOUSEHOLD_KEYS)}")
    prov = raw.get("provenance", {})
    for p in PARAMS:
        value = _get(raw, p)
        if value is None:
            raise ValueError(f"{path.name}: missing {p!r}")
        entry = prov.get(p)
        if not entry or entry.get("kind") not in KINDS or not entry.get("source"):
            raise ValueError(f"{path.name}: {p!r} has no provenance. Every number needs a kind "
                             f"({', '.join(sorted(KINDS))}) and a source")
        is_range = isinstance(value, dict) and "range" in value
        if entry["kind"] == "unknown" and not is_range:
            raise ValueError(f"{path.name}: {p!r} is unknown, so it must be a range, not a single number")
        if entry["kind"] == "data" and not entry.get("derivation"):
            raise ValueError(f"{path.name}: {p!r} is data and needs a derivation from the paper's numbers")
    if prov.get("mix", {}).get("kind") != "scenario":
        raise ValueError(f"{path.name}: the mix must be declared as a scenario in provenance")
    for i, m in enumerate(raw.get("mix", [])):
        if not m.get("events") or not isinstance(m.get("weight"), (int, float)):
            raise ValueError(f"{path.name} mix item {i + 1}: needs \"events\" (a list) and \"weight\" (a number)")
    return raw


def resolve(household: dict, rng: random.Random | None = None) -> dict[str, float]:
    """Concrete values for one run. Ranges: the middle, or a random draw when rng is given."""
    out = {}
    for p in PARAMS:
        v = _get(household, p)
        if isinstance(v, dict):
            lo, hi = v["range"]
            out[p] = rng.uniform(lo, hi) if rng else (lo + hi) / 2
        else:
            out[p] = float(v)
    return out


def _poisson(rng: random.Random, mean: float) -> int:
    limit, k, p = math.exp(-mean), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def activity(v: dict, day: int) -> float:
    """How busy a day is compared with a settled weekday (1.0)."""
    m = 1.0 + (v["novelty.peak"] - 1.0) * math.exp(-3.0 * day / v["novelty.days"])
    if day > v["long_term.from_day"]:
        span = max(1.0, v["long_term.to_day"] - v["long_term.from_day"])
        f = min(1.0, (day - v["long_term.from_day"]) / span)
        m *= 1.0 - (1.0 - v["long_term.floor"]) * f
    if day % 7 in (5, 6):
        m *= v["weekend"]
    return m


def _live_one_day(brain: HeirloomBrain, household: dict, v: dict, rng: random.Random, day: int) -> int:
    mix = household["mix"]
    n = _poisson(rng, v["moments_per_day"] * activity(v, day))
    for m in rng.choices(mix, weights=[m["weight"] for m in mix], k=n):
        for i, name in enumerate(m["events"]):
            if i:
                brain.pass_time(m.get("gap", 2))
            brain.handle(Event(name, source="sim"))
        brain.pass_time(rng.uniform(600, 7200))   # mechanics only: long enough for any sulk to end
    return n


def _replace(folder: Path) -> None:
    """Only ever deletes an old SIMULATED cartridge, never a lived one."""
    if not folder.exists():
        return
    try:
        cart = Cartridge.open(folder)
    except CartridgeError:
        raise CartridgeError(f"{folder} exists and isn't a cartridge. Not touching it") from None
    if any(l.source.get("type") != "simulated" for l in cart.layers):
        raise CartridgeError(f"{folder} holds lived wear. Not overwriting it")
    shutil.rmtree(folder)


def time_skip(profile: str, out: Path, years: int = 12, seed: int = 42, snapshots: dict | None = None,
              draw: random.Random | None = None, quiet: bool = False) -> dict[str, dict]:
    """Live `years` with a household and write a cartridge per snapshot."""
    household = load_household(profile)
    v = resolve(household, draw)
    rng = random.Random(seed)
    total_days = years * 365
    snapshots = snapshots or {"day1": 1, "month1": 30, "year1": 365, f"year{years}": total_days}
    start = date.today() - timedelta(days=total_days)

    work = Path(out) / f"{profile}_year{years}"
    for name in snapshots:
        _replace(Path(out) / f"{profile}_{name}")
    source = {"type": "simulated", "profile": profile, "seed": seed, "params": {k: round(x, 3) for k, x in v.items()}}
    cart = Cartridge.create(work, label=household.get("label", profile), source=source, on=start)

    brain = HeirloomBrain(play_sound=lambda name: None, cartridge=cart)
    results, day, moments = {}, 0, 0
    for name, until in sorted(snapshots.items(), key=lambda kv: kv[1]):
        with cart.batch():
            while day < until:
                brain.today = start + timedelta(days=day)
                moments += _live_one_day(brain, household, v, rng, day)
                day += 1
        results[name] = {"day": day, "moments": moments, "dials": dict(brain.character.dials),
                         "sulk_s": brain.character.sulk_seconds, "notice_m": brain.character.notice_distance}
        dest = Path(out) / f"{profile}_{name}"
        if dest != work:
            shutil.copytree(work, dest)
        if not quiet:
            print(f"  {name:7s} day {day:5d}  {moments:6d} moments   " +
                  "  ".join(f"{k} {x:.3f}" for k, x in brain.character.dials.items()))
    return results


def sweep(profile: str, runs: int = 30, years: int = 12, seed: int = 1) -> dict[str, dict[str, tuple]]:
    """Run the whole range of every unknown, with different random households each time.
    Returns, per snapshot and dial, (lowest, median, highest). Claim only what holds across it."""
    draw = random.Random(seed)
    collected: dict[str, dict[str, list]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(runs):
            r = time_skip(profile, Path(tmp) / str(i), years=years, seed=seed * 1000 + i, draw=draw, quiet=True)
            for snap, res in r.items():
                for k, x in {**res["dials"], "sulk_s": res["sulk_s"], "notice_m": res["notice_m"]}.items():
                    collected.setdefault(snap, {}).setdefault(k, []).append(x)
    return {snap: {k: (min(xs), statistics.median(xs), max(xs)) for k, xs in d.items()}
            for snap, d in collected.items()}
