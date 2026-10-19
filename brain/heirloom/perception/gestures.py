"""Hand gestures, read from hand joints. No Meta code, so the same logic works on any camera later.

Input: one "hands" message from Unity (or, in winter, from the robot's camera through MediaPipe):
    {"type": "hands", "left_tracked": bool, "left": [x,y,z]*26, "right_tracked": bool, "right": [...]}
Positions are metres in robot space: measured from the robot's head at rest, x right, y up, z forward.
So the robot's head is at (0, 0, 0) and a person in front of it has positive z.

Joint order (Unity XR Hands / OpenXR, 26 joints):
    0 wrist  1 palm
    2-5   thumb:  metacarpal, proximal, distal, tip
    6-10  index:  metacarpal, proximal, intermediate, distal, tip
    11-15 middle, 16-20 ring, 21-25 little (same five as index)

Gestures -> brain events:
    thumbs up      -> good       four fingers curled, thumb pointing up
    middle finger  -> offended   middle straight, index/ring/little curled
    palm out, still-> not_now    open hand, palm facing the robot, held still
    wave           -> wave       open hand swinging side to side
    beckon         -> curious    palm up, index finger curling in and out (2+ times)
    heart (2 hands)-> heart      index tips touching on top, thumb tips touching below
"""
from __future__ import annotations

from collections import deque

import numpy as np

WRIST, PALM = 0, 1
THUMB = (2, 3, 4, 5)
FINGERS = {"index": (7, 8, 9, 10), "middle": (12, 13, 14, 15),     # proximal, intermediate, distal, tip
           "ring": (17, 18, 19, 20), "little": (22, 23, 24, 25)}
INDEX_KNUCKLE, LITTLE_KNUCKLE = 7, 22

# Tuning (change one at a time and watch --gesture-debug)
STRAIGHT = 0.85        # finger straightness above this = extended (1.0 = perfectly straight)
CURLED = 0.70          # below this = curled
HOLD = 0.30            # seconds a pose must be held before it counts
STILL_SPEED = 0.25     # m/s, palm-out must be held about this still (so a wave isn't a stop)
COOLDOWN_SAME = 2.5    # seconds before the same gesture can fire again
COOLDOWN_ANY = 1.0     # seconds after any gesture before another can fire

EVENTS = {"thumbs_up": "good", "middle_finger": "offended", "palm_out": "not_now",
          "wave": "wave", "beckon": "curious", "heart": "heart"}
BECKON_DEPTH = 0.10    # how far the index straightness has to dip and recover to count as one curl
HEART_TOUCH = 0.045    # metres: index tips (and thumb tips) closer than this count as touching


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v * 0


def straightness(j: np.ndarray, chain) -> float:
    """Distance from first to last joint, divided by the length along the bones. 1 = straight."""
    pts = j[list(chain)]
    along = np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))
    return float(np.linalg.norm(pts[-1] - pts[0]) / along) if along > 1e-6 else 0.0


class HandState:
    """Everything we read from one hand in one frame."""

    def __init__(self, joints: np.ndarray, side: str) -> None:
        j = joints
        self.side = side
        self.palm = j[PALM]
        self.fingers = {name: straightness(j, chain) for name, chain in FINGERS.items()}
        self.thumb = straightness(j, THUMB)
        self.thumb_dir = _unit(j[THUMB[-1]] - j[THUMB[1]])
        self.middle_dir = _unit(j[FINGERS["middle"][-1]] - j[FINGERS["middle"][0]])
        self.middle_tip = j[FINGERS["middle"][-1]]
        self.index_tip = j[FINGERS["index"][-1]]
        self.thumb_tip = j[THUMB[-1]]
        self.wrist = j[WRIST]
        # Palm normal from three points. The cross product flips between hands, so correct for that.
        n = np.cross(j[INDEX_KNUCKLE] - j[WRIST], j[LITTLE_KNUCKLE] - j[WRIST])
        self.palm_normal = _unit(-n if side == "right" else n)
        self.toward_robot = float(np.dot(self.palm_normal, _unit(-self.palm)))   # 1 = palm faces the robot's head

    def ext(self, name: str) -> bool:
        return self.fingers[name] > STRAIGHT

    def curl(self, name: str) -> bool:
        return self.fingers[name] < CURLED

    @property
    def open(self) -> bool:
        return sum(self.ext(f) for f in FINGERS) >= 4

    def summary(self) -> str:
        f = " ".join(f"{n[0].upper()}{'+' if self.ext(n) else '-' if self.curl(n) else '~'}"
                     for n in FINGERS)
        return (f"{self.side[0].upper()}: T{'+' if self.thumb > STRAIGHT else '~'} {f}  "
                f"palm->robot {self.toward_robot:+.2f}  palm up {self.palm_normal[1]:+.2f}  "
                f"thumb up {self.thumb_dir[1]:+.2f}")


