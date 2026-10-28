"""Habits wear: it picks up its keeper's way of moving (spine 2, proposed D90 to D93).

Never live mimicry. A robot that copies you within seconds feels like a trick (Jonell et al. 2021).
Instead it watches how you move while you're together, keeps only running numbers in memory, and
when you say good night it "dreams": the day becomes seven numbers, the raw motion is thrown away,
and your numbers move a small step toward today's. Over weeks, every move it plays takes on a
little of how you move. Seven numbers per keeper, nothing else on disk (D90).

    tempo        how fast your gestures peak (wrist speed, m/s)         -> its moves play quicker or slower
    amplitude    how far your hand travels in a gesture (m)             -> bigger or smaller moves
    smoothness   1 = speed rises and falls once, lower = it surges and dips -> eased or stiff
                 (the noisiest number: Quest tracking jitter looks like jerkiness. Smoothed over
                 3 frames. Check against real hands before trusting it)
    directness   straight to the point (1) or wandering on the way     -> a beat of hesitation, or none
    settle       seconds from a gesture's peak until your hand is still -> slower or quicker finish
    stillness    share of the time you're not moving at all             -> it glances around less or more
    tilt         your usual head roll when still (degrees, if Unity sends "roll")   -> a resting head tilt

What it reads: wrists from hand tracking and head position (+ head roll when sent). Head and hands
are what Quest tracks reliably with passthrough on (Meta body tracking drops to low fidelity). No
face, no voice, no emotion.

Learning (design numbers, not research):
    a day counts if it saw at least MIN_GESTURES gestures. Thin days are skipped
    your numbers move ALPHA (1/30) of the way to today's: half-life about three weeks
    a new keeper's influence ramps from 0 to full over RAMP_DAYS (35) counted days, so a new keeper
    first meets the character the droid already had
    total influence capped at CAP (30%) of each setting, so the droid stays itself (D92)

Passing down: the old keeper's numbers freeze with the layer. Their influence fades over FADE_DAYS
to a FLOOR of 0.25, never zero (D93): it still moves a little like the last keeper.
Strength: each layer's page has "strength" (1 = normal, 0 = off), for owners who don't want it.

Page per layer (layers/L1/habits.json):
    {"schema": "heirloom.wear.habits/1", "style": {"tempo": 0.92, ...}, "days": 12,
     "last": "2026-10-27", "strength": 1.0}
"""
from __future__ import annotations

import statistics
from datetime import date, datetime

import numpy as np

from .base import Wear

SCHEMA = "heirloom.wear.habits/1"
FEATURES = ("tempo", "amplitude", "smoothness", "directness", "settle", "stillness", "tilt")

# What counts as moving (design values, tune with real hands)
MOVE = 0.25           # m/s: a wrist faster than this is in a gesture
STILL = 0.06          # m/s: slower than this is still
MIN_TRAVEL = 0.03     # m: smaller than this isn't a gesture (tracking jitter)
MAX_GESTURE_S = 4.0   # longer than this is not one gesture
JUMP = 4.0            # m/s: faster than this is tracking losing and finding the hand, not a gesture
SMOOTH = 0.35         # wrist position smoothing per frame (0..1, lower = smoother). Tracking jitter of a few mm
                      # at 30 Hz otherwise reads as motion: without it, 2 mm of jitter made a calm keeper
                      # look busy, jerky and wandering (Oct 27 test). Jitter size on Quest is unmeasured
MIN_GESTURES = 15     # a day needs at least this many to count

ALPHA = 1 / 30        # step toward today's numbers
RAMP_DAYS = 35        # a new keeper's influence ramps over this many counted days
FADE_DAYS = 180       # an old keeper's influence fades over this long after the handoff...
FLOOR = 0.25          # ...but never below this
CAP = 0.30            # most any setting can move from habits

# "Typical" person at a desk and how far from it counts as a full step. GUESSES to tune with real
# people, not data: no study gives desk-gesture norms on Quest hand tracking (as far as we found).
TYPICAL = {"tempo": (0.8, 0.5), "amplitude": (0.15, 0.10), "smoothness": (0.85, 0.15),
           "directness": (0.75, 0.2), "settle": (0.5, 0.4), "stillness": (0.7, 0.25), "tilt": (0.0, 10.0)}
# How much each number is allowed to change motion, until checked against real hands (Oct 27 synthetic test):
# with 30 Hz hand data and the jitter smoothing it needs, tempo, amplitude, stillness and tilt separate an
# energetic keeper from a calm one even at 2 mm of tracking jitter. Directness only weakly. Smoothness and
# settle don't survive the smoothing. They're still recorded, so trusting them later loses no history.
TRUST = {"tempo": 1.0, "amplitude": 1.0, "stillness": 1.0, "tilt": 1.0, "directness": 0.5,
         "smoothness": 0.0, "settle": 0.0}
