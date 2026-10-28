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

**D37 · Same character out of the box, wears in with you** · Oct 19 · Decided (revises D14 and D22)
- Every Heirloom starts with the same character: all five dials at a modest middle (brain/character.json). One designed personality, not born different.
- Fixed forever: what it can do and what it values (it can sulk, get shy, it won't just please you).
- Wears in: the dials drift with how the owner lives with it, within a limit (wear_limit 0.25). Two owners end up with two different droids from the same canvas.
- Why: Riya wants a blank-canvas start that builds with the owner. Pure blank was rejected because a personality made only from the owner is a mirror, which breaks Rule 7, and is dull on day one (novelty effect).
- Built: the dials now drive behaviour. Sass = sulk length, boldness = notice distance, energy = size and speed of expressions, curiosity = how often it glances around. Warmth speed waits for the Wear System.

**D38 · Body differences to plan for (no build yet)** · Oct 19 · Noted
- The custom droid has an aperture eye (the iris channel already covers it), rolls (needs drive channels: forward/back and turn, beyond base_yaw), and an unknown number of antennas.
- Expressions should stay body-agnostic: e.g. antennas expressed as intent (up/down, spread) that each body spreads over however many it has. Settle once the form is set with the ID collaborator.

**D39 · Rechargeable lithium allowed** · Oct 20 · Decided (reopens D05)
- Rechargeable lithium cells are allowed (Geekworm X1202 UPS HAT + 4 x 18650, ~40 Wh, ~2.4 h off the dock by first estimate). The battery is the one part designed to be replaced. See docs/hardware/Heirloom-Hardware-Breakdown.xlsx.

**D40 · Wear shows without the headset (R-1)** · Oct 20 · Decided
- Patina in motion, dialect in chirps, and recognising its regulars. The MR overlay is the lens for the demo and debugging, never the only place wear shows.
- Wear is the answer to the novelty effect.
- Research: Hill et al. 1992 (edit wear / read wear), Li 2016 via Yang et al. 2023 review (people respond to personalization they notice), Leite et al. 2013 and Leite PhD (novelty fades, memory and incremental novelty sustain).

**D41 · Praise can't pass the dial limits (R-2)** · Oct 20 · Decided
- Rewards soften temperament only within wear_limit. A sassy droid stays a little sassy.
- Research: De Freitas (HBS), companion apps manipulate in ~37% of farewells to keep engagement. The people-pleaser failure mode.

**D42 · Predictable what, variable how (R-3)** · Oct 20 · Decided
- The same input always gets the same kind of reaction. The style of that reaction wears in and keeps a little randomness.
- Research: Hancock et al. 2011 meta-analysis (robot performance r = +0.34 with trust, robot attributes r = +0.03). Sung et al. 2007: Roomba owners read random movement as personality, 21 of 30 named theirs.

**D43 · Rhythms by default, content only on request (R-4)** · Oct 20 · Decided (clarifies D33)
- By default it learns rhythms only (when you're around, what lands warmly). Voice memories and photos are saved only when asked, with a clear sign while recording, a hardware mute that cuts the mics, and nothing leaving the cartridge. Guests leave no wear.
- Research: MIT Technology Review 2022, Roomba test-unit photos leaked via data-labelling gig workers, one person consenting for a whole home.

**D44 · No guilt (R-5)** · Oct 20 · Decided
- It never reacts to you leaving. Shyness on return is short, fixed and cautious, with no sad sounds.
- Research: De Freitas (HBS), guilt tactics raise engagement up to 14x but cause anger and churn. Pollmann et al. 2023 (via Yang et al. 2023) warn against robot "guilt trips".

**D45 · Memories can be retired (R-6)** · Oct 20 · Decided
- Rested layers surface only on request. "Not now" during a memory retires that memory for good. No settings menu.
- Research: Facebook Memories research 2017 ("contamination sequences", filters by people and dates), Massimi 2013 (mementos can dredge up pain, limit availability).

**D46 · Time skip with household profiles (R-7)** · Oct 20 · Decided
- The simulator runs 2 or 3 synthetic homes (e.g. quiet solo owner, loud family) so worn droids differ. The write-up labels the wear as simulated.
- Research: Sung et al. via Leite PhD, about 2 months to stable use patterns. No quarter playtest can show real wear.

**D47 · Full Wear System across weeks 8 and 9 (R-8)** · Oct 20 · Decided
- Cartridge layers, patina, dialect, time-skip simulator, rings overlay, handoff and transfer. Journal photos preloaded and shown on the desk in MR. Live photo capture waits for winter.
- Cut order if behind: rings polish, then dialect. Patina and transfer are not cuttable.

**D48 · Warm response v0** · Oct 20 · Decided
- Warm: thumbs up, heart, a wave back, staying close. Cold: "not now", walking away.

**D49 · Dials wear: treated badly, it gets grumpier** · Oct 21 · Decided, built
- Being offended or scolded nudges sass up. Making up during a sulk (heart, sorry) nudges it down. Riya: grumpier "shows character and charm" (Rule 7). The alternative, getting more cautious (boldness down), was rejected.
- Other nudges: wave = bolder, "not now" = less bold and calmer, shh = calmer, praise after a big reaction = more energy, praise after curious = more curious. Warmth speed stays fixed for now.
- One step = 0.001, capped at wear_limit 0.25 per layer and in total (D41). Rules live in brain/wear/dials.json, code in heirloom/wear/dials.py.
- Gaps: boldness up should come from "stayed close" and curiosity down from "ignored its glances". Both need presence events first.

**D50 · Dials settle toward the balance of how it's treated** · Oct 22 · Decided, built
- Each nudge moves a dial a fraction of the way toward the limit in its direction. Fast at first, slower over time, and it lands where the balance of warm and cold moments puts it. Never passes wear_limit (D41).
- Why: fixed steps raced every dial to the cap within a year (time skip, Oct 21). Pleo lost families because growth was invisible (Fernaeus et al. 2010, R44), so early change has to be noticeable.
- Design rule for Heirloom's behaviour, not a claim about people.

**D51 · Time skip: no number without a source** · Oct 22 · Decided, built (supersedes prep/oct22 households)
- Every number in a household is declared as data (with the arithmetic from the paper), unknown (a range bounded by what is known, swept) or scenario (the mix of moments). The loader refuses undeclared numbers. Riya: "assumed" claims look credible and aren't, so they're not allowed.
- `--sweep 30` runs the whole range of every unknown. Only results that hold across it may be claimed, and only as "in a home where...". The worn cartridge records every value used.
- Four households: quiet solo, loud family, enthusiast, shelved. Sources: Bentley 2018, Cagiltay 2022, Weiss 2021, Bajones 2019, Zhao & McEwen 2025, Kertész & Turunen 2017, Shen & Guan 2025. See docs/time-skip-provenance.md.
- First sweep: homes end up with distinct characters, wear keeps changing after year 1, dial changes alone are too small to see (→ D55), shelved droids freeze (Rule 5 missing), curiosity only climbs.

**D52 · Positioning** · Oct 23 · Decided
- Main line: "Every companion robot today either remembers you and stays, or moves to a new home and forgets. Heirloom remembers when it changes hands."
- Tagline: "Built to be inherited."
- Why: LOVOT, RoBoHoN and aibo already move memory into a new body for the same owner. Sony erases aibo memory before rehoming, LOVOT's memory ends with its subscription (R43, R47, R48, R49, R50). Name them as precedent. Say "as far as we found", never "no one does this".

**D53 · Two-key handoff** · Oct 23 · Decided
- The giver's key: over the years the owner marks moments "pass on" or "keep with me". At a handoff only "pass on" moments travel. After a death, the marks act as their will (katamiwake).
- The receiver's key: for each past owner, carry, soften or let rest (keep / blend / fade in code).
- Why: Sony erases aibo memory to protect the previous owner. Heirloom has to protect them without erasing. Fits D43 (content only on request) and D45 (grief on request).
- Build: a "pass on" flag on journal entries in the cartridge. The marking gesture is part of the handoff ritual brief.

**D54 · Scenario 10: passing it down while alive** · Oct 23 · Decided
- A grandparent hands the droid to a grandchild. "The Introduction": when the old owner is present and warm toward the newcomer, the droid warms to them faster.
- Why: Shen & Guan 2025 saw grandparents hand their robot to grandchildren (R61). Design hypothesis for the mechanic, not research.

**D55 · Patina carries the fresh vs worn demo** · Oct 23 · Decided
- The dials stay subtle (Rule 4). Patina (motion that wears in) becomes the top build for weeks 7 to 8.
- Why: the D51 sweep shows the largest dial change is a sulk going from 6.0 s to 6.9 s, too small to see. Kertész & Turunen (R45) and Fernaeus et al. (R44): wear must be felt in the interaction.

**D56 · Weak-robot boundary** · Oct 23 · Decided
- Hesitation and wobble are fresh-droid traits that fade with wear. It may invite help once, never repeats the request, never sulks if ignored.
- Why: Okada's weak robots (R51) invite people in. Guilt tactics backfire (R26, R39, D44).

**D57 · Pillar revisions** · Oct 23 · Decided
- Luka: "lasts because it has a job" → "robots last when they become part of the family's story" (R10, R47, R61).
- New "why now": China's July 2026 rules ban dependence-building companion AI (R58). Pew 2026 privacy concern (R33).
- Honest machines + Mori 1970 (R65), Okada (R51), NICOBO (R52), Qian 2026 (R60). Story + wenwan (R54), A-FUN scratches (R43), aibo funerals (R46), Roomba naming (R22). Companies die + LOVOT cancel erases memory (R47), Moxie twice (R63), Sony's 7-year window (R43). Trust + Hancock 2011 (R21), Scassellati's "day two" (R63).

**D58 · Wake word stays for now** · Oct 23 · Decided
- "Heirloom" stays the voice gate. It filters a loud playtest room. Revisit with owner naming. NICOBO shows a companion can skip one (R52).

**D59 · Patina built (first draft)** · Oct 23 · Built, needs tuning
- Every expression counts its own uses in the cartridge. Wear per move: w = 1 - exp(-uses / 40). A fresh move pauses about 0.35 s, wobbles, plays stiff and small. A worn move starts instantly, plays faster, bigger and eased.
- Measured in code: fresh hello 1.6 s with a 0.4 s pause. After 300 waves: 0.87 s, no pause, about 30% bigger.
- Every value in brain/wear/patina.json is a design draft by Claude, not research. Riya tunes it by feel in the headset.
- Open design call: at 40 uses a family's hello is fully worn inside year 1, so year 1 and year 12 look alike. Options: a slow second layer that keeps deepening over years, or a much larger uses_to_wear.

**D60 · Patina v2: lived-in, a home's own, never repeats, rusts** · Oct 23 · Built, needs tuning
- Checked patina v1 against the Oct 21 research. Three conflicts fixed:
  - Worn was machine-perfect (no wobble, fully smooth). Okada (R51): slight unsteadiness reads as alive, people stop forgiving high-function robots. Worn now keeps a little wobble and isn't fully eased.
  - Every home wore toward the same style. 経年変化 (R67) and wenwan (R54): the same material ends up different with different use. A slow second layer, "character", gives the most-used moves the home's dials: boldness leans in, curiosity tilts the head, sass flicks the antennas, energy changes size and speed. depth = 1 - exp(-uses / 2500).
  - Worn moves repeated exactly. Hyodol returners cited repetition (R59). Speed and size now vary up to 6% per play.
- Rule 5 now has code: after 7 days without a moment, settling slips back (up to 60% at 90 days). Each move loosens it by 40%. Rust comes from the date of the last moment and is never stored. Fixes the frozen shelved droid (R61).
- Time skip (10 runs, conditional on the mix scenario): family hello character 0.20-0.39 at year 1, 0.77-0.99 at year 12. Quiet owner 0.12-0.14 at year 1, 0.43-0.74 at year 12. Shelved rust 0.60. Year 1 and year 12 now differ.
- Measured, one run: fresh hello 1.63 s with a 0.35 s pause. Family year 12: 0.87 s, no pause, leans +7 deg, tilts +9 deg, antenna flick +17 deg. Quiet year 12: 1.03 s, smaller, mostly a head tilt.
- Rust also makes it shy (Riya, Oct 23): notice distance slides toward the shyest droid's by the rust amount. Back after 90 days, a default droid notices you at about 1.9 m instead of 2.5 m, and it's back to normal after about 5 moments. Checked about once a minute, so a droid left running alone still gets shy.
- Bug fixed: time-skip snapshots now end today, so a year-1 cartridge doesn't open rusty.
- Every number in brain/wear/patina.json is a design draft by Claude. Mapping dials to lean, tilt and flick is a design call, not a finding.

**D61 · No wake word when it has noticed you** · Oct 23 · Built, Riya to confirm
- Up close (inside notice distance) commands work without "Heirloom". From further away the name is still needed, so a loud room stays out. Replaces the always-on wake word in D58.
- Why: Riya in the headset, Oct 23: "it can't even understand hi". Saying a name before "hi" to something already looking at you feels wrong. Being close and in view is how you address it, consistent with reading body language. NICOBO has no wake word (R52).
- Voice also reacts while you're still talking when the phrase can't mean anything else ("hi" in about 0.2 s). Phrases that start another command ("good" → "good night", "no" → "not now") wait for the pause. Mic read every 0.1 s instead of 0.25 s. Vosk 0.3.45 has no setting for the end-of-sentence silence, checked against the package.

**D62 · Fresh end of patina made bigger** · Oct 23 · Tuning
- Headset, Oct 23: Riya couldn't see the fresh vs worn difference. Fresh pause 0.35 → 0.7 s, wobble 1.5 → 4 deg, speed 0.9 → 0.7, size 0.85 → 0.65. A fresh hello now pauses about 0.8 s and runs 2.4 s, peak about 26 deg vs 44 deg worn. Still design values.

**D63 · Whisper replaces Vosk as the default voice** · Oct 23 · Built, needs a real test
- Riya: "This thing is supposed to understand me." Vosk small (about 40 MB) restricted to about 40 phrases missed even "hi".
- faster-whisper 1.2.1 (CTranslate2), base.en, int8 on the CPU, local only. Checked against the project README: small model int8 on 8 threads did 13 min of audio in 1 m 42 s, so a short phrase should take a fraction of a second. Not measured on Riya's PC yet. The model couldn't be downloaded in Claude's workspace (Hugging Face blocked), so real accuracy is untested.
- A loudness gate cuts each sentence (ends 0.35 s after you stop). Whisper gets a prompt and the hotword "Heirloom". Loose matching adds everyday phrasings (intents.EXTRA) and spellings of the name.
- Low-confidence results are dropped (Whisper's no-speech rule plus avg_logprob below -1.2), because Whisper is known to hear "thank you" in noise, which here would be praise.
- Vosk stays available: --voice-engine vosk. Bigger model if needed: --voice-model small.en.

**D64 · No wake word by default** · Oct 23 · Decided (Riya)
- Riya: having to say "Heirloom" before every word is annoying. Whisper heard every phrase correctly in the Oct 23 test (about 0.4 s each), so the name isn't needed to avoid mishearing.
- Default: just talk. --need-name brings back D61 (name needed from further away) for loud rooms like zoo stations. Supersedes D58.

**D65 · Palm-out ("not now") tightened** · Oct 25 · Built, needs a headset check
- It fired in every Oct 23 log when Riya didn't mean it, knocking the droid into giving her space.
- Now: fingers pointing up (a stop sign), palm facing the robot more squarely (0.75, was 0.6), hand more than 20 cm from its head (so petting doesn't count), held 0.6 s (was 0.3). Petting and a hand close to its face both fired under the old rule and don't now (synthetic hands, checked).

**D66 · "I hear you" reflex** · Oct 25 · Built
- The moment you start talking, the antennas lift a little, about 0.75 s before Whisper has understood you. Not while asleep or sulking.
- A reflex skips reactions and patina: instant even on a fresh droid, never counted as a practised move.

**D67 · Journal projection prototype (MR)** · Oct 25 · Built, needs a headset check
- Riya: prototype moving, photo taking, audio recording and projection. Order: projection, photo, voice memories, moving. Pulls the week 9 Journal plan forward (Oct 16), partly reverses D47 (live capture waited for winter).
- "Show me a memory" / "what do you remember": soft remember chirp, head tilts down and holds still, a light cone from the head and a journal photo on the real desk, about 9 s. Only on request (D45). "Not now" during it stops quietly and retires that photo (journal/retired.json).
- Photos live in <cartridge>/journal/ and pass down with it (D04). Samples in brain/journal_samples/ until it has its own.
- The projector is a body ability (Body.show_photo), like the speaker: Unity draws it (ProjectorBeam.cs), the custom droid gets a real one, the lab Reachy has none and skips it.
- Look: a real image on a real surface with a lamp tint, soft edges and a switch-on flicker, never a floating hologram (honest-machine pillar). Inspiration board: BD-1 (Star Wars Jedi), principles only: separate lens for the projector, head as instrument. Not its look.

**D68 · Voice memories built (D33)** · Oct 25 · Built, needs a real test
- "Record this" / "remember this": listening chirp, antennas up and still, eye wide (a clear recording sign, D43), no chirps. The next sentence is kept, with natural pauses (ends after 1.5 s quiet, up to 30 s). "Not now" cancels. Nothing said for 15 s: stops waiting.
- Saved untouched in <cartridge>/journal/voice/ as 16-bit WAV plus a note of what was said (Whisper, local) and when. Passes down with the droid.
- "Play it back" / "let me hear it" / "play the one about the birthday": finds by words, else the newest. Plays through a tape filter (band-limited, wow and flutter, light hiss) so it's always clearly a recording, never the droid talking. It listens along quietly.
- Only on request (D45). Not yet: pairing a recording with a photo, retiring a recording, stopping playback midway.

**D69 · Voice memories: the person's voice through a droid speaker** · Oct 25 · Built, Riya to pick a style by ear
- Riya: the tape filter is "creep city". She wants the person's real voice with a warm, nostalgic robotic touch, never a voice of its own.
- Replaced wow, flutter and hiss with a small-speaker sound: thinner lows, softer top, a gentle body resonance, a faint metallic echo, a light digital crunch (fewer bits, lower rate, smoothed). Three strengths: speaker (lightest), droid (default), radio (most robotic). Reference: R2-D2 playing Leia's message.
- Playback is framed: a soft chirp before and after, so the droid presents the memory rather than pretending to be the person.
- scripts/voice_styles.py writes all three from the newest recording for listening. Tested only on espeak in Claude's workspace, so it must be judged on a real voice.
- Oct 25, Riya by ear on her own voice: the lighter styles sounded identical to the original (the Quest mic is 16 kHz). "radio" best, wanted a bit more. "transmission" too much ("dead corpse zombie"), blamed on the ring-mod buzz. Default is now "heirloom": between the two, 7-bit, 9.6 kHz, more body resonance and metal, no buzz.

**D70 · Photo taking works in MR** · Oct 25 · Built, needs a headset check
- Test: Meta's PassthroughCameraAccess (MRUK, SDK 207) gives the real Quest 3 camera over Link in the Editor at 1280x960, right way up. It returned colour bars until "Passthrough Camera API permissions" was turned on in the Meta Horizon Link app (Settings > Developer), then the Editor restarted.
- "Take a picture" / "say cheese": looks at you, three countdown beeps, the iris snaps shut and opens with a shutter chirp, then Unity (PhotoCapture.cs) grabs a camera frame and sends the JPEG to the brain, which keeps it in <cartridge>/journal/. "Show me a memory" can then project it. Never automatic (D02).
- In MR it photographs what you're looking at, since the camera is on the headset. The custom droid uses its own camera.
- Link accepts messages up to 8 MB now (photos). Verified with websockets 15.0.1.

**D71 · Rolling (MR)** · Oct 25 · Built, needs a headset check
- Riya: keep it simple, it just rolls (no shuffle, no wear-based variation).
- Beckon or "come here": it rolls toward you at 12 cm/s, eases in, stops about 45 cm away, keeps looking at you. "Go back" / "go home": rolls to where it started.
- Never more than 35 cm from its starting spot: there are no cliff sensors in MR, so this keeps it on the desk. The custom droid gets cliff sensors in winter.
- New pose channels drive_x / drive_z (metres from its starting spot). Unity moves the robot (ReachyRig.canRoll), so the overlays, the beam and your measured distance all come along. The lab Reachy can't roll and ignores them.

**D72 · Frame gesture takes a photo** · Oct 25 · Built, needs a headset check
- Both hands in an L (index and thumb out at roughly a right angle, other fingers curled), 12 to 70 cm apart, held 0.4 s: same as "take a picture" (countdown, shutter). Fulfils D02's "button, gesture or voice". Works silently, for loud rooms.
- Checked against synthetic hands: one hand alone, an open hand, a pointing hand with the thumb in, a heart, hands too close or too far all don't fire.
- In MR the photo comes from the headset camera, so your framing hands may be in the shot.

**D73 · Understanding by meaning, "huh?", and learning your words** · Oct 25 · Built, accuracy untested
- Riya: the biggest thing is the brain's intuitiveness and its ability to learn and understand.
- Order: exact words (a "not" in front blocks warm matches, "I don't love you" isn't a heart), then words it learned from you, then meaning, then "huh?".
- Meaning: fastembed 0.9.1 + all-MiniLM-L6-v2 (about 90 MB, ONNX, CPU, local). Every example phrase becomes a vector. A sentence is accepted if it's at least 0.55 close to a command and 0.05 closer than the runner-up. It only picks among existing commands, never generates words. Couldn't download the model in Claude's workspace, so real accuracy is measured on Riya's PC with scripts/meaning_check.py.
- "Huh?": short sentences (8 words or fewer) it can't place get a head tilt and a questioning chirp, at most once per 8 s (TV and roommates).
- Learning: an unknown phrase of 6 words or fewer, followed within 6 s by any command or gesture, is learned as meaning that (a "got it" chirp). Kept as text in the cartridge (words wear), never audio. Passes down: the next owner's droid still answers to the last family's pet names. A faded layer forgets them.
- To check against D43 (content only on request): it stores short phrases you teach it on purpose. Riya's call whether that counts as asked.
- Oct 25 first check on Riya's PC: 24/31 as expected, about 1 ms per sentence, no false understanding of unrelated sentences (top score 0.40). Fixes: one-word keywords only count in sentences of 3 words or fewer ("long time no see" was a scold, "I need some space right now" was a scold via "now"); meaning can't pick a warm command when there's a "not" (MiniLM scored "I don't love you" as love, 0.73); ACCEPT lowered to 0.50; added examples for "you mean the world to me", "get lost", "look what I've got" (these three now pass by construction). Long sentences (up to 25 words) are now understood by meaning, but only short ones (8 words or fewer) get a "huh?".

*D74 to D100 are kept for the proposals in docs/research/learning-system-research.md and learning-spine-research.md (moments.py and dialect.py already cite D99 and D85 to D87). Accepted ones get logged under those numbers.*

**D101 · Wheels dropped** · Oct 27 · Decided
- No free roaming. Reasons: it breaks "one brain, any body" (no other body can roll), desk edges and falls, a battery and dock to design, drivetrains fail first and can't be repaired by hand, and scope.
- D23 (rolls) and the wheel half of D39 are replaced. Rolling code (D71) stays as a sim experiment and is left out of demos.
- Maybe later: a tethered scoot of a few cm or a rocker. To do: redo the hardware list without wheels, cliff sensors or drive battery.

**D102 · The brain doesn't move to the lab's real Reachy Mini** · Oct 27 · Riya's call, to confirm in the plan
- The custom droid becomes the first real hardware. The Reachy Mini stays as the virtual body in MR.
- Knock-on: the spring transfer test needs a different second body (two custom droids, or custom droid + virtual Reachy). The project instructions and older plan docs still say winter runs on the real Reachy. Update them.

**D103 · Demo clock and the moment on the overlay** · Oct 27 · Built, needs a headset check
- run.py --clock 9:58 makes the droid think it's that time of day (the date stays real, the clock ticks at real speed), so a habit like the 10 am wave can be filmed at any hour. The overlay says "demo clock" whenever it's on, so footage stays honest.
- The wear panel now shows the clock, a NOW line for the moment happening (e.g. "wave around 10:03"), "family chirp" or "family chirp, passed down", how often and whose it is, and a HABITS list (an old keeper's habits marked "· L1", a woken habit replaces its old copy).
- Only real waves and voice count. Number keys never leave wear, so they never trigger a moment.
- scripts/demo_cartridges.py builds the four demo droids in one go (fresh, desk_student_year1, desk_student_passed_on, loud_family_year12) so their years end on the day you film. tests/test_demo_moment.py 8/8.
