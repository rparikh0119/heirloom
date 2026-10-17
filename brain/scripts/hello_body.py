"""Heirloom says hi through any body.

    python scripts/hello_body.py --body null
    python scripts/hello_body.py --body unity          (press Play in Unity)
    python scripts/hello_body.py --body reachy         (run `reachy-mini-daemon --sim --no-media` first)
    python scripts/hello_body.py --body reachy+unity
"""
import argparse

from heirloom.body import Pose, make_body


def greet(body) -> None:
    body.move(Pose(head_pitch=15, antenna_left=35, antenna_right=35, iris=1.0, light=0.8), 1.0)  # look up, curious
    body.move(Pose(head_roll=12), 0.6)                                                          # tilt, like a question
    for _ in range(2):                                                                          # antenna wiggle
        body.move(Pose(antenna_left=15, antenna_right=-15), 0.25)
        body.move(Pose(antenna_left=-15, antenna_right=15), 0.25)
    body.rest(1.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", default="null", help="null, reachy, unity, or combined like reachy+unity")
    args = parser.parse_args()
    with make_body(args.body) as body:
        if "unity" in args.body:
            from heirloom.link import LinkServer
            print("Waiting for Unity to connect (press Play)...")
            LinkServer.get().wait_for_client()
        greet(body)
    print("Heirloom says hi.")


if __name__ == "__main__":
    main()
