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

A household can also have a "routine" (also a scenario): when it's awake, and things it does at
set times ("wave at 10:00 on weekdays, 80% of days"). With a routine, every moment gets a time of
day, so the moments wear can notice habits. Without one there's no clock and it learns no moments.

A household can also have a "taste" and a "keeper" (both scenarios), for the learning loop (D104 to D106):
    taste    which authored move it warms to for each cue ({"wave": "happy"}), how often it praises a
             move it likes ("praise") or says no to one it doesn't ("says_no"), and whether it warms to
             higher or lower family chirps ("chirp"). It reacts to what the droid actually CHOSE, so the
             real learner and drift run. These reactions are extra events on top of the mix
    keeper   how the keeper moves (habits wear's seven numbers) and a day-to-day "spread". Years of hand
             frames can't be simulated, so each active day hands the keeper style (with noise) straight
             to the habits learning rule. Only days with at least KEEPER_MIN moments count
With either one, the brain runs with learning on. Without, it's exactly as before.

The cartridge it writes records the profile, seed and every value used (D46).
"""
from __future__ import annotations

import json
import math
import random
import shutil
import statistics
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from .brain import HeirloomBrain
from .cartridge import Cartridge, CartridgeError
from .events import Event

HOUSEHOLDS_DIR = Path(__file__).resolve().parents[1] / "sim" / "households"
HOUSEHOLD_KEYS = {"note", "label", "moments_per_day", "weekend", "novelty", "long_term", "mix", "routine",
                  "taste", "keeper", "provenance"}
TASTE_KEYS = {"note", "favourite", "praise", "says_no", "chirp"}
KEEPER_KEYS = {"note", "style", "spread"}
KEEPER_MIN = 3        # moments in a day for it to count as a day of seeing the keeper move (habits needs enough gestures)
ROUTINE_ITEM_KEYS = {"note", "events", "at", "jitter", "chance", "days", "gap"}
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
    if "routine" in raw:
        _check_routine(raw["routine"], prov, path.name)
    if "taste" in raw:
        _check_taste(raw["taste"], prov, path.name)
    if "keeper" in raw:
        _check_keeper(raw["keeper"], prov, path.name)
    return raw


def _check_taste(taste: dict, prov: dict, name: str) -> None:
    if prov.get("taste", {}).get("kind") != "scenario":
        raise ValueError(f"{name}: the taste must be declared as a scenario in provenance")
    bad = set(taste) - TASTE_KEYS
    if bad:
        raise ValueError(f"{name} taste: unknown field(s) {sorted(bad)}. Allowed: {sorted(TASTE_KEYS)}")
    from .reactions import load_reactions
    choices = {w: [r.motion] + r.choices for r in load_reactions() if r.choices for w in r.when}
    for cue, move in taste.get("favourite", {}).items():
        if cue not in choices:
            raise ValueError(f"{name} taste: {cue!r} doesn't learn. Learnable: {sorted(choices)}")
        if move not in choices[cue]:
            raise ValueError(f"{name} taste: {move!r} isn't a choice for {cue}. Choices: {choices[cue]}")
    for k in ("praise", "says_no"):
        if not 0 <= taste.get(k, -1) <= 1:
            raise ValueError(f"{name} taste: needs {k!r} from 0 to 1")
    if taste.get("chirp", "none") not in ("higher", "lower", "none"):
        raise ValueError(f"{name} taste: \"chirp\" is higher, lower or none")


def _check_keeper(keeper: dict, prov: dict, name: str) -> None:
    from .wear.habits import FEATURES
    if prov.get("keeper", {}).get("kind") != "scenario":
        raise ValueError(f"{name}: the keeper must be declared as a scenario in provenance")
    bad = set(keeper) - KEEPER_KEYS
    if bad:
        raise ValueError(f"{name} keeper: unknown field(s) {sorted(bad)}. Allowed: {sorted(KEEPER_KEYS)}")
    extra = set(keeper.get("style", {})) - set(FEATURES)
    if extra or not keeper.get("style"):
        raise ValueError(f"{name} keeper: \"style\" takes the habits numbers {list(FEATURES)}"
                         + (f", found {sorted(extra)}" if extra else ""))
    if not 0 <= keeper.get("spread", -1) <= 0.5:
        raise ValueError(f"{name} keeper: needs \"spread\" from 0 to 0.5 (day-to-day variation, as a share)")


def _react(brain: HeirloomBrain, household: dict, rng: random.Random) -> None:
    """The household reacts to what the droid just chose (taste). Never to its own reaction."""
    taste = household.get("taste")
    o = brain.rewards.open
    if not taste or brain.learner is None or o is None or o.t != brain.t:
        return
    d = brain._decided.get(o.decision_id) or {}
    arm = d.get("arm")
    cue = d["bucket"].split("|")[0] if d.get("bucket") else None
    liked_move = arm is not None and taste.get("favourite", {}).get(cue) == arm
    chirp = d.get("chirp")
    pref = taste.get("chirp", "none")
    liked_chirp = chirp is not None and pref != "none" and ((chirp[1]["pitch"] > 1.0) == (pref == "higher"))
    parts = [liked_move] if arm is not None else []          # a home warms to the whole answer: each part it
    if chirp is not None and pref != "none":                  # likes (the move, the chirp) adds to the chance
        parts.append(liked_chirp)
    if parts and any(parts) and rng.random() < taste["praise"] * sum(parts) / len(parts):
        brain.pass_time(1.5)
        brain.handle(Event("good", source="sim"))
    elif arm is not None and not liked_move and cue in taste.get("favourite", {}) and rng.random() < taste["says_no"]:
        brain.pass_time(1.5)
        brain.handle(Event("scold", source="sim"))


def _keeper_day(brain: HeirloomBrain, household: dict, rng: random.Random, moments: int) -> None:
    keeper = household.get("keeper")
    habits = next((w for w in brain.wear if w.name == "habits"), None)
    if not keeper or habits is None or moments < KEEPER_MIN:
        return
    spread = keeper["spread"]
    habits.learn_day({k: v * (1 + rng.gauss(0, spread)) if k != "tilt" else v + rng.gauss(0, 2.0)
                      for k, v in keeper["style"].items()})


def _minute(text: str, where: str) -> int:
    """'09:30' -> 570 minutes after midnight."""
    try:
        hh, mm = text.split(":")
        m = int(hh) * 60 + int(mm)
    except (ValueError, AttributeError):
        raise ValueError(f"{where}: {text!r} should be a time like \"09:30\"") from None
    if not 0 <= m < 1440:
        raise ValueError(f"{where}: {text!r} is not a time of day")
    return m


def _check_routine(routine: dict, prov: dict, name: str) -> None:
    """A routine gives the household a clock: when it's awake and what it does at set times.
    It's what the household IS, so it must be declared as a scenario, like the mix."""
    if prov.get("routine", {}).get("kind") != "scenario":
        raise ValueError(f"{name}: the routine must be declared as a scenario in provenance")
    awake = routine.get("awake")
    if not isinstance(awake, list) or len(awake) != 2:
        raise ValueError(f"{name} routine: needs \"awake\": [\"08:30\", \"23:30\"] (when untimed moments can happen)")
    a, b = (_minute(t, f"{name} routine awake") for t in awake)
    if b <= a:
        raise ValueError(f"{name} routine: awake must start before it ends, on the same day")
    for i, item in enumerate(routine.get("items", [])):
        where = f"{name} routine item {i + 1}"
        unknown = set(item) - ROUTINE_ITEM_KEYS
        if unknown:
            raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}. Allowed: {sorted(ROUTINE_ITEM_KEYS)}")
        if not item.get("events"):
            raise ValueError(f"{where}: needs \"events\" (a list)")
        _minute(item.get("at"), where)
        if not 0 <= item.get("chance", -1) <= 1:
            raise ValueError(f"{where}: needs \"chance\" from 0 to 1 (how many days it happens)")
        if not isinstance(item.get("jitter", 0), (int, float)):
            raise ValueError(f"{where}: \"jitter\" is minutes, a number")
        if item.get("days", "all") not in ("all", "weekdays", "weekends"):
            raise ValueError(f"{where}: \"days\" is all, weekdays or weekends")


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
    if "routine" in household:
        return _live_one_timed_day(brain, household, v, rng, day)
    mix = household["mix"]
    n = _poisson(rng, v["moments_per_day"] * activity(v, day))
    for m in rng.choices(mix, weights=[m["weight"] for m in mix], k=n):
        for i, name in enumerate(m["events"]):
            if i:
                brain.pass_time(m.get("gap", 2))
            brain.handle(Event(name, source="sim"))
            _react(brain, household, rng)
        brain.pass_time(rng.uniform(600, 7200))   # mechanics only: long enough for any sulk to end
    _keeper_day(brain, household, rng, n)
    return n


