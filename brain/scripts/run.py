"""Run Heirloom: presence + reactions + chirps (+ voice). Ctrl+C to stop.

    python scripts/run.py --body unity
    python scripts/run.py --body unity --voice          # talk to it (up close just talk, from afar say "Heirloom" first)
    python scripts/run.py --body unity --voice --mic 3  # pick a microphone (see scripts/voice_test.py --list)
    python scripts/run.py --body unity --voice --voice-model small.en   # bigger Whisper, more accurate, a bit slower
    python scripts/run.py --body unity --voice --voice-engine vosk      # the old phrase-list recogniser
    python scripts/run.py --body unity --voice --need-name              # loud room: from afar, say "Heirloom" first
    python scripts/run.py --body reachy+unity
    python scripts/run.py --body unity --gesture-debug  # print finger states twice a second, for tuning
    python scripts/run.py --body unity --cartridge cartridges/riya   # learn into a cartridge (made if missing)
    python scripts/run.py --body unity --cartridge cartridges/riya --learn-from-keys   # key presses count too

Two droids side by side (fresh vs worn), each brain in its own terminal, each Unity link on its own port:
    python scripts/run.py --body unity --voice --port 8765 --cartridge cartridges/fresh_test
    python scripts/run.py --body unity --voice --port 8766 --cartridge cartridges/sim/loud_family_year12

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
from heirloom.cartridge import Cartridge
from heirloom.events import as_event
from heirloom.link import LinkServer
from heirloom.perception.gestures import GestureDetector

HZ = 30


def _label_from(folder: str) -> str:
    """cartridges/sim/loud_family_year12 -> LOUD FAMILY  YEAR 12.  cartridges/fresh_test -> FRESH TEST"""
    import re
    from pathlib import Path
    name = Path(folder).name.replace("_", " ")
    name = re.sub(r"(year|month|day)(\d+)", r" \1 \2", name)
    return " ".join(name.upper().split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", default="unity")
    parser.add_argument("--voice", action="store_true", help="listen through the microphone")
    parser.add_argument("--mic", type=int, default=None, help="microphone number")
    parser.add_argument("--voice-engine", choices=["whisper", "vosk"], default="whisper",
                        help="whisper understands ordinary speech (D63). vosk only knows the phrase list")
    parser.add_argument("--voice-model", default="base.en", help="Whisper size: tiny.en, base.en, small.en")
    parser.add_argument("--need-name", action="store_true",
                        help="loud rooms: from further away, say 'Heirloom' first. Off by default, just talk (D64)")
    parser.add_argument("--gesture-debug", action="store_true", help="print what each finger is doing")
    parser.add_argument("--cartridge", default=None, help="folder of the cartridge to learn into")
    parser.add_argument("--port", type=int, default=8765, help="link port. A second droid uses 8766")
    parser.add_argument("--name", default=None, help="label on the overlay (default: from the cartridge folder)")
    parser.add_argument("--learn-from-keys", action="store_true",
                        help="let Unity key presses leave wear (off by default, so testing doesn't change the droid)")
    args = parser.parse_args()

    cartridge = None
    if args.cartridge:
        from pathlib import Path
        path = Path(args.cartridge)
        cartridge = Cartridge.open(path) if (path / "cartridge.json").exists() else Cartridge.create(path)
        cartridge.seat(args.body)
        print(f"[cartridge] {path}  droid {cartridge.droid.get('id')}  {cartridge.health()[1]}")

    voice = None
    if args.voice and args.voice_engine == "whisper":
        from heirloom.perception.whisper_voice import WhisperListener   # only needs faster-whisper when used
        voice = WhisperListener(mic=args.mic, model=args.voice_model, require_wake_word=args.need_name).start()
    elif args.voice:
        from heirloom.perception.voice import VoiceListener   # only needs vosk when used
        voice = VoiceListener(mic=args.mic, require_wake_word=args.need_name).start()

    link = LinkServer.get(port=args.port)
    with make_body(args.body) as body:
        print("Waiting for Unity to connect (press Play)...")
        link.wait_for_client()
        ignores = set() if args.learn_from_keys else {"unity"}
        brain = HeirloomBrain(play_sound=body.play_sound, cartridge=cartridge, wear_ignores=ignores)
        brain.label = args.name or (_label_from(args.cartridge) if args.cartridge else "NO CARTRIDGE")
        if cartridge:
            print("[dials] " + "  ".join(f"{k} {v:.3f}" for k, v in brain.character.dials.items()))
            print("[wear] learning from hands and voice" + (" and keys" if args.learn_from_keys else " (keys don't count)"))
            ws = brain.wear_state()
            worn = "  ".join(f"{v['name']} {v['settled']:.2f}/{v['character']:.2f}" for v in ws["moves"]) or "none yet"
            print(f"[patina] settled/character: {worn}")
            print(f"[patina] rust {ws['rust']:.2f}, notices you at {ws['notice_m']:.2f} m")
        problems = [(n, m) for n, ok, m in brain.health() if not ok]
        print(f"[health] {len(brain.health())} modules checked, " + (f"{len(problems)} problem(s):" if problems else "all ok"))
        for name, msg in problems:
            print(f"  ! {name}: {msg}")
        gestures = GestureDetector(debug=args.gesture_debug)
        last_mode, last = None, time.perf_counter()
        wear, next_wear = brain.wear_state(), 0.0
        try:
            while True:
                now = time.perf_counter()
                dt, last = now - last, now

                # Every sense feeds the same stream. The source is kept so the brain knows how it heard.
                events = [as_event(e, "unity") for e in link.pop_events()]
                events += [as_event(e, "voice") for e in (voice.pop_events() if voice else [])]
                user = link.latest("user", max_age=0.5)
                head = user["head"] if user else None
                events += [as_event(e, "hands") for e in gestures.step(dt, link.latest("hands", max_age=0.3), head)]
                for event in events:
                    print(f"[event] {event}")
                    brain.handle(event)

                pose, info = brain.step(dt, tuple(user["head"]) if user else None)
                if voice:   # up close, no name needed (D61). Your real distance, even while it gives you space or sulks
                    near = user is not None and sum(v * v for v in user["head"]) ** 0.5 < brain.presence.cfg.notice_distance
                    voice.addressed = near
                body.set_target(pose)
                if now >= next_wear:                  # wear changes slowly, so once a second is plenty
                    wear, next_wear = brain.wear_state(), now + 1.0
                link.broadcast({"type": "state", **info, "wear": wear})

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
