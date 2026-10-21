# Heirloom · Session Handoff (Oct 16 to Oct 20, 2026)

Read this first in a new chat. It covers everything since the Oct 15 handoff: the new repo, the brain, the headset test, voice, gestures, the modular refactor, character dials, and hardware.

---

## 1. Who and how

**Riya Parikh** (RP.Studiio). SCAD BFA Immersive Reality, Applied AI minor, graduating May 2027. Professor: Kane Tyler Garrett (ARVR 455). Collaborating with an industrial design student on the droid's form.

**How Riya wants to work (learned this session):**
- Concise, direct, personality-driven. No em dashes, no semicolons, no performative framing, no "it's this, not that."
- Push back with reasons. Verify research and flag uncertain facts.
- Design brief before each feature. Log decisions and research. Logs live on her FigJam board (she copies them), plain-text copies in `E:\HEIRLOOM\docs\logs\`. Don't crowd the claude.ai Project with docs.
- **Never tell her to stop or take a break, or decide for her that a session is done.** She says when she's done.
- Don't overwhelm: one clear step at a time, say which files to ignore.
- She learns by seeing: show the **full** code, not fill-in-the-blanks. When she says "just do it" (tired, no coffee, indentation fights), do it directly.
- **Character motion: she directs, Claude animates.** She gives notes on feel, Claude writes the keyframes, she reviews in Unity. She doesn't want to hand-animate or hand-write reaction files routinely.
- Sometimes no headset and no mic (music playing). Offer laptop-only work then.
- Remind her to commit regularly with `git add -A`.

---

## 2. The project in one paragraph

**Heirloom** is a small modular desk companion droid, kept for decades and passed down. It keeps the family's journal (photos on trigger, projected on the table), records and replays voice memories, learns locally, never speaks in its own human voice (chirps and body language only), and stores everything it learns on a memory cartridge. Core question: when a droid is passed to someone new, does what it learned come with it? Look: used-future cassette futurism (Braun, vintage Sony), cream and oxblood enamel over brushed aluminum, aperture eye, antennas, rolls on wheels, no screen, no arms or legs. Character references: R2-D2, WALL-E, Bumblebee, BB-8. A companion, not a pet.

---

## 3. Where everything lives

- **Repo:** `E:\HEIRLOOM` (GitHub: github.com/rparikh0119/heirloom, Git LFS on). The old `E:\Capstone` is the archived project.
- **Drive:** RiyaSSD (E:) is exFAT and external. It threw a "scan the drive" warning on Oct 19 (unplugged without ejecting). Scan passed, nothing lost. Always Safely Remove, always push at the end of a session.
- **Laptop:** Windows, Intel + NVIDIA RTX hybrid, 63 GB RAM. Quest 3 over Meta Horizon Link (cable). Left controller not connecting (battery or re-pair), not needed, hand tracking works.

```
E:\HEIRLOOM
├─ brain\                     Python brain (venv in brain\.venv, Python 3.12)
│  ├─ character.json          the 5 temperament dials (all 0.5 out of the box)
│  ├─ reactions\*.json        what it does for each event (Riya wrote most of these)
│  ├─ expressions\*.json      keyframed motions (happy, love, offended, yawn...)
│  ├─ heirloom\
│  │  ├─ brain.py             core: names no specific reaction or mode
│  │  ├─ events.py            Event(name, source, strength, data)
│  │  ├─ reactions.py         loads + validates reaction files
│  │  ├─ character.py         loads dials, maps them to behaviour
│  │  ├─ modes\               sulk, sleep, back_off, listening, quiet (plug-ins)
│  │  ├─ behavior\            presence.py (breathe, notice, look), expressions.py
│  │  ├─ perception\          voice.py (Vosk), intents.py (phrases), gestures\ (plug-ins)
│  │  ├─ sound\chirps.py      procedural R2-style chirps
│  │  ├─ body\                NullBody, UnityBody, ReachyBody, MultiBody ("+")
│  │  └─ link\server.py       WebSocket server, port 8765
│  ├─ scripts\run.py          main loop
│  ├─ scripts\voice_test.py   test voice alone
│  └─ tests\                  test_reactions.py, test_gestures.py, test_shh.py
├─ unity\HeirloomMR\          Unity 6.3 LTS URP, Meta XR SDK 207, OpenXR
│  └─ Assets\Heirloom\Scripts\  ReachyRig, HeirloomLink, HandStream, PoseRecorder,
│                               KeyboardEvents, StateOverlay, Channels, WavUtility
└─ docs\
   ├─ architecture.md, modularity-brief.md, wear-system.md, cartridge-format.md
   ├─ hardware\Heirloom-Hardware-Breakdown.xlsx
   └─ logs\ decision-log.md (D01 to D39), research-log.md (R01 to R18, T01 to T10),
            session-log.md, open-items.md
