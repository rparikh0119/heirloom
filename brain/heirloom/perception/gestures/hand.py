"""What we read from one hand in one frame. Shared by every gesture.

Positions are metres in robot space: from the robot's head at rest, x right, y up, z forward.
So the robot's head is at (0, 0, 0) and a person in front of it has positive z.

Joint order (Unity XR Hands / OpenXR, 26 joints):
    0 wrist  1 palm
    2-5   thumb:  metacarpal, proximal, distal, tip
    6-10  index:  metacarpal, proximal, intermediate, distal, tip
    11-15 middle, 16-20 ring, 21-25 little (same five as index)
"""
from __future__ import annotations

import numpy as np

WRIST, PALM = 0, 1
THUMB = (2, 3, 4, 5)
FINGERS = {"index": (7, 8, 9, 10), "middle": (12, 13, 14, 15),     # proximal, intermediate, distal, tip
           "ring": (17, 18, 19, 20), "little": (22, 23, 24, 25)}
INDEX_KNUCKLE, LITTLE_KNUCKLE = 7, 22

STRAIGHT = 0.85   # finger straightness above this = extended (1.0 = perfectly straight)
CURLED = 0.70     # below this = curled


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v * 0


def straightness(j: np.ndarray, chain) -> float:
    """Distance from first to last joint, divided by the length along the bones. 1 = straight."""
    pts = j[list(chain)]
    along = np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))
    return float(np.linalg.norm(pts[-1] - pts[0]) / along) if along > 1e-6 else 0.0


class HandState:
    """One hand, one frame. Every gesture reads from this, so it's computed once."""

    def __init__(self, joints: np.ndarray, side: str) -> None:
        j = joints
        self.joints = j
        self.side = side                      # "left" or "right"
        self.wrist = j[WRIST]
        self.palm = j[PALM]
        self.fingers = {name: straightness(j, chain) for name, chain in FINGERS.items()}
        self.thumb = straightness(j, THUMB)
        self.thumb_dir = unit(j[THUMB[-1]] - j[THUMB[1]])         # where the thumb points
        self.thumb_tip = j[THUMB[-1]]
        self.index_tip = j[FINGERS["index"][-1]]
        self.index_dir = unit(j[FINGERS["index"][-1]] - j[FINGERS["index"][0]])
        self.middle_tip = j[FINGERS["middle"][-1]]
        self.middle_dir = unit(j[FINGERS["middle"][-1]] - j[FINGERS["middle"][0]])
        # Palm normal from three points. The cross product flips between hands, so correct for that.
        n = np.cross(j[INDEX_KNUCKLE] - j[WRIST], j[LITTLE_KNUCKLE] - j[WRIST])
        self.palm_normal = unit(-n if side == "right" else n)    # the way the palm faces
        self.toward_robot = float(np.dot(self.palm_normal, unit(-self.palm)))   # 1 = palm faces the robot

    def ext(self, name: str) -> bool:
        """Is this finger extended? name: index, middle, ring, little"""
        return self.fingers[name] > STRAIGHT

    def curl(self, name: str) -> bool:
        """Is this finger curled?"""
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
