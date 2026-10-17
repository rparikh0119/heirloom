"""Presence: Heirloom breathes and glances around while it waits. Ctrl+C to stop.

    python scripts/idle.py --body unity
    python scripts/idle.py --body reachy+unity
"""
import argparse
import random

from heirloom.body import Pose, make_body


def idle(body) -> None:
    breaths = 0
    while True:
        # One slow breath, about 4 seconds.
        body.move(Pose(head_pitch=3, antenna_left=8, antenna_right=8, iris=0.7, light=0.6), 2.0)
        body.move(Pose(head_pitch=-1, antenna_left=-2, antenna_right=-2, iris=0.55, light=0.45), 2.0)
        breaths += 1
        # Every few breaths, a curious glance to one side and back.
        if breaths >= random.randint(3, 5):
            breaths = 0
            side = random.choice([-1, 1])
            body.move(Pose(head_yaw=18 * side, head_roll=-5 * side, iris=0.85), 0.6)
            body.move(Pose(), random.uniform(0.6, 1.4))  # hold
            body.move(Pose(head_yaw=0, head_roll=0), 0.9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", default="unity")
    args = parser.parse_args()
    with make_body(args.body) as body:
        if "unity" in args.body:
            from heirloom.link import LinkServer
            print("Waiting for Unity to connect (press Play)...")
            LinkServer.get().wait_for_client()
        body.rest(1.0)
        try:
            idle(body)
        except KeyboardInterrupt:
            body.rest(1.0)


if __name__ == "__main__":
    main()
