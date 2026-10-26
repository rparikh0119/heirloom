"""Moments wear: the moment registry (proposed D99). The spine the other learning hangs off.

A moment is something that keeps happening at about the same time of day: the 9 am wave, the
3:30 kettle break, the good-night at 11. Once a moment exists it gets a stable id (L1.m01), and
later plug-ins hang things off that id: a chirp minted for it (dialect), how it moves through it
(habits), a ritual it belongs to (practice). So "Grandma's 3:30 kettle" is one thing with one
history, and you can always say whose layer it came from.

How a moment is found:
    Every event that isn't a reflex is noted with its time of day (minutes after midnight).
    When the same event happens within WINDOW minutes of the same time on MIN_DAYS different days,
    spread over at least MIN_SPAN_DAYS, it's a candidate. Two weeks of a habit, not one busy week.
    It only becomes a moment if it also stands out: since it started, random timing would almost
    never put that many in one slot (COINCIDENCE), and it happens on MIN_DAY_SHARE of those days.
    Waving at random all day is not a 9 am habit. Waving at random AND every morning at 9 is.
    The curious-then-good pair at 3:30 shows up as two moments. Grouping them into one ritual
    is the practice spine's job, later.

What it keeps (privacy):
    Only the event name and the minute it happened. No audio, no words, no who. Raw notes older
    than KEEP_DAYS are dropped. A moment itself is just: which event, what time, how often, since when.

Passing down:
    A previous owner's moments are never deleted, whatever their layer's weight. They sleep.
    If the new owner does the same thing at the same time, the old moment wakes up in the new
    owner's layer with its lineage ("from": "L1.m01"), so the droid can say it used to do this
    with the last keeper.

Clock: moments need the time of day. In real use that's the computer clock. Tests and the time
skip can set brain.now (a datetime). If the brain has a pretend date (brain.today) but no
brain.now, there's no real time of day, so it learns nothing rather than learning nonsense.

Page per layer (layers/L1/moments.json):
    {"seen": {"wave": {"2026-10-25": [545, 1210]}},
     "moments": {"L1.m01": {"cue": "wave", "at": 545, "spread": 12, "name": "wave around 9:05",
                            "first": "2026-10-04", "last": "2026-10-25", "days": 9,
                            "tag": null, "from": null}}}
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from .base import Wear

WINDOW = 45           # minutes either side of a moment's usual time that still count as it
MIN_DAYS = 5          # different days it has to happen on
MIN_SPAN_DAYS = 14    # and those days must spread over at least two weeks
COINCIDENCE = 1e-5    # and the odds that random timing would pile up that many in one slot must be
                      # under 1 in 10,000. Found by the time skip (Oct 25): looser rules let random
                      # events pile up over weeks until slots looked like habits (40 fake moments in
                      # a year at first, then about 1 fake per two years with a simple 3x rule).
                      # It's strict because it gets checked after every event, for years
AWAKE = 960           # a waking day is about 16 hours. Design value: if it has only ever seen you
                      # at 9 am, it still assumes you could have shown up any time you're awake
LOOK_BACK = 14        # compare against two weeks before the habit seems to start
MIN_DAY_SHARE = 0.3   # and it happens on at least this share of days since it started
KEEP_DAYS = 60        # raw notes older than this are dropped
DORMANT_DAYS = 30     # a moment not seen this long is asleep (kept, just not expected)
MAX_PER_DAY = 6       # notes per event per day, so a burst of waves doesn't flood the page
MAX_MOMENTS = 40      # per layer
HOLD = 90.0           # seconds brain.moment stays set after a moment happens
IGNORE = {"hearing", "listen", "unknown"}   # reflexes and "huh?" aren't moments
DAY = 1440


def _gap(a: float, b: float) -> float:
    """Minutes between two times of day, going round midnight the short way."""
    d = abs(a - b) % DAY
    return min(d, DAY - d)


def _mean_time(minutes: list[int]) -> float:
    """Average time of day on a clock face, so 23:50 and 00:10 average to midnight, not noon."""
    ang = [m / DAY * 2 * math.pi for m in minutes]
    x, y = sum(math.cos(a) for a in ang), sum(math.sin(a) for a in ang)
    return (math.atan2(y, x) / (2 * math.pi) * DAY) % DAY


def _odds(hits: int, total: int, share: float) -> float:
    """If `total` events landed at random times, how likely is it that `hits` or more fall in a slot
    that's `share` of the day? (A binomial tail.) Tiny = this slot really is a habit."""
    return sum(math.comb(total, k) * share ** k * (1 - share) ** (total - k) for k in range(hits, total + 1))


def _clock(m: float) -> str:
    m = int(round(m)) % DAY
    return f"{m // 60}:{m % 60:02d}"