class _Tracker:
    """Per-hand memory: how long each pose has been held, and recent motion for wave and beckon."""

    def __init__(self) -> None:
        self.held: dict[str, float] = {}
        self.tips: deque[tuple[float, np.ndarray]] = deque()
        self.palms: deque[tuple[float, np.ndarray]] = deque()
        self.index_curls: deque[tuple[float, float]] = deque()
        self.latched: set[str] = set()   # static poses that already fired and are still being held
        self.palm_ups: deque[tuple[float, float]] = deque()


class GestureDetector:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        self._t = 0.0
        self._hands = {"left": _Tracker(), "right": _Tracker()}
        self._last_fired: dict[str, float] = {}
        self._last_any = -99.0
        self._next_debug = 0.0
        self._heart_held = 0.0
        self._heart_latched = False

    def step(self, dt: float, msg: dict | None) -> list[str]:
        """Feed the newest hands message (or None). Returns brain events that fired this tick."""
        self._t += dt
        fired: list[str] = []
        lines = []
        states: dict[str, HandState] = {}
        for side in self._hands:
            joints = None
            if msg and msg.get(f"{side}_tracked"):
                arr = np.asarray(msg.get(side) or [], dtype=float)
                if arr.size == 78 and np.all(np.isfinite(arr)):
                    joints = arr.reshape(26, 3)
            if joints is None:
                self._hands[side] = _Tracker()   # lost the hand: forget its history
                continue
            states[side] = HandState(joints, side)
            lines.append(states[side].summary())

        # Two-hand gestures first. While both hands make a heart, single-hand gestures are ignored.
        heart = self._heart(states, dt)
        if heart:
            if self._can_fire("heart"):
                self._fire("heart", "both", fired)
                self._heart_latched = True
        else:
            for side, hand in states.items():
                tracker = self._hands[side]
                for gesture in self._detect(hand, tracker, dt):
                    if self._can_fire(gesture):
                        tracker.latched.add(gesture)          # holding a pose fires it once
                        if gesture in ("wave", "beckon"):     # start the motion history fresh
                            tracker.tips.clear()
                            tracker.index_curls.clear()
                        self._fire(gesture, side, fired)
                        break

        if self.debug and self._t >= self._next_debug:
            self._next_debug = self._t + 0.5
            print("[hands] " + ("   |   ".join(lines) if lines else "no hands"))
        return fired

    def _fire(self, gesture: str, side: str, fired: list[str]) -> None:
        self._last_fired[gesture] = self._last_any = self._t
        print(f"[gesture] {side} {gesture} -> {EVENTS[gesture]}")
        fired.append(EVENTS[gesture])

    def _heart(self, states: dict, dt: float) -> bool:
        """Both hands: index tips touching above, thumb tips touching below, held briefly. Fires once per hold."""
        on = False
        if "left" in states and "right" in states:
            l, r = states["left"], states["right"]
            on = (np.linalg.norm(l.index_tip - r.index_tip) < HEART_TOUCH
                  and np.linalg.norm(l.thumb_tip - r.thumb_tip) < HEART_TOUCH
                  and (l.index_tip[1] + r.index_tip[1]) / 2 > (l.thumb_tip[1] + r.thumb_tip[1]) / 2 + 0.03
                  and np.linalg.norm(l.wrist - r.wrist) > 0.08)
        self._heart_held = self._heart_held + dt if on else 0.0
        if not on:
            self._heart_latched = False
        return on and self._heart_held >= HOLD and not self._heart_latched

    # ---------- detection ----------
    def _detect(self, h: HandState, tr: _Tracker, dt: float) -> list[str]:
        now = self._t
        tr.tips.append((now, h.middle_tip.copy()))
        tr.palms.append((now, h.palm.copy()))
        tr.index_curls.append((now, h.fingers["index"]))
        tr.palm_ups.append((now, float(h.palm_normal[1])))
        for q, keep in ((tr.tips, 1.2), (tr.palms, 0.3), (tr.index_curls, 2.5), (tr.palm_ups, 2.5)):
            while q and now - q[0][0] > keep:
                q.popleft()

        out = []
        # Motion gestures first, so a waving open hand isn't read as "stop".
        if h.open and h.middle_dir[1] > 0.3 and self._swings(tr):
            out.append("wave")
        palm_stays_up = min(v for _, v in tr.palm_ups) > 0.4
        if palm_stays_up and self._palm_speed(tr) < STILL_SPEED and self._curl_cycles(tr) >= 2:
            out.append("beckon")

        static = {
            "thumbs_up": all(h.curl(f) for f in FINGERS) and h.thumb_dir[1] > 0.7,
            "middle_finger": h.ext("middle") and all(h.curl(f) for f in ("index", "ring", "little")),
            "palm_out": h.open and h.toward_robot > 0.6 and self._palm_speed(tr) < STILL_SPEED,
        }
        for name, on in static.items():
            tr.held[name] = tr.held.get(name, 0.0) + dt if on else 0.0
            if not on:
                tr.latched.discard(name)    # let go of the pose, so it can fire again next time
            elif tr.held[name] >= HOLD and name not in tr.latched:
                out.append(name)
        return out

    @staticmethod
    def _swings(tr: _Tracker) -> bool:
        """Did the fingertips reverse direction side to side at least 3 times, by 3 cm or more?"""
        if len(tr.tips) < 8:
            return False
        pts = np.array([p for _, p in tr.tips])
        # "Side to side" from the person's point of view: horizontal, across the line to the robot.
        to_robot = _unit(np.array([-pts[-1][0], 0.0, -pts[-1][2]]))
        across = np.array([to_robot[2], 0.0, -to_robot[0]])
        x = pts @ across
        reversals, direction, anchor = 0, 0, x[0]
        for v in x[1:]:
            if direction >= 0 and v < anchor - 0.03:
                reversals += direction > 0
                direction, anchor = -1, v
            elif direction <= 0 and v > anchor + 0.03:
                reversals += direction < 0
                direction, anchor = 1, v
            elif (direction > 0 and v > anchor) or (direction < 0 and v < anchor):
                anchor = v
        return reversals >= 3

    @staticmethod
    def _curl_cycles(tr: _Tracker) -> int:
        """How many times the index finger dipped and came back up recently.

        Measured as a relative dip, not fixed thresholds: a real beckon only hooks the finger
        partway (straightness ~0.95 -> ~0.75 in testing), it rarely fully curls.
        """
        cycles, peak, trough, dipping = 0, None, None, False
        for _, s in tr.index_curls:
            if peak is None:
                peak = s
            elif not dipping:
                peak = max(peak, s)
                if s < peak - BECKON_DEPTH:
                    dipping, trough = True, s
            else:
                trough = min(trough, s)
                if s > trough + BECKON_DEPTH:
                    cycles += 1
                    dipping, peak = False, s
        return cycles

    @staticmethod
    def _palm_speed(tr: _Tracker) -> float:
        if len(tr.palms) < 2:
            return 0.0
        (t0, p0), (t1, p1) = tr.palms[0], tr.palms[-1]
        return float(np.linalg.norm(p1 - p0) / max(1e-3, t1 - t0))

    def _can_fire(self, gesture: str) -> bool:
        if self._t - self._last_any < COOLDOWN_ANY:
            return False
        return self._t - self._last_fired.get(gesture, -99.0) >= COOLDOWN_SAME
