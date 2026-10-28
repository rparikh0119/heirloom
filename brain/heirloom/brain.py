"""Heirloom's brain core. It doesn't know any specific reaction or mode by name.

Every tick:  events -> reactions (reactions/*.json) -> modes (heirloom/modes/) -> one pose.

    awake      the default: presence runs (idle, or attending to you)
    any mode   loaded from heirloom/modes/, started and ended by reactions

To add behaviour, add a reaction file or a mode file. This file shouldn't need to change.

With a cartridge, wear plug-ins (heirloom/wear/) learn from every event and shape the character.
Without one, it behaves exactly like the out-of-the-box droid.
"""
from __future__ import annotations

from datetime import datetime

from .behavior.expressions import EXPRESSIONS, ExpressionPlayer
from .behavior.presence import Presence, PresenceConfig
from .behavior.rolling import Roller
from .body.base import Pose
from .character import load_character
from .events import Event, as_event
from .journal import Journal
from .learning import DecisionLog, RewardInterpreter
from .perception.intents import normalize
from .modes import load_modes
from .reactions import choose, load_reactions
from .sound.chirps import CHIRPS, to_wav_bytes
from .sound.tape import framed, tape
from .wear import load_wear

AWAKE = "awake"
HUH_COOLDOWN = 8.0         # seconds between "huh?"s
HUH_MAX_WORDS = 8          # it only asks "huh?" about short things. Longer ones it understands or lets go
REFLEXES = {"hearing"}     # the moment you start talking (whisper_voice), before it knows what you said


