"""Run Heirloom: presence + reactions + chirps. Ctrl+C to stop.

    python scripts/run.py --body unity
    python scripts/run.py --body reachy+unity

In the Unity Editor, number keys (Game view focused) send events:
    1 wave   2 good job   3 not now   4 go to sleep   5 wake up   6 curious
"""
import argparse
import time

from heirloom.body import make_body
from heirloom.brain import HeirloomBrain
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
        brain = HeirloomBrain(play_sound=body.play_sound)
        last_mode, last = None, time.perf_counter()
        try:
            while True:
                now = time.perf_counter()
                dt, last = now - last, now

                for event in link.pop_events():
                    print(f"[event] {event}")
                    brain.handle(event)

                user = link.latest("user", max_age=0.5)
                pose, info = brain.step(dt, tuple(user["head"]) if user else None)
                body.set_target(pose)
                link.broadcast({"type": "state", **info})

                if info["mode"] != last_mode:
                    print(f"[mode] {info['mode']}")
                    last_mode = info["mode"]
                time.sleep(max(0.0, 1.0 / HZ - (time.perf_counter() - now)))
        except KeyboardInterrupt:
            body.rest(1.0)


if __name__ == "__main__":
    main()