WORDS = {"tempo": ("quicker", "slower"), "amplitude": ("bigger", "smaller"), "smoothness": ("smoother", "stiffer"),
         "directness": ("surer", "more hesitant"), "settle": ("slower to settle", "quicker to settle"),
         "stillness": ("calmer", "busier"), "tilt": ("tilts right", "tilts left")}


class _Gesture:
    """One gesture in progress, one hand. Lives in memory only."""
    def __init__(self, p, t) -> None:
        self.start, self.last = p, p
        self.t0, self.t_peak, self.peak = t, t, 0.0
        self.path = 0.0
        self.reach = 0.0
        self.speeds: list[float] = []
        self.done_at = None

    def add(self, p, v, t) -> None:
        self.path += float(np.linalg.norm(p - self.last))
        self.last = p
        self.reach = max(self.reach, float(np.linalg.norm(p - self.start)))
        self.speeds.append(v)
        if v > self.peak:
            self.peak, self.t_peak = v, t

    def summary(self, t_still: float) -> dict | None:
        if self.reach < MIN_TRAVEL or t_still - self.t0 > MAX_GESTURE_S or len(self.speeds) < 3:
            return None
        raw = self.speeds
        s = [sum(raw[max(0, i - 1):i + 2]) / len(raw[max(0, i - 1):i + 2]) for i in range(len(raw))]   # 3-frame average: tracking jitter isn't jerkiness
        updown = sum(abs(b - a) for a, b in zip(s, s[1:])) + s[0] + s[-1]
        smooth = min(1.0, 2 * max(s) / updown) if updown > 1e-9 else 1.0   # 1 = one clean rise and fall
        return {"tempo": self.peak, "amplitude": self.reach, "smoothness": smooth,
                "directness": float(np.linalg.norm(self.last - self.start)) / self.path if self.path > 1e-6 else 1.0,
                "settle": t_still - self.t_peak}


