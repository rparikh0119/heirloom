"""Presence station: Heirloom breathes, notices you, and looks at you. Ctrl+C to stop.

    python scripts/presence.py --body unity
    python scripts/presence.py --body reachy+unity
"""
import argparse
import time

from heirloom.behavior import Presence
from heirloom.body import make_body
from heirloom.link import LinkServer

HZ = 30


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", default="unity")
    args = parser.parse_args()

    link = LinkServer.get()
    with make_body(args.body) as body:
        print("Waiting for Unity to connect (press Play)...")
        link.wait_for_client()
        presence = Presence()
        last_mode = None
        last = time.perf_counter()
        try:
            while True:
                now = time.perf_counter()
                dt, last = now - last, now
                user = link.latest("user", max_age=0.5)
                head = tuple(user["head"]) if user else None
                pose, info = presence.step(dt, head)
                body.set_target(pose)
                link.broadcast({"type": "state", **info})
                if info["mode"] != last_mode:
                    print(f"[presence] {info['mode']}")
                    last_mode = info["mode"]
                time.sleep(max(0.0, 1.0 / HZ - (time.perf_counter() - now)))
        except KeyboardInterrupt:
            body.rest(1.0)


if __name__ == "__main__":
    main()