def _live_one_timed_day(brain: HeirloomBrain, household: dict, v: dict, rng: random.Random, day: int) -> int:
    """Same day as above, but every moment has a time of day, so the moments wear can learn habits.
    Untimed moments (the mix) land anywhere while it's awake. Routine items land near their time."""
    routine, mix = household["routine"], household["mix"]
    wake, sleep = (_minute(t, "awake") for t in routine["awake"])
    busy = activity(v, day)
    weekend = day % 7 in (5, 6)
    plan = []
    for m in rng.choices(mix, weights=[m["weight"] for m in mix], k=_poisson(rng, v["moments_per_day"] * busy)):
        plan.append((rng.uniform(wake, sleep), m))
    for item in routine.get("items", []):
        when = item.get("days", "all")
        if (when == "weekdays" and weekend) or (when == "weekends" and not weekend):
            continue
        if rng.random() < item["chance"] * min(1.0, busy):
            at = _minute(item["at"], "routine") + rng.gauss(0, item.get("jitter", 0))
            plan.append((max(0.0, min(1439.0, at)), item))
    midnight = datetime.combine(brain.today, datetime.min.time())
    last = None
    for minute, m in sorted(plan, key=lambda pm: pm[0]):
        now = midnight + timedelta(minutes=minute)
        if last is not None:
            brain.pass_time(max(60.0, (now - last).total_seconds()))
        for i, name in enumerate(m["events"]):
            if i:
                brain.pass_time(m.get("gap", 2))
            brain.now = now + timedelta(seconds=m.get("gap", 2) * i)
            brain.handle(Event(name, source="sim"))
            _react(brain, household, rng)
        last = now
    brain.pass_time(3600)
    _keeper_day(brain, household, rng, len(plan))
    return len(plan)


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


