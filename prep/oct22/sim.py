"""The time skip (D46): a synthetic household lives with Heirloom for years, in seconds.

It drives the REAL brain with the REAL wear plug-ins. Nothing is faked except the household:
events come from a profile in brain/sim/households/*.json instead of a person, and time between
moments passes with nobody watching (brain.pass_time).

    {
      "label": "a family",
      "sources": ["Bentley et al. 2018: medium users about 2.4 sessions a day"],
      "moments_per_day": 2.4,                       how many moments on a settled weekday
      "weekend": 1.4,                               busier on weekends
      "novelty": {"peak": 3, "days": 21},           extra busy at first, fading over 3 weeks
      "long_term": {"floor": 0.5, "from_day": 365, "to_day": 1095},   quieter after year 1
      "mix": [                                      WHAT the moments are (a design assumption)
        {"events": ["wave"], "weight": 6},
        {"events": ["offended", "heart"], "gap": 3, "weight": 0.25}    a little scene, 3 s apart
      ]
    }

The totals and the curve over time come from research (see each file's "sources"). The mix of
moments is a design assumption and is labelled as one (D46).

The cartridge it writes says it's simulated, with the profile and seed (D46).
Same profile + same seed = the same droid every time.
"""
from __future__ import annotations

import json
import math
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

from .brain import HeirloomBrain
from .cartridge import Cartridge, CartridgeError
from .events import Event

HOUSEHOLDS_DIR = Path(__file__).resolve().parents[1] / "sim" / "households"
HOUSEHOLD_KEYS = {"note", "label", "sources", "moments_per_day", "weekend", "novelty", "long_term", "mix"}


def load_household(name: str, folder: Path = HOUSEHOLDS_DIR) -> dict:
    path = folder / f"{name}.json"
    if not path.exists():
        known = sorted(p.stem for p in folder.glob("*.json"))
        raise ValueError(f"no household called {name!r}. Known: {known}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(raw) - HOUSEHOLD_KEYS
    if unknown:
        raise ValueError(f"{path.name}: unknown field(s) {sorted(unknown)}. Allowed: {sorted(HOUSEHOLD_KEYS)}")
    if not isinstance(raw.get("moments_per_day"), (int, float)):
        raise ValueError(f"{path.name}: needs \"moments_per_day\" (a number)")
    for i, m in enumerate(raw.get("mix", [])):
        if not m.get("events") or not isinstance(m.get("weight"), (int, float)):
            raise ValueError(f"{path.name} mix item {i + 1}: needs \"events\" (a list) and \"weight\" (a number)")
    return raw


def _poisson(rng: random.Random, mean: float) -> int:
    """How many times something that happens `mean` times a day happens today."""
    limit, k, p = math.exp(-mean), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def activity(household: dict, day: int) -> float:
    """How busy today is compared with a settled weekday (1.0).

    novelty    starts at `peak` and fades to 1 over about `days` (Cagiltay 2022, Weiss 2021: 2 to 3 weeks)
    long_term  slides from 1 to `floor` between `from_day` and `to_day` (assumption, Luka recall, R10)
    weekend    multiplier on days 5 and 6 of each week (Bentley 2018: more use on weekends)
    """
    m = 1.0
    nov = household.get("novelty")
    if nov:
        m *= 1.0 + (nov["peak"] - 1.0) * math.exp(-3.0 * day / nov["days"])
    lt = household.get("long_term")
    if lt and day > lt["from_day"]:
        f = min(1.0, (day - lt["from_day"]) / max(1, lt["to_day"] - lt["from_day"]))
        m *= 1.0 - (1.0 - lt["floor"]) * f
    if day % 7 in (5, 6):
        m *= household.get("weekend", 1.0)
    return m


def _live_one_day(brain: HeirloomBrain, household: dict, rng: random.Random, day: int) -> int:
    mix = household["mix"]
    n = _poisson(rng, household["moments_per_day"] * activity(household, day))
    today = rng.choices(mix, weights=[m["weight"] for m in mix], k=n)
    for m in today:
        for i, name in enumerate(m["events"]):
            if i:
                brain.pass_time(m.get("gap", 2))
            brain.handle(Event(name, source="sim"))
        brain.pass_time(rng.uniform(600, 7200))        # ten minutes to two hours until the next moment
    return len(today)


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


def time_skip(profile: str, out: Path, years: int = 12, seed: int = 42,
              snapshots: dict[str, int] | None = None, quiet: bool = False) -> dict[str, dict]:
    """Live `years` with a household. Writes a cartridge folder per snapshot, e.g.
    out/loud_family_day1, out/loud_family_year1, out/loud_family_year12.
    Returns the dials at each snapshot."""
    household = load_household(profile)
    rng = random.Random(seed)
    total_days = years * 365
    snapshots = snapshots or {"day1": 1, "month1": 30, "year1": 365, f"year{years}": total_days}
    start = date.today() - timedelta(days=total_days)

    work = Path(out) / f"{profile}_year{years}"
    for name in snapshots:
        _replace(Path(out) / f"{profile}_{name}")
    source = {"type": "simulated", "profile": profile, "seed": seed}
    cart = Cartridge.create(work, label=household.get("label", profile), source=source, on=start)

    brain = HeirloomBrain(play_sound=lambda name: None, cartridge=cart)
    results, day, moments = {}, 0, 0
    for name, until in sorted(snapshots.items(), key=lambda kv: kv[1]):
        with cart.batch():
            while day < until:
                brain.today = start + timedelta(days=day)
                moments += _live_one_day(brain, household, rng, day)
                day += 1
        dials = dict(brain.character.dials)
        results[name] = {"day": day, "moments": moments, "dials": dials,
                         "sulk_s": brain.character.sulk_seconds, "notice_m": brain.character.notice_distance}
        dest = Path(out) / f"{profile}_{name}"
        if dest != work:
            shutil.copytree(work, dest)
        if not quiet:
            print(f"  {name:7s} day {day:5d}  {moments:6d} moments   " +
                  "  ".join(f"{k} {v:.3f}" for k, v in dials.items()))
    return results
