"""Bodies. Robot SDKs are imported only inside their own adapter module."""
from .base import Body, Pose

__all__ = ["Body", "Pose", "make_body"]


def make_body(name: str) -> Body:
    """Create a body by name. Adapters are imported lazily so the brain never needs robot SDKs installed."""
    if name == "null":
        from .null_body import NullBody
        return NullBody()
    if name == "reachy":
        from .reachy_body import ReachyBody
        return ReachyBody()
    raise ValueError(f"Unknown body: {name}")