def _ends_today(folder: Path, sim_day: date) -> None:
    """A snapshot is meant to be put on the desk right after its last simulated day, so shift the
    patina dates to end today. Otherwise a year-1 snapshot reads as 11 years on a shelf and rusts.
    The gap a shelved droid really had is kept, because every date moves by the same amount."""
    shift = date.today() - sim_day
    cart = Cartridge.open(folder)
    for layer in cart.layers:
        page = cart.read_page(layer.id, "patina")
        for rec in page.values():
            if "last" in rec:
                rec["last"] = (date.fromisoformat(rec["last"]) + shift).isoformat()
        if page:
            cart.write_page(layer.id, "patina", page)
        moments = cart.read_page(layer.id, "moments")
        if moments:
            move = lambda d: (date.fromisoformat(d) + shift).isoformat()
            for m in moments.get("moments", {}).values():
                m["first"], m["last"] = move(m["first"]), move(m["last"])
            moments["seen"] = {cue: {move(d): ms for d, ms in days.items()}
                               for cue, days in moments.get("seen", {}).items()}
            cart.write_page(layer.id, "moments", moments)
        habits = cart.read_page(layer.id, "habits")
        if habits.get("last"):
            habits["last"] = (date.fromisoformat(habits["last"]) + shift).isoformat()
            cart.write_page(layer.id, "habits", habits)


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

    learn = "taste" in household or "keeper" in household
    brain = HeirloomBrain(play_sound=lambda name: None, cartridge=cart, learn=learn)
    if learn:
        from .learning import DecisionLog
        brain.decisions = DecisionLog(None)              # years of decisions: no log file, no odds
        brain.estimate_odds = False
    results, day, moments = {}, 0, 0
    for name, until in sorted(snapshots.items(), key=lambda kv: kv[1]):
        with cart.batch():
            while day < until:
                brain.today = start + timedelta(days=day)
                moments += _live_one_day(brain, household, v, rng, day)
                day += 1
        pat = next((w for w in brain.wear if w.name == "patina"), None)
        results[name] = {"day": day, "moments": moments, "dials": dict(brain.character.dials),
                         "sulk_s": brain.character.sulk_seconds, "notice_m": brain.character.notice_distance,
                         "notice_back_m": brain.character.notice_distance_when_shy(pat.rust_on(brain.today + timedelta(days=1)) if pat else 0.0),
                         "moves": dict(pat.settle) if pat else {}, "deep": dict(pat.depth) if pat else {},
                         "rust": pat.rust_on(brain.today + timedelta(days=1)) if pat else 0.0,
                         "uses": pat.uses(brain.today) if pat else {},
                         "found": {mid: m["name"] for mid, m in cart.read_page(cart.active.id, "moments").get("moments", {}).items()}}
        dest = Path(out) / f"{profile}_{name}"
        if dest != work:
            shutil.copytree(work, dest)
            _ends_today(dest, start + timedelta(days=day - 1))
        if not quiet:
            print(f"  {name:7s} day {day:5d}  {moments:6d} moments   " +
                  "  ".join(f"{k} {x:.3f}" for k, x in brain.character.dials.items()))
            if results[name]["found"]:
                print(f"  {'':7s} habits it noticed: " + ", ".join(results[name]["found"].values()))
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
                moves = {f"worn_{m}": res["moves"].get(m, 0.0) for m in ("hello", "happy", "offended")}
                moves |= {f"deep_{m}": res["deep"].get(m, 0.0) for m in ("hello", "happy", "offended")}
                moves["rust"] = res["rust"]
                for k, x in {**res["dials"], "sulk_s": res["sulk_s"], "notice_m": res["notice_m"], **moves}.items():
                    collected.setdefault(snap, {}).setdefault(k, []).append(x)
    return {snap: {k: (min(xs), statistics.median(xs), max(xs)) for k, xs in d.items()}
            for snap, d in collected.items()}