class HabitsWear(Wear):
    name = "habits"

    def __init__(self) -> None:
        self.brain = None
        self.on = False                    # watching only with the learning loop on (run.py --learn)
        self._reset_day()
        self.offsets: dict[str, float] = {f: 0.0 for f in FEATURES}   # -1..1 per feature, already capped
        self.mix: list[tuple[str, float]] = []                        # (layer, weight) for the overlay

    def _reset_day(self) -> None:
        self._prev: dict[str, tuple] = {}             # side -> (smoothed position, t, raw position)
        self._open: dict[str, _Gesture] = {}
        self._gestures: list[dict] = []               # today's gesture summaries (numbers only)
        self._frames = 0
        self._still_frames = 0
        self._rolls: list[float] = []
        self._day: date | None = None

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain

    # ---------- watching (memory only) ----------
    def observe(self, t: float, hands: dict | None, head=None, roll: float | None = None) -> None:
        """One new hands message (and the head). Nothing here is ever written to disk."""
        if not self.on or hands is None:
            return
        self._day = self._day or self._today()
        any_moving = False
        for side in ("left", "right"):
            arr = hands.get(side) if hands.get(f"{side}_tracked") else None
            if not arr or len(arr) != 78:
                self._prev.pop(side, None)
                self._open.pop(side, None)
                continue
            raw = np.asarray(arr[:3], dtype=float)        # joint 0 = wrist
            if side in self._prev:
                p0, t0, raw0 = self._prev[side]
                dt = t - t0
                if dt <= 0:
                    continue
                if float(np.linalg.norm(raw - raw0)) / dt > JUMP:  # the hand jumped: start over from here
                    self._prev[side] = (raw, t, raw)
                    self._open.pop(side, None)
                    continue
                p = p0 + SMOOTH * (raw - p0)               # smoothed, so jitter isn't motion
                v = float(np.linalg.norm(p - p0)) / dt
                any_moving |= v >= STILL
                g = self._open.get(side)
                if g is None and v > MOVE:
                    g = self._open[side] = _Gesture(p0, t0)
                if g is not None:
                    g.add(p, v, t)
                    if v < STILL:                         # it settled: the gesture is over
                        s = g.summary(t)
                        if s:
                            self._gestures.append(s)
                        del self._open[side]
            else:
                p = raw
            self._prev[side] = (p, t, raw)
        self._frames += 1
        if not any_moving:
            self._still_frames += 1
            if roll is not None:
                self._rolls.append(float(roll))

    # ---------- dreaming ----------
    def record(self, event, mode: str, t: float) -> bool:
        """Saying good night is when it consolidates the day."""
        if event.name == "sleep" and self.on:
            return self.dream()
        return False

    def tick(self, brain) -> bool:
        """A new day started without a good night: consolidate yesterday's anyway."""
        if self.on and self._day is not None and self._today() != self._day:
            return self.dream()
        return False

    def dream(self) -> bool:
        """Today's motion becomes seven numbers. The raw data is dropped either way. Returns True if
        the keeper's numbers changed (a thin day changes nothing)."""
        gestures, frames, still, rolls = self._gestures, self._frames, self._still_frames, self._rolls
        self._reset_day()
        if len(gestures) < MIN_GESTURES:
            if frames:                                    # (silent when it never saw hands, e.g. the time skip)
                print(f"[habits] a thin day ({len(gestures)} gestures), nothing learned")
            return False
        today = {k: statistics.median(g[k] for g in gestures) for k in ("tempo", "amplitude", "smoothness", "directness", "settle")}
        today["stillness"] = still / frames if frames else TYPICAL["stillness"][0]
        if len(rolls) >= 30:
            today["tilt"] = statistics.median(rolls)
        self.learn_day(today)
        print(f"[habits] dreamed on {len(gestures)} gestures: " + self.describe())
        return True

    def learn_day(self, today: dict) -> None:
        """One counted day: the keeper's numbers move ALPHA toward today's. The time skip calls this
        directly with a declared keeper style (it can't simulate years of hand frames)."""
        lid = self.cart.active.id
        page = self._page(lid)
        style = page["style"]
        for k, v in today.items():
            style[k] = round(v if k not in style else style[k] + ALPHA * (v - style[k]), 4)
        page["days"] = page.get("days", 0) + 1
        page["last"] = self._today().isoformat()
        self.cart.write_page(lid, self.name, page)
        if self.brain is not None:
            self.apply(self.brain)

    # ---------- what it does to motion ----------
    def apply(self, brain) -> None:
        """Blend every keeper's numbers into one offset per feature, -1..1."""
        today = self._today()
        total = {f: 0.0 for f in FEATURES}
        self.mix = []
        for layer in self.cart.layers:
            page = self._page(layer.id)
            if not page["style"]:
                continue
            strength = float(page.get("strength", 1.0))
            if layer.id == self.cart.active.id:
                w = strength * min(1.0, page.get("days", 0) / RAMP_DAYS)
            else:
                since = date.fromisoformat(layer.until) if layer.until else today
                w = strength * max(FLOOR, 1.0 - (today - since).days / FADE_DAYS)
            if w <= 0:
                continue
            self.mix.append((layer.id, round(w, 2)))
            for f, v in page["style"].items():
                ref, spread = TYPICAL[f]
                total[f] += w * TRUST[f] * max(-1.0, min(1.0, (v - ref) / spread))
        self.offsets = {f: max(-1.0, min(1.0, v)) for f, v in total.items()}
        brain.habit_idle = 1.0 + CAP * self.offsets["stillness"]       # calmer keeper: it glances around less often

    def restyle(self, move: str, st: dict) -> dict:
        """Called on every move after patina: shift how it plays. Every change at most CAP."""
        o = self.offsets
        if not any(o.values()):
            return st
        st = dict(st)
        st["speed"] *= 1.0 + CAP * (0.7 * o["tempo"] - 0.3 * o["settle"])
        st["size"] *= 1.0 + CAP * o["amplitude"]
        st["smooth"] = max(0.0, min(1.0, st["smooth"] + CAP * o["smoothness"]))
        st["hesitate_s"] = max(0.0, st["hesitate_s"] - 0.5 * CAP * o["directness"])
        st["tilt_deg"] += 20.0 * CAP * o["tilt"]                       # up to 6 degrees
        return st

    def describe(self) -> str:
        """'quicker, bigger · L1 40%' for the overlay. Empty if it hasn't picked anything up."""
        words = [WORDS[f][0 if v > 0 else 1] for f, v in sorted(self.offsets.items(), key=lambda kv: -abs(kv[1]))
                 if abs(v) >= 0.15][:3]
        if not words:
            return ""
        return ", ".join(words) + " · " + "  ".join(f"{lid} {w * 100:.0f}%" for lid, w in self.mix)

    # ---------- contract ----------
    def validate(self, data: dict, where: str) -> None:
        if not data:
            return
        if data.get("schema") != SCHEMA:
            raise ValueError(f"{where}: schema should be {SCHEMA!r}, found {data.get('schema')!r}")
        extra = set(data.get("style", {})) - set(FEATURES)
        if extra:
            raise ValueError(f"{where}: only the seven style numbers are kept ({', '.join(FEATURES)}), found {sorted(extra)}")
        if set(data) - {"schema", "style", "days", "last", "strength"}:
            raise ValueError(f"{where}: unknown field(s) {sorted(set(data) - {'schema', 'style', 'days', 'last', 'strength'})}")
        s = data.get("strength", 1.0)
        if not isinstance(s, (int, float)) or not 0 <= s <= 1:
            raise ValueError(f"{where}: strength should be 0 (off) to 1")

    def health(self) -> tuple[bool, str]:
        d = self.describe()
        return True, (f"moves like: {d}" if d else "nothing picked up yet")

    def _page(self, lid: str) -> dict:
        page = self.cart.read_page(lid, self.name)
        page.setdefault("schema", SCHEMA)
        page.setdefault("style", {})
        return page

    def _today(self) -> date:
        b = self.brain
        now = getattr(b, "now", None) if b is not None else None
        if now is not None:
            return now.date()
        return (b.today if b is not None and b.today else None) or datetime.now().date()
