"""Wear plug-ins. Every Wear subclass in this folder is found automatically."""
from __future__ import annotations

import importlib
import pkgutil

from .base import Wear


def load_wear() -> list[Wear]:
    for info in pkgutil.iter_modules(__path__):
        if info.name != "base":
            importlib.import_module(f"{__name__}.{info.name}")
    found, stack = [], list(Wear.__subclasses__())
    while stack:
        cls = stack.pop()
        stack += cls.__subclasses__()
        if cls.name:
            found.append(cls())
    return sorted(found, key=lambda w: w.name)


__all__ = ["Wear", "load_wear"]
