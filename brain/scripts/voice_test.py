"""Check the voice listener on its own: no Unity, no robot. Ctrl+C to stop.

    python scripts/voice_test.py            # default mic
    python scripts/voice_test.py --list     # show microphones
    python scripts/voice_test.py --mic 3    # use microphone number 3

Say "Heirloom", then "good job". You should see:  heard "heirloom" -> listen, then -> good
"""
import argparse
import time

from heirloom.perception.voice import VoiceListener


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mic", type=int, default=None)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        import sounddevice as sd
        print(sd.query_devices())
        return

    voice = VoiceListener(mic=args.mic).start()
    try:
        while True:
            for e in voice.pop_events():
                print(f"    >>> brain event: {e}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        voice.stop()


if __name__ == "__main__":
    main()
