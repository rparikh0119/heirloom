# Heirloom Handoff, Oct 27, 2026

Read this first in a new chat. It covers everything since the Oct 20 handoff: the learning research, what got built (moments, dialect, time skip clock), hardware and form decisions, and what's open.

Riya's working style: concise, direct, personality-driven. No em dashes, no semicolons, no performative framing, no "it's this, not that" phrasing. Push back with reasons. Credible, verified research, flag uncertainty, say "as far as we found". Bullets over dense prose. Never tell her to stop or take a break. Run commands always start with `cd E:\HEIRLOOM\brain`. Remind her to commit with `git add -A`. Log decisions and research in `E:\HEIRLOOM\docs\logs\`. Don't crowd this Project with docs.

---

## 1. Where things stand

- Repo: `E:\HEIRLOOM` (github.com/rparikh0119/heirloom). Brain in `E:\HEIRLOOM\brain` (venv `.venv`). Unity 6.3 project `E:\HEIRLOOM\unity\HeirloomMR` (Quest 3 over Link, Meta XR SDK 207.0.1, URP 17.3).
- Calendar: week 7 of fall quarter now. Week 8 Learning station, week 9 Transfer (two Reachys), week 10 playable POC + 3-person playtest.
- Everything below is committed and pushed (last pushes Oct 25 night).
- All four requested prototypes work in the headset: memory projection, voice memories, photo taking (voice + two-hand frame gesture), rolling (now a sim experiment only, see wheels decision).
- Test suite status: everything passes except `test_shh.py` 5/6 (`shh.py` is Riya's own unwritten exercise).

## 2. Brain pipeline (current)

events (voice, hands, camera) → REFLEXES ("hearing") → understanding → wear.record → reactions (JSON) → modes (plug-ins) → presence/expressions → Pose → body. WebSocket on port 8765 (second droid 8766).

- **Voice:** faster-whisper 1.2.1 base.en int8 CPU, loudness Segmenter, confidence filter. Quest mic is `--mic 2`. No wake word by default (`--need-name` to require it).
- **Understanding (D73):** exact match (SOLO_MAX 3, NEGATIONS guard) → learned words (words wear) → Meaning (fastembed 0.9.1 + all-MiniLM-L6-v2, ACCEPT 0.50, MARGIN 0.05, negation guard) → "unknown" → "huh?" (≤8 words, 8 s cooldown). Meaning check scored 24/31 on unseen paraphrases.
- **Wear plug-ins** (auto-discovered in `heirloom/wear/`, alphabetical): dialect, dials, moments, patina, words. Contract: `attach, record(event, mode, t), played(kind, name, t), tick(brain), apply(brain), validate(page, where), health()`. One JSON page per owner layer: `layers/L1/<plugin>.json`. Layer weights active/keep 1.0, blend 0.5, fade 0.5→0 over 56 days.

## 3. Built since Oct 20

### Moment registry: `heirloom/wear/moments.py` (proposed D99)
Something that keeps happening at about the same time of day becomes a moment with a stable id (`L1.m01`, name like "wave around 10:03"). Other learning hangs off these ids.
- Rule: same event within ±45 min (WINDOW) on ≥5 days (MIN_DAYS) spread over ≥14 days (MIN_SPAN_DAYS), on ≥30% of days since it started (MIN_DAY_SHARE), AND a coincidence test: binomial odds that random timing would pile that many into one slot must be < 1e-5 (COINCIDENCE). Compares against 2 weeks before the habit starts (LOOK_BACK 14), assumes a 16 h waking day (AWAKE 960), and habits it already knows don't count as noise.
- Why so strict (devlog material): first rule found 40 fake habits per simulated year. A 3x-busier rule still left ~1 fake per two years. Coincidence test: 0 fakes in 30 two-year runs, real habits found within a month in 29/30.
- Known behavior: three habits of the same gesture dilute each other and take ~3 to 6 weeks to separate. Two take ~9 days.
- `brain.moment` = current moment id (held 90 s). `brain.moments` = all moments, all layers, with `dormant` flag (not seen 30 days).
- Passed down: old moments never deleted, they sleep. New owner doing the same thing at the same time wakes it in their layer with `"from": "L1.m01"`. `explain(id)` gives an overlay line incl. "It used to do this with keeper L1, "first home"". `tag(id, name)` lets the owner name a moment.
- Privacy: stores only event name + minute. Raw notes dropped after 60 days.
- Needs a clock: real use uses the computer clock. If `brain.today` is set but `brain.now` isn't, it learns nothing.
- Tests: `tests/test_wear_moments.py` 15/15.

### Time skip clock: `heirloom/sim.py`
- Optional household `"routine"` (declared as a scenario in provenance): `"awake": ["09:00","23:59"]` + items with `events, at, jitter, chance, days (all/weekdays/weekends), gap`. Untimed mix moments land anywhere while awake.
- New household `sim/households/desk_student.json` (quiet_solo numbers + routine: 10:00 weekday hello, 15:30 weekday curious+good, 23:30 sleep).
- `_ends_today` now shifts moment dates too. Output prints "habits it noticed".
- Households without a routine behave exactly as before (no moments).
- Tests: `tests/test_time_skip.py` 12/12.

### Dialect v0: `heirloom/sound/genome.py` + `heirloom/wear/dialect.py` (proposed D85 to D87)
- Core chirps (chirps.py) stay fixed and readable by anyone.
- When the droid answers a moment, `brain._accent()` swaps the reaction's sound for a family chirp `m:<moment id>`, minted the first time, bred from that reaction's core chirp. So the 10 am hello still reads as hello, in the family accent.
- Genome = list of notes `{f0, f1, dur, gap, shape, wobble, wobble_hz, amp}`. `capture(name)` reads a core chirp as a genome. Identity = note count + direction of each note (Brewster earcons: rhythm/count discriminate, pitch alone weak). Every new chirp is ≥ MIN_DIST 1.0 from all chirps. Crowded families branch further (1 to 3 changes). Rhythm counts at most 0.5. Accent ×0.88 to 1.15, lengths ×0.85 to 1.2. Amp capped 0.45. Max length 1.0 s.
- Seeded per droid id + moment id: two droids grow different hellos.
- Passed down: a woken moment speaks with the old keeper's exact chirp (`"from"`).
- Registered into `chirps.CHIRPS` so bodies render it by name. No Unity change needed.
- Not yet: drift toward variants the family reacts warmly to.
- `scripts/dialect_listen.py` writes core vs family WAVs to `<cartridge>/dialect_listen/` (default `cartridges/sim/desk_student_year1`), plus `00_all_in_a_row.wav`.
- Tests: `tests/test_wear_dialect.py` 10/10. `test_wear_dials.py` fixed to find dials by name.
- **Riya hasn't listened yet.** Open item: run time skip + dialect_listen, judge each pair (too close / too far). Knobs are the mutation ranges in `genome.py`.

Run:
```
cd E:\HEIRLOOM\brain
python tests\test_wear_moments.py
python tests\test_wear_dialect.py
python scripts\time_skip.py --profile desk_student --years 1
python scripts\dialect_listen.py
```

## 4. Research done (Oct 25)

Two deep-research reports. Full files were delivered in chat (`Heirloom modular learning system.md`, `Heirloom learning spine.md`). Key takeaways:

### Modular learning system
- Learner: contextual bandit, bucketed Beta-Bernoulli Thompson sampling (a "worked X of Y times" tally per situation × response family). Full RL child-robot studies didn't converge in 7 to 8 sessions (Gordon 2016, Park 2019). Song et al. HRI '26 used TS over ~1,400 encounters and showed the best arm depends on the reward chosen.
- Eight plug-in slots on an in-process bus: feature extractor, baseline page, intent prototypes (embedding → 6 to 10 named intents), context provider, tagged response catalog, safety mask, learner (`propose/learn/explain/migrate`), reward interpreter. Decisions logged as JSONL with propensities (VW CB ADF shape) for offline replay (Li et al. 2011).
- Tone = per-owner, per-mic z-scores. Correct the spread, not the mean (Tran et al. INTERSPEECH 2023, ~200 s per speaker). Skip pretrained affect models.
- Pushback logged: EU AI Act may count tone-vs-baseline as emotion recognition (voice = biometric). Frame tone only as feedback on the droid's own last action, never store or show a feeling. "Learns what lands" can learn manipulation (Williams et al. 2024, De Freitas 2025): 7 structural guards. Inherited response table must be a capped fading prior.
- Market gap: as far as we found, no study or product lets an owner hold and pass on learned state.
- Proposed D74 to D84 (not logged): D74 bandit/TS, D75 learning only picks authored responses, D76 tone as per-owner per-mic z-scores used only as context/reward, D77 warm 1 cold 0 silence skips, no reward from session length/return/proximity, D78 safety mask + mute above learner, fixed goodbye, D79 log every decision, D80 features keyed by name, D81 handover rules, D82 per-body pages, D83 versioned pages + migrate, no pickle, D84 no culture presets.

### Learning spine (three systems that make inheritance real)
- One rule: universal core anyone can read, private family layer that wears in and passes down.
- **Chirp dialect:** Steels Talking Heads, Kirby 2008 iterated learning (numbers came via National Geographic, verify against PNAS before slides). Owners barely read barks better than strangers (Pongrácz 2005), so core feelings use universal sounds, the private dialect is for moments. Homonym filter, vocab cap 12 to 20, archive "fossil" chirps.
- **Keeper habits:** 7 numbers per keeper (tempo, amplitude, smoothness, directness, tilt bias, settle time, stillness), nightly update, never live mimicry (Jonell 2021 "tricked"). Laban Effort as body-agnostic style. Previous keeper fades to a floor 0.2 to 0.3, never zero. Correction: couple/dog "convergence" isn't supported (Tea-makorn & Kosinski 2020). Frame as "it picks up its keeper's habits".
- **Practice:** rhythm ribbon (per-weekday 96 × 15-min bins + Markov table), talk-presence hard-blocks self-initiated actions (Fogarty 2005 ~76%), owner-taught home sounds via YAMNet + 5 to 10 example prototypes.
- Moment registry is the shared spine (built). Per-plug-in fade curves needed (fading to 0 erases heirloom traits).
- Most publishable idea: an A → B → C handoff chain with real people on chirps.
- Proposed D85 to D100 (not logged). Research entries in the report are numbered R93 to R129 but must be renumbered to follow R79 in her log.
- Flags: Fu et al. 2025 ("felt heard but not understood") could not be found, don't cite until rechecked. Yin et al. PNAS 2024 is a verified neighbor. No Pi 5 timings exist for faster-whisper, YAMNet or MediaPipe: benchmark in winter week 1.

### Creative angles brainstormed (Riya agreed to the spine of 1, 2, 3)
1 private chirp language, 2 picks up owner body language, 3 learns a practice, 4 clicker training via toggle/touch, 5 dreaming/consolidation at night, 6 restraint as main skill, 7 doubt shown in the body, 8 droids teach droids, 9 open the cartridge in MR to curate before handover. Breeding cartridges rejected as gimmick.

## 5. Hardware and form (Oct 27)

- **Wheels: Riya is dropping them** (free roaming). Reasons: breaks "one brain any body" parity, desk edges and falls, battery/dock, drivetrains fail first and aren't repairable by hand, scope. Rolling code stays as a sim experiment. Optional later: a few-cm tethered scoot or rocker. To do: log the decision, rework the hardware list.
- **Real Reachy Mini: Riya says she's not moving the brain to the lab's real Reachy Mini.** Older plan docs still say she does. Confirm and update the plan. Effects: the spring transfer test needs a different second body (two custom droids, or custom + virtual Reachy), and the custom body becomes the first real hardware.
- **Touch sensing: undecided, leaning optional.** Camera can't see touches on its own head or back, can't tell hover from touch, fails in the dark or when the camera is off. Touch is the clearest warm signal and shows real wear zones. Implementation: copper foil zones inside printed panels, MPR121 (12 channels, I2C, works straight on a Pi 5, Arduino not required), wires to the base. Metal panels block sensing (a metal panel can itself be the electrode). Test wall thickness with a sample print. "Arduino touch pad" was shorthand, not a product.
- **ID sketches (industrial design collaborator):** Riya's favorites are (A) sphere head with iris on a control-panel trapezoid base with wheels, and (B) boxy camera-like head on a neck over a tapered body with hidden wheels. Also seen: reel/cassette head on a tall cone. Claude's read: B maps best to Reachy-style tilt/roll and the "field instrument / vintage Sony" brief. A's base is the best detail on any sheet. A hybrid (A sphere head on B neck over A base) could be strongest. Claude flagged A's head as possibly reading like a cartoon bomb (round body + square collar + curly antenna on top). Riya disagrees. Suggested test: show 5 strangers cold, ask "what is this?". Fix if needed: move the antenna off top center or use a rounded gimbal collar.
- **Missing from all sketches (next round):** cartridge slot (A's front slot is the obvious spot), the toggle mute switch, the projector lens (+ camera spot), an iris that reads as an overlapping aperture rather than a fan, marked wear zones, the cream/oxblood split, scale with a hand, one visible repair.
- **Funding:** the robotics satellite program may fund part of the build if Riya brings a solid design plan and a parts list ("shopping list") by week 10. This is a priority deliverable.
- **Lee Cody** (past professor, helped on Tether hardware): email drafted and finalized asking for 20 to 30 min to poke holes in the design and parts list. She'll bring sketches + draft parts list. He dislikes cockiness and people who talk without knowing what they're saying, so be precise about hardware facts.

## 6. Open items

1. Build the hardware plan + parts list for the satellite program (week 10). Redo the list without wheels. Decide: power (plug-in vs battery, she's OK with lithium since Oct 20), servos (model not chosen), projector module, camera, mics, speaker, touch (maybe), toggle, cartridge (currently a folder of files, physical form TBD), Pi 5 enclosure/heat.
2. Prep for the Lee Cody meeting (draft parts list, sketches, questions: power, fixed base vs wheels, servo choice and failure points, enamel-over-aluminum wear effect, projector heat/brightness, touch through printed walls).
3. Listen to the family chirps and tune `genome.py` if needed.
4. Log decisions: wheels dropped, real-Reachy change, and whichever of proposed D74 to D100 she accepts. Renumber research entries after R79. Recheck Fu et al. 2025 and Kirby numbers.
5. Next code: show `brain.moment` in the wear overlay (`explain()` line), then dialect drift (needs the reward interpreter), then the learner (bandit) per the modular report.
6. Older carried items: meaning_check rerun with her own sentences, D43 question (does teaching words count as "asked"?), headset checks (palm-out vs petting, User Head field, overlay Text Size 0.12 / Offset X ±0.12, projector beam values), `shh.py` exercise, goodbye/presence events, handoff ritual direction (A/B/C), deck/FigJam updates for D52/D57, roommate privacy note on photos.