```

---

## 4. How to run it

```
cd E:\HEIRLOOM\brain
.venv\Scripts\activate
python scripts\run.py --body unity                  # keys only
python scripts\run.py --body unity --voice          # + voice (laptop mic)
python scripts\run.py --body unity --gesture-debug  # + finger readout for tuning
```
Then press Play in Unity (scene `Presence`), click the Game view.

- **Keys:** 1 wave · 2 good · 3 not now · 4 sleep (yawns) · 5 wake · 6 curious · 7 offended · 8 scold · 9 sorry · 0 heart
- **Voice:** say "Heirloom" first (5 s listening window) or in one breath: "Heirloom, good job". Phrases in `perception\intents.py`.
- **Gestures (headset):** thumbs up = good · palm out (still) = not now · wave = hello · beckon (palm up, index curls twice) = curious · middle finger = offended · heart (both hands) = love · finger to lips = shh (quiet)
- **Tests:** `python tests\test_reactions.py` (all reactions + scenario) · `python tests\test_gestures.py` · `python tests\test_shh.py`
- **Headset:** Meta Horizon Link app → Beta: Developer Runtime Features + Passthrough over Link on. Quest Quick Settings → Link. BrainLink's User Head field empty (uses headset camera).
- **Pose recorder (Unity):** Pose Recorder component on the robot → tick Recording → drag ReachyRig Preview Pose sliders → K capture, P play, Backspace undo, N clear, Enter save to `brain\expressions\<name>.json`.

---

## 5. Architecture (short)

```
SENSES (voice, hands, keys, later camera, touch, mute switch)
  -> EVENTS {name, source, strength, data}
  -> REACTIONS (reactions/*.json: motion, sound, mode, only_while, works_while, ignored_while)
  -> MODES (sulk, sleep, back_off, listening, quiet: timers, poses, silent, attentive, blocks)
  -> PRESENCE + EXPRESSIONS, scaled by CHARACTER dials -> one pose per tick
  -> BODY (Unity now, Reachy sim/lab robot in winter, custom droid later)
```
Rules: robot SDKs only inside body adapters. The core names nothing specific, behaviour is added as files. Senses only measure, the brain interprets (Unity streams 26 hand joints per hand in robot space, voice is heard in Python), so it all moves to the robot's own camera and mics in winter. Every module has a `health()` hook for future self-maintenance. Learned values go in the cartridge, never in module files.

Link protocol (port 8765): brain → Unity `pose`, `state`, `sound` (WAV base64). Unity → brain `user` (head xyz), `event`, `hands` (26 joints x 2, OpenXR order). Robot space: from the robot's head at rest, x right, y up, z toward the person.

---

## 6. What happened, day by day

**Oct 16:** New repo, Unity + Meta XR + OpenXR, Reachy URDF imported and posed directly, brain ↔ Unity link, presence (notice within 2.5 m, look, glance), state overlay, keyboard reactions, chirps. Class feedback: extremely modular, charging station or solar, no lithium (later reversed), understands speech but answers in chirps and motion.

**Oct 17:** Course correction: too much table-stakes behaviour, lost the core idea. Wear System designed (7 rules, 9 scenarios, behaviour tree, 5 temperament dials). Concept sketches. Hardware doesn't fit 18 cm, so the target is 25 to 30 cm, stacked modules with a twist-lock "lens mount" collar.

**Oct 18:** Devlogs (pivot post, Reachy video post). First headset test over Link: Reachy on her real desk in MR, hands tracked, slightly sunk into the desk (since fixed). Voice v0 (offline Vosk, wake word "Heirloom"). New reactions: scold, offended/sulk (her favourite), listening perk-up, heart/love, all modes eased. Brain-side gestures from hand joints (her choice to build from scratch). Beckon retuned from real data. Heart ends a sulk. Modular refactor step 1: reactions as JSON (she wrote 8 of 12), modes as plug-ins.

**Oct 19:** Drive scare, fine. Step 2: gestures as plug-ins, Riya's first Python module `shh.py` (6/6 tests), quiet mode (silent), voice "be quiet". Step 3: expressions as JSON, pose recorder in Unity, yawn added to sleep ("perfect, so cute"). Step 4: character dials. Big ideas logged: no LLM, companion not pet, tone of voice, voice memories, Bumblebee, Build-A-Bear, self-maintenance.

**Oct 20:** Hardware research and a single plain spreadsheet. Rechargeable lithium allowed. Devlog reflection drafted.

---

## 7. Key decisions (full list in docs/logs/decision-log.md)

- **D23** Heirloom rolls (wheels, dock, cliff sensors).
- **D25** Talk and Gesture v0: voice in the brain (laptop mic now, robot mics later), gestures as events.
- **D26** It can be offended: middle finger → recoil, grumble, back turned ~6 s, peek, forgive. Open: does it hold a grudge?
- **D27** Wake word "Heirloom" (placeholder, owner-naming likely later).
- **D28** Gestures read in the brain from hand joints (works with MediaPipe later).
- **D29** Heart → love (shy tilt, light beats like a heartbeat). Heart also ends a sulk.
- **D30** No large language model. Organic, local.
- **D31** A companion, not a pet. Learns by association, has its own opinions.
- **D32** Tone of voice read alongside words. Guard: react to tone, never name an emotion.
- **D33** Voice memories (proposed): "Heirloom, record this", replays only real recordings through a tape-like filter, never generates speech. Pairs with projected photos. Grief safeguard: only on request. Clear line from AugTwins.
- **D34** Modular brain: reactions as files, modes as plug-ins. Missing body parts skipped silently, self-maintenance indicator later.
- **D35** Gestures as plug-ins, gestures get head position, silent modes.
- **D36** Expressions as files + pose recorder.
- **D37** Same character out of the box, wears in with the owner within a limit (revises D14/D22). Not a blank mirror (would break Rule 7).
- **D38** Body differences to plan for: aperture eye, rolling drive channels, unknown antenna count, keep expressions body-agnostic.
- **D39** Rechargeable lithium allowed. Battery = the one part designed to be replaced.

Character dials today (0.5 = original behaviour): sass → sulk 3 to 9 s, boldness → notice 1.5 to 3.5 m, energy → expression size and speed 0.7 to 1.3x, curiosity → glance rate, warmth_speed → waits for the Wear System.

---

## 8. Hardware (docs/hardware/Heirloom-Hardware-Breakdown.xlsx, one plain sheet)

- **Buy list ~$468**, plus ~$43 to check in the lab first. Projector not included (TI shows no price).
- **School cabinet:** CanaKit Pi 5 set, a box of sensors, a full Arduino starter kit. Likely covers micro servo, L293D motor driver, buttons, switch, knob, touch module, maybe IR sensors usable as cliff sensors. Photo the kits to confirm.
- **Power:** Geekworm X1202 UPS HAT for Pi 5 ($51) + 4 x 18650 cells, ~40 Wh, ~2.4 h off the dock by first estimate. Separate 5 V rail for motors.
- **Findings:** 1080p TI projector (DLPDLCR230NPEVM, 100 lm) documented for Pi 4 only and uses most GPIO pins. DLP2000 verified: 640 x 360, 30 lm, 54 x 76 mm. ReSpeaker XVF3800 board is 108 x 108 mm (body mount or Flex version). XL330 servo fits antennas, STS3215 doesn't. N20 encoder motors ~$15 each.
- Ask the SCAD robotics department for spare servos, sensors, motor drivers.

---

## 9. Next up

**Build (modular plan step 5 and beyond):**
- Voice memories capability (D33): record, tape filter, replay, attach to photos. Needs the mic.
- Tone-of-voice sense (D32).
- v1 meaning: hear every word, match meaning (small local model like MiniLM).
- MR overlay showing attention and learning (quarter plan).
- Week 9: transfer between two virtual Reachys. Week 10: playable POC, 3-person playtest, demo video.

**Design (blocking learning, week 8):**
- Wear System risks R-1 to R-8. Claude's proposed answers were offered on Oct 19, Riya hasn't reacted yet: R-1 invisible wear (MR overlay + motion), R-2 people-pleaser (solved by D37), R-3 unpredictability (small capped drift), R-4 creepiness (rhythms not content, all local), R-5 neglect guilt (shy not pleading), R-6 grief ambush (on request only), R-7 untestable in a quarter (time-skip simulator), R-8 scope (dials + time skip this quarter).
- Also open: handoff ritual, warm response per channel, memory surfacing rarity, wear permanence, grudges, naming, heart weight, how to find voice memories.

**Research:** Leite et al. 2013 (novelty effect), Hill et al. 1992 (edit/read wear), Hallnäs & Redström 2001 (slow technology), Odom, robot personality. Verify Roomba naming, aibo funerals, Tamagotchi, Bumblebee (better source), emotion-from-voice science, Pi 5 + projector.

**Hardware:** photo the lab kits, projector price and Pi 5 support, servo count with the ID collaborator, packaging block-out at real size, power wiring in winter.

**Class:** next assignment (progress check, ~2 weeks from Oct 18), deck speaker notes slides 8, 11, 13, FigJam catch-up D25 to D39, devlogs.

**Devlog reflection posted option (Oct 18 video thread):** "Reflection: those reactions were triggered by keys, so it wasn't really listening yet. Now it hears its name and reads my hands, all on my own machine. Struggles: a new stack, a package clash, and moving too fast. Next time: design brief first, then build."
