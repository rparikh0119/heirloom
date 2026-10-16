"""Study tool: browse Pollen's Reachy Mini emotions library in the simulator.

Reachy-only dev tool. It lives outside the heirloom/ package on purpose, so the brain never depends on it.

    reachy-mini-daemon --sim          (terminal 1)
    python tools/reachy/browse_emotions.py   (terminal 2)

Type a number to play that move, r to replay, q to quit.
"""
from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import RecordedMoves

DATASET = "pollen-robotics/reachy-mini-emotions-library"


def main() -> None:
    print("Loading emotions library (first run downloads it)...")
    library = RecordedMoves(DATASET)
    names = sorted(library.list_moves())

    with ReachyMini(media_backend="no_media") as mini:
        last = None
        while True:
            print()
            for i, name in enumerate(names):
                print(f"{i:3d}  {name:22s} {library.get(name).description[:70]}")
            choice = input("\nPlay # (r = replay, q = quit): ").strip().lower()
            if choice == "q":
                break
            if choice == "r" and last is not None:
                idx = last
            elif choice.isdigit() and int(choice) < len(names):
                idx = int(choice)
            else:
                continue
            last = idx
            print(f"> {names[idx]}")
            mini.play_move(library.get(names[idx]), initial_goto_duration=0.5, sound=False)


if __name__ == "__main__":
    main()
