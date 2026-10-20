# Decision Log

One entry per real decision. **Status:** Decided · Proposed (waiting on Riya) · Revisit.

---

**D01 · Heirloom's purpose: the family journal** · Oct 15 · Decided
- Question: the robot needed a clear job (professors' feedback, "Luka lasts because it has a job").
- Choice: a desk companion that keeps the family's journal. It takes photos while you talk to it, projects them on the table, and the journal passes down with it.
- Why: class feedback (projector, photo memories) plus R10. Gives "we keep what holds our story" a mechanic.

**D02 · The shutter is never automatic** · Oct 15 · Decided
- Choice: photos only after a countdown started by a button, a hand gesture or a voice command. Iris snaps, it chirps.

**D03 · Privacy stance** · Oct 15 · Decided
- Choice: not a design concern, because everything is local. Like passing on an old camera with its card. Personality and journal are still stored as separate files, so transfer can be tested with and without photos.
- Retired: the FigJam line "inherit how, never when or where."

**D04 · The memory cartridge** · Oct 15 · Decided
- Choice: a cassette-style cartridge holds personality + journal. Plug into a new body or any computer. No app. Open formats only.
- Why: feedback (USB ports, old data storage) plus Vint Cerf's point that data must stay readable.

**D05 · Power, avoiding lithium** · Oct 16 · Revisit (D23: rolling needs onboard power)
- Choice: wall power (dock or USB-C PD), a supercapacitor for clean shutdown, optional NiMH AA pack for untethered use.
- Rejected: solar as main power (T05, needs a source). Lithium primary battery.

**D06 · Extreme modularity** · Oct 16 · Decided (details with the ID collaborator)
- Choice: snap-together modules (base, neck, head, antennas), one standard connector each, a small ID chip so the brain knows what's attached.
- Why: class feedback + R09. Matches the software's "bodies declare what they support."

**D07 · It never talks** · Oct 16 · Decided (confirmed)
- Choice: understands speech, answers only in chirps, robot noises and body language.
- Why: R01, honest-machine pillar.

**D08 · Reachy Mini is a test body, never baked in** · Oct 15 · Decided
- Choice: one brain, any body. The brain uses Heirloom's own channels and units. Robot code lives only in adapters. Unity listens to the brain, never the robot.
- Rules: docs/architecture.md

**D09 · Brain environment** · Oct 16 · Decided
- Python 3.12 venv in brain/.venv, installed with `python -m pip`. Simulator runs as `reachy-mini-daemon --sim --no-media` (the media server crashes on PC audio).

**D10 · Our own WebSocket client in Unity** · Oct 16 · Decided
- Why: NativeWebSocket clashes with Meta's Voice SDK (T06). .NET's ClientWebSocket does the same job with no dependency.

**D11 · Pose Reachy's head directly in Unity** · Oct 16 · Decided
- Choice: strip the URDF physics, re-parent the head, hide the Stewart linkage rods, measure axes from the robot root.
- Known issue: Reachy's antennas don't show (logged in open items).

**D12 · Sounds are made in the brain** · Oct 16 · Decided
- Choice: the brain synthesises chirps and streams them to whichever body is attached. One voice across Unity, the lab Reachy and the droid.

**D13 · The Wear System is Heirloom's signature** · Oct 16 · Proposed
- Choice: patina (motion), dialect (sound), rings (owner layers), memory (journal surfacing), plus a time-skip simulator.
- Waiting on: a design brief before any code.

**D14 · A fixed core temperament** · Oct 16 · Decided (became Rule 4, Oct 17)
- Choice: each droid is born with traits that never change (sass, shyness, curiosity). Wear adds flavour on top.
- Why: R02 (loyal through change, sass), R09 (stable core), avoids a people-pleaser.

**D15 · Process: brief before build, logs on FigJam** · Oct 16 · Decided
- Every feature gets a one-page brief (thesis link, research, feel, test) signed off by Riya before code.
- Logs live on the FigJam board (Riya maintains). Plain-text copies in docs/logs/.

**D16 · Rules and scenarios for the Wear System** · Oct 17 · Decided
- Seven rules every learning behaviour must follow: (1) it learns your warmth, (2) relationships, not accounts, (3) nothing is erased unless you choose, (4) the core never changes, (5) absence leaves a trace, (6) ownership changes through a ritual, (7) it isn't built to please you.
- Nine stress-test scenarios the rules must survive: owner dies, family shares one droid, sold to a stranger, split household, different bodies and abilities, different cultures, neglect, wear is fundamental, institution.
- Design target: the everyday person (never opens a settings menu, so every choice happens through the droid and its physical controls). Approach: "solve for one, extend to many" (Microsoft Inclusive Design).
- All nine scenarios are designed for. Only some are demoed this quarter, the rest are covered in spring tests and the write-up.

**D17 · Layers can't be copied** · Oct 17 · Decided
- Only one droid ever holds the wear. Journal photos can be copied. Like a family ring: one person keeps the actual ring.
- Why: two droids with one past is too confusing.

**D18 · Telling people apart through nuance** · Oct 17 · Decided (feasibility to verify)
- One household layer. Inside it, the droid learns its regulars from soft clues together: voice, height and usual position, rhythm (when they show up, how they interact). Unfamiliar people are guests.
- No face recognition. It can get you wrong and do a double-take, on purpose.
- To verify: local speaker recognition on a Pi 5 (T07).

**D19 · Neglect is part of the design** · Oct 17 · Decided
- Neglect leaves a mark: it gets shy and cautious, then recovers, faster than a new droid would warm up. It can never die.
- Why: R16 (Tamagotchi's guilt works), WALL-E alone. Unlike a Tamagotchi, an heirloom has to survive neglect.

**D20 · Rule 7: it isn't built to please you** · Oct 17 · Decided
- It has moods, preferences and opinions. It can be ignored, it can sulk a little, it can disagree.
- Why: Riya rejects the uncanny people-pleasing of AI. R02 (R2's sass). Builds on D14 (fixed core temperament).

**D21 · The hold switch is cut** · Oct 17 · Decided
- A switch that pauses wear would undercut the thesis. Keeping a droid as someone left it is already covered by resting their layer (Rule 3). Scenario 8 became "wear is fundamental."

**D22 · Core temperament = five dials, set at birth, never changed** · Oct 17 · Decided (for now)
- Curiosity (uninterested → investigates everything) · Sass (agreeable → talks back) · Boldness (shy → forward) · Energy (calm → bouncy) · Warmth speed (slow to trust → quick to bond).
- How they show up: curiosity = glance and investigate rate · sass = sulk or grumpy chirp after "not now" · boldness = notice distance · energy = motion speed and bounce · warmth speed = how fast wear builds and how long neglect-shyness lasts.
- Reference points: R2-D2 (high sass and boldness, slow warmth), WALL-E (high curiosity, shy, fast warmth), BB-8 (high energy).
- Open: is every droid born with different settings, or one designed personality? Where does the demo droid sit on each dial?

**D23 · Heirloom rolls** · Oct 18 · Decided
- Choice: the custom droid moves on wheels. Can't be tested on Reachy Mini (it doesn't roll). Hardware details with the ID collaborator.
- Consequences: needs onboard power, which **reopens D05** (no lithium, wall power). Likely direction: a charging dock it rolls off and returns to (class feedback suggested a charging station), with a NiMH or other non-lithium pack. Also needs cliff sensors, wheel motors and a wheel module.

**D24 · Quarter framing** · Oct 18 · Noted
- No fixed beautiful-corner date yet. The next assignment (likely within ~2 weeks) will be a significant progress check. Kane allows adjusting assignments to the project and encourages heavy research for the rest of the quarter alongside the build.

**D25 · Talk and Gesture v0: design brief** · Oct 18 · Decided
- Goal: Heirloom reacts to real hands and voice instead of keys 1–6.
- Voice lives in the brain (Python, laptop mic for now), so it moves to the robot's own mics in winter without changes. Gestures come from Quest hand tracking in Unity and arrive as the same events.
- Gestures: wave → hello · thumbs up → good · palm out → not now · beckon → curious · middle finger → offended.
- Voice is built on intents, with several everyday phrases per intent (see brain/heirloom/perception/intents.py). Offline Vosk, limited to that phrase list (T08). Meta's Voice SDK ruled out because it sends audio to the cloud (Wit.ai).
- Path to intuitive: v0 fixed phrases → v1 hears every word and matches loosely → v2 learns the owner's own words (a Wear System feature).
- Out of scope for v0: conversation, LLMs, telling people apart, any learning.

**D26 · It can be offended** · Oct 18 · Decided
- Middle finger (or key 7) → recoils, grumbles, turns its back for about 6 s, half turns to peek, then forgives. Doing it again restarts the sulk. Saying "sorry" ends it early. While sulking it ignores everything else.
- Why: Rule 7 (D20). A robot with a backbone reads as a character. R2-D2's sass (R02).
- Open: does it hold a grudge over time (Wear System)?

**D27 · Wake word "Heirloom"** · Oct 18 · Decided (placeholder)
- It only listens for about 5 s after hearing its name, or takes "Heirloom, good job" in one breath. Stops it reacting to every stray "no" in the room.
- Placeholder until the naming question is answered. Strong candidate: the owner names it and that name becomes the wake word (ties to R12, Roomba naming).

**D28 · Gestures are read in the brain** · Oct 18 · Decided (changes D25)
- Unity streams 26 hand joints per hand (XR Hands, 30 Hz) in robot space. The brain spots gestures from finger straightness, palm direction and motion (brain/heirloom/perception/gestures.py).
- Why: one brain, any body. In winter the robot's camera can give the same hand points (MediaPipe), and the gesture code carries over unchanged. It also avoids swapping in Meta's Interaction Rig, which only exists on Quest. Riya chose to build it from scratch.
- Gestures fire once per hold (let go to repeat). Wave is checked before palm-out, so a waving hand isn't read as "stop".

**D29 · Heart → love** · Oct 18 · Decided
- Both hands make a heart (index tips touching on top, thumb tips touching below), or say "Heirloom, I love you", or key 0. It tilts its head shyly, sways its antennas, and its light beats twice like a heart, with a soft warm coo.
- First two-hand gesture. While both hands form a heart, single-hand gestures are ignored.
- Open: in the Wear System, does affection count for more than a thumbs up?

**Beckon tuning** · Oct 18
- First real-hand test: every gesture read well except beckon. Real beckons only hook the index partway, so fixed curl thresholds missed them, and opening and closing a palm-up hand caused false triggers. Now it counts relative dips in index straightness (2+ in 2.5 s), with the palm staying up and the hand held still.
- Update: a heart also ends a sulk (it melts). Thumbs up and wave are still ignored while it sulks. Riya: the sulk is still the favourite reaction, "so expressive and funny".

**D30 · No large language model** · Oct 18 · Decided
- Heirloom's understanding is built from its own parts (speech recognition, small meaning matching, its learning loop), never an LLM. Keeps it organic, local, and away from people-pleasing chatbot behaviour. Also keeps it clearly separate from AugTwins.

**D31 · A companion, not a pet** · Oct 18 · Decided
- It learns by association (the way animals do), but its character is a companion with its own opinions: R2-D2, WALL-E, Bumblebee. No dog or pet framing in behaviour or language.

**D32 · Tone of voice is read, alongside words** · Oct 18 · Decided (scope to define)
- Loudness, pitch and pace work in tandem with words and gestures, the way voice and hands already do.
- Proposed guard: it reacts to tone (soft, loud, fast, flat) but never names an emotion ("you seem sad"). Keeps it honest and consistent with "physical cues only".

**D33 · Voice memories** · Oct 18 · Proposed
- "Heirloom, record this" captures the owner's voice (a recipe, a message). It replays only that recording, through a slightly mechanical, tape-like filter. It never speaks for itself and never makes new words in anyone's voice.
- Pairs with the photo journal: a photo and its sound, projected and played together.
- Why: R17 (Bumblebee), R18 (Build-A-Bear), "we keep what holds our story". The real line from AugTwins: they synthesise new speech from a person, Heirloom only replays what was really said.
- Open: how recordings are named and found without full speech recognition, whether it ever uses clips to respond (Bumblebee-style), grief safeguards (only on request, never a surprise).

**D34 · Modular brain: reactions as files, modes as plug-ins** · Oct 18 · Decided, step 1 built
- Reactions are JSON files in brain/reactions/ (no code). Behaviour over time (sulk, sleep, back off, listening) is a mode plug-in in heirloom/modes/. The core brain names nothing specific. Events now carry their source and data.
- Missing body parts are skipped silently. Later feature instead: **self-maintenance**, Heirloom indicates when something isn't working (ties to Jibo/Vector/Moxie dying and the visible-repairs look). Every module gets a health() hook now.
- See docs/modularity-brief.md.

**D35 · Gestures are plug-ins** · Oct 19 · Decided, built
- Each gesture is one file in heirloom/perception/gestures/ (thumbs_up, middle_finger, palm_out, wave, beckon, heart). Shared hand maths in hand.py, motion history in memory.py, holding and cooldowns handled once in the detector.
- Gestures receive the person's head position, so face-relative gestures work (shh = finger to lips).
- Modes can be silent (no chirps). First use: a "quiet" mode after shh.
- Riya writes shh.py as her first Python module.

**D36 · Expressions are files, made with a pose recorder** · Oct 19 · Built
- Every expression is a JSON file of keyframes in brain/expressions/. The brain checks them on startup, like reactions.
- PoseRecorder.cs in Unity: pose Reachy with sliders, capture keyframes (K), play back (P), save (Enter). Riya animates Heirloom's mannerisms directly, no code.
