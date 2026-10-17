"""Bodies. Robot SDKs are imported only inside their own adapter module."""
from .base import Body, Pose

__all__ = ["Body", "Pose", "make_body", "BODY_NAMES"]

BODY_NAMES = ("null", "reachy", "unity")


def _make_one(name: str) -> Body:
    # Adapters are imported lazily so the brain never needs robot SDKs installed.
    if name == "null":
        from .null_body import NullBody
        return NullBody()
    if name == "reachy":
        from .reachy_body import ReachyBody
        return ReachyBody()
    if name == "unity":
        from .unity_body import UnityBody
        return UnityBody()
    raise ValueError(f"Unknown body: {name!r}. Use one of {BODY_NAMES}, or combine with '+', e.g. reachy+unity")


def make_body(spec: str) -> Body:
    """'unity', 'reachy', 'null', or several joined with '+' (e.g. 'reachy+unity')."""
    names = [n.strip() for n in spec.split("+") if n.strip()]
    if len(names) == 1:
        return _make_one(names[0])
    from .multi_body import MultiBody
    return MultiBody([_make_one(n) for n in names])
