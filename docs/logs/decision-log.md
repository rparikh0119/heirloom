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
