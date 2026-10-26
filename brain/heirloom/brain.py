"""Heirloom's brain core. It doesn't know any specific reaction or mode by name.

Every tick:  events -> reactions (reactions/*.json) -> modes (heirloom/modes/) -> one pose.

    awake      the default: presence runs (idle, or attending to you)
    any mode   loaded from heirloom/modes/, started and ended by reactions

To add behaviour, add a reaction file or a mode file. This file shouldn't need to change.

With a cartridge, wear plug-ins (heirloom/wear/) learn from every event and shape the character.
Without one, it behaves exactly like the out-of-the-box droid.
"""
from __future__ import annotations

from .behavior.expressions import EXPRESSIONS, ExpressionPlayer
from .behavior.presence import Presence, PresenceConfig
from .behavior.rolling import Roller
from .body.base import Pose
from .character import load_character
from .events import Event, as_event
from .journal import Journal
from .modes import load_modes
from .reactions import choose, load_reactions
from .sound.chirps import CHIRPS, to_wav_bytes
from .sound.tape import framed, tape
from .wear import load_wear

AWAKE = "awake"
REFLEXES = {"hearing"}     # the moment you start talking (whisper_voice), before it knows what you said


class HeirloomBrain:
    def __init__(self, play_sound, reactions_dir=None, cartridge=None, wear_ignores=(), show_photo=None,
                 play_clip=None, take_photo=None) -> None:
        """play_sound(name) is called whenever the brain wants to chirp.
        show_photo(path or None) projects a journal photo, or stops (bodies without a projector skip it).
        play_clip(wav bytes) plays a voice memory through the body's speaker.
        take_photo() asks the body's camera for a picture. It comes back as a 'photo_taken' event.
        cartridge: an opened Cartridge, or None to run without learning.
        wear_ignores: event sources that never leave wear, e.g. {"unity"} so test key presses don't count."""
        self.character = load_character()
        c = self.character
        self.presence = Presence(PresenceConfig(notice_distance=c.notice_distance, glance_gap=c.glance_gap))
        self.expr = ExpressionPlayer(scale=c.motion_scale)
        self.play_sound = play_sound
        self.modes = load_modes()
        for mode in self.modes.values():
            mode.character = c
        kwargs = {"motions": EXPRESSIONS, "sounds": CHIRPS, "modes": self.modes}
        if reactions_dir is not None:
            kwargs["folder"] = reactions_dir
        self.reactions = load_reactions(**kwargs)
        self.mode = AWAKE
        self._blend = {name: 0.0 for name in self.modes}   # 0 = off .. 1 = fully in that mode
        self._last_attending = False
        self.t = 0.0                                         # seconds since it woke up
        self.today = None                                    # None = the real date. The time skip sets a pretend one
        self.shyness = 0.0                                   # set by wear after time apart (Rule 5). 0 = normal
        self.label = ""                                      # a name for this droid on the overlay, e.g. "FRESH"
        self.show_photo = show_photo or (lambda path: None)
        self.play_clip = play_clip or (lambda wav: None)
        self.take_photo = take_photo or (lambda: None)
        self.journal = Journal.for_cartridge(cartridge)
        self.showing = None                                  # the photo being projected right now, or None
        self.roller = Roller()                               # where it has rolled to on the desk
        self._user = None                                    # where the person was last seen (robot space)
        self._next_tick = 60.0

        # Wear: only with a cartridge. Each plug-in blends its layers into the brain.
        self.cartridge = cartridge
        self.wear = load_wear() if cartridge is not None else []
        self.wear_ignores = set(wear_ignores)
        for w in self.wear:
            w.attach(cartridge, self)
            w.apply(self)
        self._refresh_character()

    def _refresh_character(self) -> None:
        """Push the current dials into the parts that use them. Modes read them live."""
        c = self.character
        self.presence.cfg.notice_distance = c.notice_distance_when_shy(self.shyness)
        self.presence.cfg.glance_gap = c.glance_gap
        self.expr.scale = c.motion_scale

    # ---------- events ----------
    def handle(self, event: "Event | str") -> str | None:
        """React to one event. Returns the reaction file used, or None if it was ignored."""
        e = as_event(event)
        if e.name in REFLEXES:             # instant, below the level of reactions and wear
            return self._reflex(e.name)
        if e.name == "photo_taken" and not self._keep_photo(e):
            return None
        if e.name == "recorded" and not self._keep_recording(e):
            return None
        if e.name == "play_memory" and not self._play_memory(e):
            return None
        if e.name == "not_now" and self.mode == "showing" and self.showing is not None:
            self.journal.retire(self.showing)          # D45: "not now" during a memory retires it for good
            print(f"[journal] retired {self.showing.name}")
        learns = e.source not in self.wear_ignores
        changed = [w for w in self.wear if learns and w.record(e, self.mode, self.t)]
        for w in changed:
            w.apply(self)
        if changed:
            self._refresh_character()

        current = self.modes.get(self.mode)
        if current and current.ends_on_any_event and e.name != current.name:
            self.mode = AWAKE              # e.g. listening ends when you say the actual command
            current = None

        r = choose(self.reactions, e.name, self.mode, bool(current and current.blocks_by_default))
        if r is None:
            if not any(e.name in x.when for x in self.reactions):
                print(f"[brain] no reaction file for '{e.name}' (add one in brain/reactions/)")
            return None

        if r.mode:
            self._set_mode(r.mode)
        if r.motion:
            self.expr.play(r.motion)
            worn = [w for w in self.wear if learns and w.played("motion", r.motion, self.t)]
            for w in worn:
                w.apply(self)
            if worn:
                self._refresh_character()
        if r.sound:
            self._sound(r.sound)
        if e.name == "curious" and self.roller.toward(self._user):      # beckoned: roll over to you
            self._set_mode("rolling")
        elif e.name == "go_home" and self.roller.home():
            self._set_mode("rolling")
        self._sync_projection()
        return r.file

    def _keep_photo(self, e: Event) -> bool:
        """Save a photo the droid just took into the cartridge journal."""
        path = self.journal.save_photo(e.data.get("jpeg", b""))
        if path is None:
            print("[journal] can't keep a photo without a cartridge (run with --cartridge)")
            return False
        print(f"[journal] saved photo {path.name}")
        return True

    def _shooting_cues(self) -> None:
        """The countdown beeps and the shutter, timed by the 'shooting' mode."""
        mode = self.modes.get("shooting")
        if mode is None:
            return
        for cue in mode.pop_cues():
            if cue == "snap":
                self._sound("shutter")
                self.take_photo()
            else:
                self._sound(cue)

    def _keep_recording(self, e: Event) -> bool:
        """Save a voice memory into the cartridge (D33). Returns False if there was nowhere to keep it."""
        audio, sr, said = e.data.get("audio"), e.data.get("sr", 16000), e.data.get("said", "")
        path = self.journal.save_voice(audio, sr, said) if audio is not None else None
        if path is None:
            print("[journal] can't keep a recording without a cartridge (run with --cartridge)")
            self.mode = AWAKE
            return False
        print(f"[journal] saved {path.name}: \"{said}\" ({len(audio) / sr:.1f} s)")
        return True

    def _play_memory(self, e: Event) -> bool:
        """Play the voice memory asked for, through the tape filter (D33)."""
        path = self.journal.find_voice(e.data.get("said", ""))
        if path is None:
            print("[journal] no voice memories yet (say \"record this\")")
            return False
        samples, sr = self.journal.load_voice(path)
        clip = framed(tape(samples, sr), sr)                 # a soft chirp before and after: it presents the memory
        self.play_clip(to_wav_bytes(clip, sr))
        self.modes["replaying"].duration = len(clip) / sr + 0.5
        print(f"[journal] playing {path.name}")
        return True

    def _sync_projection(self) -> None:
        """Start projecting when 'showing' begins, stop when it ends."""
        if self.mode == "showing" and self.showing is None:
            photo = self.journal.pick()
            if photo is None:
                print("[journal] nothing to show (no photos)")
                self.mode = AWAKE
                return
            self.showing = photo
            print(f"[journal] showing {photo.name}")
            self.show_photo(photo)
        elif self.mode != "showing" and self.showing is not None:
            self.showing = None
            self.show_photo(None)

    def _reflex(self, name: str) -> None:
        """Reflexes skip reaction files and patina, so they're instant even on a brand new droid,
        and never count as a move it has practised."""
        if name == "hearing" and self.mode not in ("sleep", "sulk"):
            self.presence.perk(0.4, 18.0)          # antennas lift a little: "I hear you"
        return None

    def _sound(self, name: str) -> None:
        current = self.modes.get(self.mode)
        if not (current and current.silent):
            self.play_sound(name)

    def _set_mode(self, name: str) -> None:
        self.mode = name
        if name != AWAKE:
            self.modes[name].enter()

    def pass_time(self, seconds: float) -> None:
        """Let time go by with nobody watching (no poses). The time skip uses this between moments,
        so a sulk or a nap runs out the way it would in real life."""
        self.t += seconds
        current = self.modes.get(self.mode)
        if current and not current.step(seconds):
            self.mode = AWAKE
        self.expr.name = None
        self._sync_projection()

    # ---------- every tick ----------
    def step(self, dt: float, user_head) -> tuple[Pose, dict]:
        self.t += dt
        self._user = user_head
        if self.roller.step(dt) and self.mode == "rolling":    # arrived
            self.mode = AWAKE
        if self.t >= self._next_tick:                        # about once a minute, wear can notice time passing
            self._next_tick = self.t + 60.0
            if any([w.tick(self) for w in self.wear]):
                self._refresh_character()
        current = self.modes.get(self.mode)
        if current and not current.step(dt):
            self.mode, current = AWAKE, None
            self._sync_projection()
        self._shooting_cues()

        # Presence only follows you when the mode allows it (sulking, sleeping and backing off don't).
        attentive = current is None or current.attentive
        pose, info = self.presence.step(dt, user_head if attentive else None)
        ch = pose.channels()

        # Notice chirp the moment it starts attending.
        attending = info["mode"] == "attend"
        if attending and not self._last_attending:
            self._sound("notice")
        self._last_attending = attending

        # Ease every mode in or out, then let each one shape the pose.
        for name, mode in self.modes.items():
            target = mode.target() if name == self.mode else 0.0
            rate = mode.ease_in if target > self._blend[name] else mode.ease_out
            self._blend[name] += (target - self._blend[name]) * min(1.0, rate * dt)
            if self._blend[name] > 0.001:
                mode.apply(ch, self._blend[name])

        for k, v in self.expr.step(dt).items():
            ch[k] += v
        ch["drive_x"], ch["drive_z"] = self.roller.x, self.roller.z
        ch["iris"] = min(1.0, max(0.0, ch["iris"]))
        ch["light"] = min(1.0, max(0.0, ch["light"]))

        shown = self.mode if self.mode != AWAKE else info["mode"]
        return Pose(**ch), {**info, "mode": shown, "expression": self.expr.name or ""}

    # ---------- what the overlay shows ----------
    def wear_state(self) -> dict:
        """Everything the MR overlay needs to show how worn in it is (R64: make relationship
        stages visible). Without a cartridge it's a fresh droid with nothing to show.

            dials      the five dials it has today, 0..1 (0.5 = out of the box)
            limit      how far wear can ever move a dial from 0.5 (D41)
            moves      a list, most used first: name, settled 0..1 (weeks), character 0..1 (years), uses
        Plain fields and lists only, because Unity's JsonUtility can't read dictionaries.
            rust       0 = in practice, up to about 0.6 after months apart (Rule 5)
            notice_m   how far away it notices you right now, in metres
            label      which droid this is, for telling two apart side by side
        """
        pat = next((w for w in self.wear if w.name == "patina"), None)
        moves = []
        if pat is not None:
            uses = pat.uses(self.today)
            moves = [{"name": m, "settled": round(pat.settle.get(m, 0.0), 3), "character": round(pat.depth.get(m, 0.0), 3),
                      "uses": round(uses.get(m, 0.0))} for m in sorted(uses, key=lambda m: -uses[m])]
        return {"learning": self.cartridge is not None,
                "label": self.label,
                "dials": {k: round(v, 3) for k, v in self.character.dials.items()},
                "limit": self.character.wear_limit,
                "moves": moves,
                "rust": round(pat.rust, 3) if pat else 0.0,
                "notice_m": round(self.presence.cfg.notice_distance, 2)}

    # ---------- self-check ----------
    def health(self) -> list[tuple[str, bool, str]]:
        """Every module that can check itself: (name, ok, message). For the future self-maintenance feature."""
        parts = [(f"mode {n}", m) for n, m in self.modes.items()] + [(f"wear {w.name}", w) for w in self.wear]
        if self.cartridge is not None:
            parts.append(("cartridge", self.cartridge))
        out = []
        for name, part in parts:
            try:
                ok, msg = part.health()
            except Exception as e:  # noqa: BLE001  a broken check is itself a problem worth showing
                ok, msg = False, f"health check failed: {e}"
            out.append((name, ok, msg))
        return out