class HeirloomBrain:
    def __init__(self, play_sound, reactions_dir=None, cartridge=None, wear_ignores=(), show_photo=None,
                 play_clip=None, take_photo=None, meaning=None, learn=False) -> None:
        """play_sound(name) is called whenever the brain wants to chirp.
        show_photo(path or None) projects a journal photo, or stops (bodies without a projector skip it).
        play_clip(wav bytes) plays a voice memory through the body's speaker.
        take_photo() asks the body's camera for a picture. It comes back as a 'photo_taken' event.
        meaning: a perception.meaning.Meaning to understand sentences it has no exact words for (or None).
        cartridge: an opened Cartridge, or None to run without learning.
        wear_ignores: event sources that never leave wear, e.g. {"unity"} so test key presses don't count.
        learn: let the learning loop pick among a reaction's "choices" (needs a cartridge). Off = as designed."""
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
        self.now = None                                      # None = the computer clock. The time skip and the demo clock set it
        self.demo_clock = False                              # True when run.py --clock fakes the time of day (shown on the overlay)
        self.moment = None                                   # the moment happening right now (moments wear sets it)
        self.moments = {}                                    # every moment it knows, all layers (moments wear fills it)
        self.shyness = 0.0                                   # set by wear after time apart (Rule 5). 0 = normal
        self.habit_idle = 1.0                                # habits wear: >1 a calmer keeper, it glances around less
        self.label = ""                                      # a name for this droid on the overlay, e.g. "FRESH"
        self.show_photo = show_photo or (lambda path: None)
        self.play_clip = play_clip or (lambda wav: None)
        self.take_photo = take_photo or (lambda: None)
        self.journal = Journal.for_cartridge(cartridge)
        self.showing = None                                  # the photo being projected right now, or None
        self.roller = Roller()                               # where it has rolled to on the desk
        self.meaning = meaning
        self.vocabulary: dict[str, str] = {}                 # words it has learned (the words wear fills this)
        self._last_huh = -99.0
        self._user = None                                    # where the person was last seen (robot space)
        self._next_tick = 60.0

        # Wear: only with a cartridge. Each plug-in blends its layers into the brain.
        self.cartridge = cartridge
        self.wear = load_wear() if cartridge is not None else []
        self.wear_ignores = set(wear_ignores)
        for w in self.wear:
            w.attach(cartridge, self)
            w.apply(self)
        for w in self.wear:
            if w.name == "habits":
                w.on = learn                                 # it only watches how you move with the learning loop on
        shapers = [w for w in self.wear if hasattr(w, "restyle")]
        if shapers:                                          # habits shape every move, on top of patina
            base = self.expr.style

            def styled(move: str, base=base) -> dict:
                st = {**self.expr.PLAIN, **(base(move) if base else {})}
                for w in shapers:
                    st = w.restyle(move, st)
                return st
            self.expr.style = styled
        self._refresh_character()

        # Learning loop v0: which authored move lands (heirloom/learning, wear/responses.py)
        self.learner = next((w for w in self.wear if w.name == "responses"), None) if learn else None
        self.rewards = RewardInterpreter()
        self.decisions = DecisionLog.for_cartridge(cartridge) if self.learner else DecisionLog(None)
        self._decided: dict[str, dict] = {}                  # recent decisions by id, to learn from
        self._n_decisions = 0
        self._last_cold = -1e9
        self.estimate_odds = True                           # the time skip turns this off: no log, years of decisions
        self.last_learning: dict = {}                        # what the overlay shows about the last decision
        if self.meaning is not None:                         # learned words help it understand close variations too
            for phrase, event in self.vocabulary.items():
                self.meaning.teach(phrase, event)

    def _refresh_character(self) -> None:
        """Push the current dials into the parts that use them. Modes read them live."""
        c = self.character
        self.presence.cfg.notice_distance = c.notice_distance_when_shy(self.shyness)
        self.presence.cfg.glance_gap = c.glance_gap * self.habit_idle
        self.expr.scale = c.motion_scale

    # ---------- events ----------
    def handle(self, event: "Event | str") -> str | None:
        """React to one event. Returns the reaction file used, or None if it was ignored."""
        e = as_event(event)
        if e.name in REFLEXES:             # instant, below the level of reactions and wear
            return self._reflex(e.name)
        if e.name == "unknown":            # heard words with no exact match: learned words, then meaning
            found = self._understand(e.data.get("said", ""))
            if found:
                event, how = found
                print(f"[understood] \"{e.data.get('said', '')}\" -> {event} ({how})")
                return self.handle(Event(event, source=e.source, strength=e.strength,
                                         data={**e.data, "understood": how}))
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
        if self.learner is not None and learns:
            self._judge(e.name)
        changed = [w for w in self.wear if learns and w.record(e, self.mode, self.t)]
        for w in changed:
            w.apply(self)
        if changed:
            self._refresh_character()
        learned_now = next((w.just_learned for w in self.wear if getattr(w, "just_learned", None)), None)
        if learned_now:
            phrase, meant = learned_now
            print(f"[learned] \"{phrase}\" means {meant}")
            if self.meaning is not None:
                self.meaning.teach(phrase, meant)
        if e.name == "unknown":
            if len(normalize(e.data.get("said", "")).split()) > HUH_MAX_WORDS:
                return None                                 # a long sentence it can't place: probably not meant for it
            if self.t - self._last_huh < HUH_COOLDOWN:      # background chatter shouldn't make it ask over and over
                return None
            self._last_huh = self.t

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
        motion = r.motion
        if r.motion and r.choices and self.learner is not None and learns:
            motion = self._decide(e.name, r)
        if motion:
            self.expr.play(motion)
            worn = [w for w in self.wear if learns and w.played("motion", motion, self.t)]
            for w in worn:
                w.apply(self)
            if worn:
                self._refresh_character()
        if learned_now:
            self._sound("learned")                          # "oh! got it"
        elif r.sound:
            name = self._accent(r.sound, e.name)
            if self.learner is not None and learns and name.startswith("m:"):
                name = self._vary(name)                      # dialect drift: a slightly fresh version each time
            self._sound(name)
        if e.name == "curious" and self.roller.toward(self._user):      # beckoned: roll over to you
            self._set_mode("rolling")
        elif e.name == "go_home" and self.roller.home():
            self._set_mode("rolling")
        self._sync_projection()
        return r.file

    def sense_body(self, hands: dict | None, head=None, roll: float | None = None) -> None:
        """A new hands message from Unity (or the robot's camera later). Only the habits wear looks,
        in memory, and only with the learning loop on. Never live mimicry (proposed D90)."""
        for w in self.wear:
            if w.name == "habits":
                w.observe(self.t, hands, head, roll)

    # ---------- learning loop v0 ----------
    def _clock_now(self):
        """The time it thinks it is: the demo clock or the time skip's, else the computer's.
        None when there's a pretend date with no time of day (a time skip household without a routine)."""
        if self.now is not None:
            return self.now
        return None if self.today is not None else datetime.now()

    def _bucket(self, cue: str) -> str:
        from .wear.responses import time_of_day
        now = self._clock_now()
        return f"{cue}|{time_of_day(now.hour) if now else 'anytime'}"

    def _decide(self, cue: str, r) -> str:
        """Pick which of the reaction's authored moves to answer with, and log it (proposed D74, D79)."""
        from .wear.responses import INTRUSION, QUIET_MAX, QUIET_S
        arms = [r.motion] + [c for c in r.choices if c != r.motion]
        quiet = self.t - self._last_cold < QUIET_S
        masked = {a for a in arms if quiet and INTRUSION.get(a, 0.5) > QUIET_MAX}
        bucket = self._bucket(cue)
        self._n_decisions += 1
        did = f"d_{self._n_decisions:04d}"
        stamp = self._clock_now() or self.today
        seed = f"{self.cartridge.droid.get('id', '')}:{stamp.isoformat()}:{self._n_decisions}"
        p = self.learner.propose(bucket, r.motion, arms, masked, seed, estimate=self.estimate_odds)
        chosen = p["chosen"]
        cue_name, tod = bucket.split("|")
        self.decisions.write({"decision_id": did, "t": round(self.t, 2), "when": stamp.isoformat(),
                              "seed": seed, "context": {"cue": cue_name, "tod": tod, "mode": self.mode},
                              "candidates": arms, "masked": sorted(masked), "probs": p["probs"], "chosen": chosen,
                              "explored": p["explored"], "learner": "bucket_ts/1",
                              "layers": {k: round(v, 2) for k, v in self.cartridge.weights(self.today).items()}})
        self._decided[did] = {"bucket": bucket, "arm": chosen, "default": r.motion, "arms": arms, "t": self.t}
        if len(self._decided) > 50:
            self._decided.pop(next(iter(self._decided)))
        self.rewards.start(did, self.t)
        self.last_learning = {"line": self.learner.explain(bucket, chosen, r.motion, arms),
                              "explored": p["explored"], "reward": "", "quiet": bool(masked)}
        print(f"[learn] {did} {self.last_learning['line']}" + ("  (trying something new)" if p["explored"] else ""))
        return chosen

    def _vary(self, name: str) -> str:
        """Play a slightly varied family chirp and remember the variation, so a warm reaction
        can drift the chirp toward it (proposed D88: drift uses the same reward interpreter)."""
        dialect = next((w for w in self.wear if w.name == "dialect"), None)
        mid = name[2:]
        if dialect is None or mid not in dialect.chirps:
            return name
        o = self.rewards.open
        if o is not None and o.t == self.t and o.decision_id in self._decided:
            did = o.decision_id                              # the move it just chose for this same reaction
        else:
            self._n_decisions += 1
            did = f"c_{self._n_decisions:04d}"
            self._decided[did] = {"bucket": None, "arm": None, "t": self.t}
            self.rewards.start(did, self.t)
        seed = f"{self.cartridge.droid.get('id', '')}:{did}:{(self._clock_now() or self.today).isoformat()}"
        played, jitter = dialect.variant(mid, seed)
        self._decided[did]["chirp"] = (mid, jitter)
        self.decisions.write({"decision_id": did, "chirp": mid, "seed": seed, "jitter": {
            "pitch": round(jitter["pitch"], 4), "len": [round(x, 4) for x in jitter["len"]],
            "wobble": round(jitter["wobble"], 4)}})
        return played

    def _judge(self, event_name: str) -> None:
        """Was this event a reaction to the last move it chose? Learn from it (proposed D77)."""
        verdict = self.rewards.observe(event_name, self.t)
        if verdict is None:
            return
        did, reward, cue = verdict
        d = self._decided.get(did)
        if d is None:
            return
        if reward == 0:
            self._last_cold = self.t
        self.decisions.write({"decision_id": did, "reward": reward, "cue": cue, "delay_s": round(self.t - d["t"], 2)})
        drifted = ""
        if reward == 1 and d.get("chirp"):
            dialect = next((w for w in self.wear if w.name == "dialect"), None)
            change = dialect.nudge(*d["chirp"]) if dialect is not None else None
            if change:
                drifted = f"family chirp drifted: {change}"
                print(f"[dialect] {d['chirp'][0]} {drifted}")
        if d.get("arm") is None:                             # a chirp on its own, no move was chosen
            self.last_learning = {**self.last_learning, "reward": f"{'landed' if reward else 'missed'} ({cue})",
                                  "chirp": drifted}
            return
        self.learner.learn(d["bucket"], d["arm"], reward)
        self.last_learning = {"line": self.learner.explain(d["bucket"], d["arm"], d["default"], d["arms"]),
                              "explored": False, "reward": f"{'landed' if reward else 'missed'} ({cue})",
                              "quiet": reward == 0, "chirp": drifted}
        print(f"[learn] {did} {'landed' if reward else 'missed'} ({cue}): {self.last_learning['line']}")

    def _understand(self, said: str) -> tuple[str, str] | None:
        """Words it learned from you first, then meaning. None if it really doesn't know."""
        text = normalize(said)
        if text:
            for phrase in sorted(self.vocabulary, key=len, reverse=True):
                if f" {phrase} " in f" {text} ":
                    for w in self.wear:
                        if w.name == "words":
                            w.used(phrase)
                    return self.vocabulary[phrase], "learned"
        if self.meaning is not None and text:
            event, how_sure = self.meaning.understand(said)
            if event:
                return event, f"meaning {how_sure:.2f}"
        return None

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

    def _accent(self, sound: str, event: str) -> str:
        """During a moment (the 10 am hello), answer with the family's chirp for it (dialect wear).
        Any other time, the core chirp everyone can read."""
        moment = getattr(self, "moment", None)
        dialect = next((w for w in self.wear if w.name == "dialect"), None)
        info = (getattr(self, "moments", {}) or {}).get(moment) if moment else None
        if dialect is None or info is None or info.get("cue") != event:
            return sound
        return dialect.voice(moment, sound)

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
        self.rewards.expire(self.t)

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
        now = self.now or datetime.now()
        return {"learning": self.cartridge is not None,
                "label": self.label,
                "clock": now.strftime("%H:%M"),
                "clock_demo": self.demo_clock,
                **self._moment_state(),
                "learn_on": self.learner is not None,
                "learn_line": self.last_learning.get("line", ""),
                "learn_reward": self.last_learning.get("reward", ""),
                "learn_explore": bool(self.last_learning.get("explored")),
                "learn_chirp": self.last_learning.get("chirp", ""),
                "habits_line": next((w.describe() for w in self.wear if w.name == "habits"), ""),
                "dials": {k: round(v, 3) for k, v in self.character.dials.items()},
                "limit": self.character.wear_limit,
                "moves": moves,
                "rust": round(pat.rust, 3) if pat else 0.0,
                "notice_m": round(self.presence.cfg.notice_distance, 2)}

    def _moment_state(self) -> dict:
        """The moment part of the overlay (proposed D99, D85).
            moment         the moment happening now, e.g. "wave around 10:03", or ""
            moment_detail  one line on it: how often, since when, whose (moments.explain)
            moment_lines   the same, as short lines that fit the panel
            moment_chirp   "family chirp", "family chirp, passed down", or "" if it used the core chirp
            habits         every awake moment it knows, earliest in the day first. An old keeper's gets " · L1"
            habit_now      which of habits is happening now, or -1"""
        mom = next((w for w in self.wear if w.name == "moments"), None)
        dialect = next((w for w in self.wear if w.name == "dialect"), None)
        out = {"moment": "", "moment_detail": "", "moment_lines": [], "moment_chirp": "", "habits": [], "habit_now": -1}
        if mom is None:
            return out
        known = self.moments or {}
        active = self.cartridge.active.id
        woken = {m.get("from") for m in known.values() if m.get("from")}
        shown = [(mid, m) for mid, m in sorted(known.items(), key=lambda kv: kv[1]["at"])
                 if not m.get("dormant") and mid not in woken]          # a woken habit replaces the old keeper's copy
        out["habits"] = [(m.get("tag") or m["name"]) + ("" if m["layer"] == active else f" · {m['layer']}")
                         for _, m in shown]
        out["habit_now"] = next((i for i, (hid, _) in enumerate(shown) if hid == self.moment), -1)
        mid = self.moment
        if mid and mid in mom.known:
            m = mom.known[mid]
            out["moment"] = m.get("tag") or m["name"]
            out["moment_detail"] = mom.explain(mid)
            out["moment_lines"] = self._moment_lines(mom, m)
            rec = dialect.chirps.get(mid) if dialect is not None else None
            if rec is not None:
                out["moment_chirp"] = "family chirp, passed down" if rec.get("from") else "family chirp"
        return out

    @staticmethod
    def _moment_lines(mom, m: dict) -> list[str]:
        """Short lines for the overlay: how often, since when, whose, and where it came from."""
        from datetime import date as _date

        def keeper(lid: str) -> str:
            try:
                return f"keeper {lid} · {mom.cart.layer(lid).label}"
            except Exception:  # noqa: BLE001
                return f"keeper {lid}"

        first = _date.fromisoformat(m["first"])
        days = m["days"]
        lines = [f"seen on {days} day{'' if days == 1 else 's'} since {first:%b %Y}", keeper(m["layer"])]
        src = mom.known.get(m.get("from") or "")
        if src:
            lines.append(f"passed down from {keeper(src['layer'])}")
        return lines

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