class MomentsWear(Wear):
    name = "moments"

    def __init__(self) -> None:
        self.brain = None
        self.known: dict[str, dict] = {}        # every moment in every layer, with "layer" added
        self._holding: tuple[str, float] | None = None
        self.just_found: str | None = None      # id of a moment minted or woken by the last event

    # ---------- contract ----------
    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain
        brain.moment = None
        self._index()

    def record(self, event, mode: str, t: float) -> bool:
        self.just_found = None
        self._release(t)
        cue = event.name
        if cue in IGNORE:
            return False
        now = self._now()
        if now is None:
            return False
        day, minute = now.date(), now.hour * 60 + now.minute
        lid = self.cart.active.id
        page = self._page(lid)

        notes = page["seen"].setdefault(cue, {}).setdefault(day.isoformat(), [])
        if len(notes) < MAX_PER_DAY:
            notes.append(minute)          # kept even when it matches a moment, so comparisons stay fair
        self._prune(page, day)

        mid = self._match(page["moments"], cue, minute)
        if mid:
            self._saw(page["moments"][mid], day)
            self._hold(mid, t)
            self._write(lid, page)
            return False

        inherited = self._match_inherited(cue, minute)
        if inherited and len(page["moments"]) < MAX_MOMENTS:
            new_id = self._next_id(lid, page)
            old = self.known[inherited]
            page["moments"][new_id] = {"cue": cue, "at": old["at"], "spread": old["spread"],
                                       "name": old["name"], "first": day.isoformat(),
                                       "last": day.isoformat(), "days": 1, "tag": old.get("tag"),
                                       "from": inherited}
            print(f"[moments] {new_id} woke up: {old['name']} (from {inherited}, {self._keeper(old['layer'])})")
            return self._found(lid, page, new_id, t)

        new_id = self._try_mint(lid, page, cue, day)
        if new_id:
            m = page["moments"][new_id]
            print(f"[moments] new moment {new_id}: {m['name']} ({m['days']} days since {m['first']})")
            return self._found(lid, page, new_id, t)
        self._write(lid, page)
        return False

    def tick(self, brain) -> bool:
        self._release(brain.t)
        return False

    def apply(self, brain) -> None:
        self._index()
        today = self._today()
        brain.moments = {mid: {**m, "dormant": self._dormant(m, today)} for mid, m in self.known.items()}

    def validate(self, data: dict, where: str) -> None:
        if not data:
            return
        if set(data) - {"seen", "moments"}:
            raise ValueError(f"{where}: only \"seen\" and \"moments\" belong here, found {sorted(set(data))}")
        for mid, m in data.get("moments", {}).items():
            for key in ("cue", "at", "first", "last", "days"):
                if key not in m:
                    raise ValueError(f"{where}: moment {mid!r} is missing {key!r}")
            if not 0 <= m["at"] < DAY:
                raise ValueError(f"{where}: moment {mid!r} at {m['at']} is not a time of day (0 to 1439 minutes)")
        for cue, days in data.get("seen", {}).items():
            if not isinstance(days, dict):
                raise ValueError(f"{where}: seen[{cue!r}] should be {{day: [minutes]}}")

    def health(self) -> tuple[bool, str]:
        today = self._today()
        awake = sum(not self._dormant(m, today) for m in self.known.values())
        return True, f"{len(self.known)} moments ({awake} awake)"

    # ---------- for owners and other plug-ins ----------
    def tag(self, moment_id: str, name: str) -> None:
        """The owner names a moment ("when Dad gets home"). Owner-given, no recognition involved."""
        m = self.known.get(moment_id)
        if m is None:
            raise KeyError(f"no moment {moment_id!r}. Known: {sorted(self.known)}")
        page = self._page(m["layer"])
        page["moments"][moment_id]["tag"] = name
        self._write(m["layer"], page)
        self._index()

    def explain(self, moment_id: str) -> str:
        """One line for the overlay: what it is, since when, and whose it was."""
        m = self.known[moment_id]
        label = m.get("tag") or m["name"]
        line = f"{label}: seen on {m['days']} days since {m['first']} ({self._keeper(m['layer'])})"
        if m.get("from") and m["from"] in self.known:
            src = self.known[m["from"]]
            line += f". It used to do this with {self._keeper(src['layer'])}, since {src['first']}"
        if self._dormant(m, self._today()):
            line += ". Asleep: not seen lately"
        return line

    # ---------- internals ----------
    def _now(self) -> datetime | None:
        b = self.brain
        now = getattr(b, "now", None) if b is not None else None
        if now is not None:
            return now
        if b is not None and b.today is not None:
            return None                       # a pretend date with no clock: no real time of day
        return datetime.now()

    def _today(self) -> date:
        now = self._now()
        if now is not None:
            return now.date()
        return (self.brain.today if self.brain is not None and self.brain.today else None) or date.today()

    def _page(self, lid: str) -> dict:
        page = self.cart.read_page(lid, self.name)
        page.setdefault("seen", {})
        page.setdefault("moments", {})
        return page

    def _write(self, lid: str, page: dict) -> None:
        self.cart.write_page(lid, self.name, page)

    def _index(self) -> None:
        self.known = {}
        for layer in self.cart.layers:
            for mid, m in self._page(layer.id)["moments"].items():
                self.known[mid] = {**m, "layer": layer.id}

    def _match(self, moments: dict, cue: str, minute: int) -> str | None:
        hits = [(abs(_gap(m["at"], minute)), mid) for mid, m in moments.items()
                if m["cue"] == cue and _gap(m["at"], minute) <= WINDOW]
        return min(hits)[1] if hits else None

    def _match_inherited(self, cue: str, minute: int) -> str | None:
        active = self.cart.active.id
        woken = {m.get("from") for m in self._page(active)["moments"].values()}
        older = {mid: m for mid, m in self.known.items() if m["layer"] != active and mid not in woken}
        return self._match(older, cue, minute)

    def _saw(self, m: dict, day: date) -> None:
        if m["last"] != day.isoformat():
            m["days"] += 1
            m["last"] = day.isoformat()

    def _try_mint(self, lid: str, page: dict, cue: str, today: date) -> str | None:
        if len(page["moments"]) >= MAX_MOMENTS:
            return None
        notes = [(date.fromisoformat(d), m) for d, ms in page["seen"].get(cue, {}).items() for m in ms]
        taken = [m["at"] for m in page["moments"].values() if m["cue"] == cue]
        free = [(d, m) for d, m in notes if all(_gap(m, a) > WINDOW for a in taken)]
        best = None
        for _, centre in free:
            near = [(d, m) for d, m in free if _gap(m, centre) <= WINDOW]
            days = sorted({d for d, _ in near})
            if len(days) < MIN_DAYS or (days[-1] - days[0]).days < MIN_SPAN_DAYS:
                continue
            since = days[0] - timedelta(days=LOOK_BACK)    # a little before it started, so a lucky start can't be cherry-picked
            lived = (today - days[0]).days + 1
            others = sum(1 for d, m in free if d >= since and _gap(m, centre) > WINDOW)   # habits it already knows aren't random, so they don't count
            covered = max(AWAKE, self._covered(notes, since))        # minutes of the day it could happen in
            slot = min(1.0, 2 * WINDOW / covered)                     # share of that day one slot is
            if len(days) / lived < MIN_DAY_SHARE or _odds(len(near), len(near) + others, slot) > COINCIDENCE:
                continue
            if best is None or len(days) > len(best[1]):
                best = (near, days)
        if best is None:
            return None
        near, days = best
        minutes = [m for _, m in near]
        at = _mean_time(minutes)
        spread = math.sqrt(sum(_gap(m, at) ** 2 for m in minutes) / len(minutes))
        new_id = self._next_id(lid, page)
        page["moments"][new_id] = {"cue": cue, "at": round(at), "spread": round(spread),
                                   "name": f"{cue.replace('_', ' ')} around {_clock(at)}",
                                   "first": days[0].isoformat(), "last": days[-1].isoformat(),
                                   "days": len(days), "tag": None, "from": None}
        return new_id

    @staticmethod
    def _covered(notes: list, since: date) -> float:
        """Roughly how much of the day this event happens in. The widest gap around the clock is
        the part of the day it never happens (when you're asleep)."""
        ms = sorted({m for d, m in notes if d >= since})
        if len(ms) < 2:
            return 0.0
        gaps = [b - a for a, b in zip(ms, ms[1:])] + [ms[0] + DAY - ms[-1]]
        return DAY - max(gaps)

    def _prune(self, page: dict, today: date) -> None:
        cutoff = (today - timedelta(days=KEEP_DAYS)).isoformat()
        for cue in list(page["seen"]):
            page["seen"][cue] = {d: ms for d, ms in page["seen"][cue].items() if d >= cutoff}
            if not page["seen"][cue]:
                del page["seen"][cue]

    def _next_id(self, lid: str, page: dict) -> str:
        n = max([int(mid.split(".m")[1]) for mid in page["moments"]] + [0]) + 1
        return f"{lid}.m{n:02d}"

    def _found(self, lid: str, page: dict, mid: str, t: float) -> bool:
        self._write(lid, page)
        self._index()
        self._hold(mid, t)
        self.just_found = mid
        return True

    def _hold(self, mid: str, t: float) -> None:
        self._holding = (mid, t + HOLD)
        if self.brain is not None:
            self.brain.moment = mid

    def _release(self, t: float) -> None:
        if self._holding and t > self._holding[1]:
            self._holding = None
            if self.brain is not None:
                self.brain.moment = None

    def _dormant(self, m: dict, today: date) -> bool:
        return (today - date.fromisoformat(m["last"])).days > DORMANT_DAYS

    def _keeper(self, lid: str) -> str:
        try:
            return f"keeper {lid}, \"{self.cart.layer(lid).label}\""
        except Exception:  # noqa: BLE001
            return f"keeper {lid}"
