"""Mode plug-ins. Every Mode subclass in this folder is found automatically."""
from __future__ import annotations

import importlib
import pkgutil

from .base import Mode


def load_modes() -> dict[str, Mode]:
    for info in pkgutil.iter_modules(__path__):
        if info.name != "base":
            importlib.import_module(f"{__name__}.{info.name}")
    found = {}
    stack = list(Mode.__subclasses__())
    while stack:
        cls = stack.pop()
        stack += cls.__subclasses__()
        if cls.name:
            found[cls.name] = cls()
    return found


__all__ = ["Mode", "load_modes"]
