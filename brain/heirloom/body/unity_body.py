"""A body that lives in Unity. Interpolates moves and streams every frame over the link."""
from __future__ import annotations

import base64
import time

from ..link import LinkServer
from ..sound import render, to_wav_bytes
from .base import REST, Body, Pose

FPS = 60


def min_jerk(s: float) -> float:
    """Smooth 0..1 easing with zero velocity and acceleration at both ends."""
    return s * s * s * (10 - 15 * s + 6 * s * s)


def _small_jpeg(path, longest: int = 1024) -> bytes:
    """Phone photos are several MB, which stalls Unity while it decodes. Shrink to about 1024 px
    if Pillow is installed (pip install pillow), otherwise send the file as it is."""
    try:
        import io
        from PIL import Image, ImageOps
    except ImportError:
        return path.read_bytes()
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")      # phone photos store rotation separately
        im.thumbnail((longest, longest))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=85)
        return out.getvalue()


class UnityBody(Body):
    supports = frozenset(Pose().__dataclass_fields__)

    def __init__(self) -> None:
        self._pose = Pose(**REST.channels())
        self._link: LinkServer | None = None

    def connect(self) -> None:
        self._link = LinkServer.get()

    def move(self, pose: Pose, duration: float = 0.5) -> None:
        start = self._pose.channels()
        target = {**start, **pose.channels()}
        frames = max(1, int(duration * FPS))
        t0 = time.perf_counter()
        for i in range(1, frames + 1):
            s = min_jerk(i / frames)
            current = {k: start[k] + (target[k] - start[k]) * s for k in target}
            self._link.broadcast({"type": "pose", "ch": current})
            delay = t0 + i / FPS - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
        self._pose = Pose(**target)

    def set_target(self, pose: Pose) -> None:
        self._pose = Pose(**{**self._pose.channels(), **pose.channels()})
        self._link.broadcast({"type": "pose", "ch": self._pose.channels()})

    def play_clip(self, wav: bytes) -> None:
        self._link.broadcast({"type": "sound", "name": "memory", "wav_b64": base64.b64encode(wav).decode("ascii")})

    def show_photo(self, path) -> None:
        """Unity draws the beam and the photo on the real desk (ProjectorBeam.cs)."""
        if path is None:
            self._link.broadcast({"type": "project", "name": ""})
            return
        from pathlib import Path
        self._link.broadcast({"type": "project", "name": Path(path).name,
                              "image_b64": base64.b64encode(_small_jpeg(Path(path))).decode("ascii")})

    def play_sound(self, name: str) -> None:
        wav = to_wav_bytes(render(name))
        self._link.broadcast({"type": "sound", "name": name, "wav_b64": base64.b64encode(wav).decode("ascii")})
