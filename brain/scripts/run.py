"""Run Heirloom: presence + reactions + chirps (+ voice). Ctrl+C to stop.

    python scripts/run.py --body unity
    python scripts/run.py --body unity --voice          # talk to it (say "Heirloom" first)
    python scripts/run.py --body unity --voice --mic 3  # pick a microphone (see scripts/voice_test.py --list)
    python scripts/run.py --body reachy+unity
    python scripts/run.py --body unity --gesture-debug  # print finger states twice a second, for tuning

Hand gestures arrive from Unity (HandStream on the BrainLink object) and are read in the brain:
    thumbs up = good · palm out = not now · wave = hello · beckon = curious · middle finger = offended
    heart (both hands) = love

In the Unity Editor, number keys (Game view focused) send events:
    1 wave   2 good job   3 not now   4 go to sleep   5 wake up   6 curious
    7 offended   8 scold ("no")   9 sorry   0 heart
"""
import argparse
import time

from heirloom.body import make_body
from heirloom.brain import HeirloomBrain
from heirloom.link import LinkServer
from heirloom.perception.gestures import GestureDetector

HZ = 30


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", default="unity")
    parser.add_argument("--voice", action="store_true", help="listen through the microphone")
    parser.add_argument("--mic", type=int, default=None, help="microphone number")
    parser.add_argument("--gesture-debug", action="store_true", help="print what each finger is doing")
    args = parser.parse_args()

    voice = None
    if args.voice:
        from heirloom.perception.voice import VoiceListener   # only needs vosk when used
        voice = VoiceListener(mic=args.mic).start()

    link = LinkServer.get()
    with make_body(args.body) as body:
        print("Waiting for Unity to connect (press Play)...")
        link.wait_for_client()
        brain = HeirloomBrain(play_sound=body.play_sound)
        gestures = GestureDetector(debug=args.gesture_debug)
        last_mode, last = None, time.perf_counter()
        try:
            while True:
                now = time.perf_counter()
                dt, last = now - last, now

                events = link.pop_events() + (voice.pop_events() if voice else [])
                events += gestures.step(dt, link.latest("hands", max_age=0.3))
                for event in events:
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
        finally:
            if voice:
                voice.stop()


if __name__ == "__main__":
    main()
