# Three Spines Make Heirloom's Inheritance Real

**Bottom line.** Build all three spine systems on one rule: **split what anyone can read from what only the family reads, and let only the family layer wear in and pass down.** For sound, that means a locked set of core chirps tuned to universal acoustic cues (high and fast reads as excited for strangers too) plus a private set of "moment chirps" that get minted for recurring family moments, drift in accent with use, and pass to the next owner as a frozen base layer the new owner slowly bends. For movement, the droid keeps a handful of body-agnostic style numbers per keeper (tempo, settle time, head-tilt bias), updated nightly and never echoed live, so a previous owner survives as a capped offset with a floor that never hits zero. For practice, the droid learns a decayed 24-hour rhythm ribbon, named rituals, interruption etiquette and owner-taught home sounds, and on handover the rituals and sounds travel as named heritage while the timing priors re-learn. The strongest single move is a **shared moment registry**: the practice spine defines the moments ("kettle break, 3:30"), the dialect spine gives each one a chirp, the habits spine colors how the droid moves through it. That gives the core question a demoable answer: the practice and the accent come along, the timing re-learns, and the person's private data stays behind. Every mechanism here is established technique on its own, and all of it fits a Pi 5 by inference (none of it benchmarked yet). The novel part, as far as we found, is the combination. No shipped product we found evolves its sounds per unit, no robot study we found absorbs one person's motion style over months, and no system we found hands a learned routine to a successor. Three of the ideas need pushback below: the dog and couple "convergence" story does not hold up, owners probably won't decode a private code for core feelings, and the dialect's context hash as drafted needs person identity that your privacy rules forbid.

---

## One rule runs all three spines: universal core, private accent

The evidence lines up behind a two-tier design across sound, motion and routine.

- **People read robot beeps categorically.** Ratings snap to prototype emotions along sound continua. ([Read & Belpaeme 2016](https://pearl.plymouth.ac.uk/handle/10026.1/4407?show=full)) [abstract] Small drifts inside a category won't flip meaning. Drift across a category boundary (rising to falling contour) will.
- **Owning a dog barely helps you read barks.** Listeners classified bark situations well above chance, and ownership and breed experience had "almost no effect". Ratings tracked pitch and inter-bark interval. ([Pongrácz et al. 2005](https://czaw.org/?p=3568)) [abstract] So "owners will learn it" cannot carry core states. Universal acoustics can.
- **Family words start as one memorable moment and spread.** Ogilvie traces familects to single incidents and children's mispronunciations, and the Mitfords coined "cake" for the Queen Mother after one remark. ([Prospect, Ogilvie 2023](https://prospectmagazine.co.uk/views/columns/62168/joy-of-lex-what-family-words-say-about-us)) [column, anecdotal] As far as we found, familect evidence is anecdotal and survey-based, with no controlled study.
- **Laban Effort axes stay legible on tiny bodies.** All four Efforts read on a 2-DOF Nao head and a 4-DOF Keepon (1,028 ratings of 72 videos). ([Knight & Simmons 2016](https://ri.cmu.edu/?p=122282)) [abstract] Style can live as a few numbers and survive a body swap.
- **Routines vary by household, and the minority variations matter.** A routine-learning robot failed when the user picked a less frequent variation. ([Patel et al. 2023](https://ar5iv.labs.arxiv.org/html/2309.06252)) [full text] Craft documentation loses the improvisations more than the steps. ([Batra et al. 2025, CraftLink](https://arxiv.org/abs/2506.10891)) [abstract]

**What it means for the design**
- Core layer: factory, locked meaning, readable by a stranger at the exhibit.
- Family layer: minted from this household's moments, drifts in fine parameters, carries the lineage.
- The Heirloom-specific research claim falls straight out of it: **a family reads its worn droid's moment chirps better than strangers do, while both read the core set equally.** That is the result Pongrácz did not find for dogs. It is testable in spring.

**Correction carried forward.** Spouses' faces "do not converge over time" in 517 couples photographed at marriage and 20 to 69 years later. ([Tea-makorn & Kosinski 2020, via Stanford GSB](https://www.gsb.stanford.edu/index%2ephp/node/501333)) [abstract] Dog work shows owner personality shaping dog stress and attention, with causation open. ([Sundman et al. 2019, via Linköping](https://liu.se/en/news-item/hunden-speglar-agarens-stress)) [press release], ([Kis et al. 2012](https://real.mtak.hu/3557/)) [abstract] Frame it as **"it picks up its keeper's habits"**. Drop any "companions come to resemble owners" line.

---

## Spine 1: a chirp dialect built like a tiny language game

### Precedent worth stealing
- **Steels' Talking Heads** grew a shared lexicon through grounded guessing games: about 400,000 games, just under 2,000 agents, 8,000 words, a core of about 100. ([Steels 2002](https://langev.com/pdf../../pdf/steels02crucialFactors.pdf)) [full text via fetch summary] The learning rule: success strengthens the used word-meaning pair and weakens rivals, failure weakens the pair. Pure co-occurrence counting was not enough. Agents had to test whether words worked. A non-verbal channel (pointing) bootstrapped meaning.
- **Turnover kills lexicons.** Replacing one agent every 10 games collapsed the vocabulary. One every 100 was fine. ([Steels 2002](https://langev.com/pdf../../pdf/steels02crucialFactors.pdf))
- **Iterated learning simplifies what it passes down.** In Kirby, Cornish & Smith, languages became easier to learn over generations. ([Stirling repository](https://stir.ac.uk/research/hub/publication/687799)) [abstract] With no filter, vocabularies collapsed to a handful of catch-all words. With homonyms removed between generations, they stayed expressive and grew compositional structure by generation 6. ([National Geographic](https://www.nationalgeographic.com/science/article/language-evolution-witnessed-in-lab-experiments)) **[secondary source: the 80 participants, 4 chains, 10 generations and 27 meanings come from Nat Geo. Check against the PNAS PDF before a slide.]**
- **Burtt built R2-D2** by speaking English lines while twiddling an ARP 2600's filters. His stated goal for constructed languages: "emotional clarity." ([Designing Sound, Burtt part 2](https://designingsound.org/2009/09/10/ben-burtt-special-star-wars-the-sounds-part-2)) Pitch, intonation and timbre carry intention and emotion in R2-D2 and WALL-E sounds. ([Jee et al. 2010](https://dspace.kaist.ac.kr/handle/10203/94821?mode=full)) [abstract]
- **Cozmo used 15 variations per sound** because a repeated sound breaks the illusion, and its designer wanted mood to drive synthesis parameters live but had no tool for it. ([Designing Sound, Gabaldon 2016](https://designingsound.org/2016/11/15/sound-for-robots-an-interview-with-sr-sound-designer-ben-gabaldon/)) Heirloom's procedural chirps can do what Cozmo wished for.
- **Brewster's earcon rules:** recognition rose from 49.1% to 86.6% after redesign. Use distinct timbres and rhythms, avoid pitch-only differences, keep notes at least 0.125 s, leave about 0.1 s between sequenced sounds. ([Brewster et al. CHI 1993](https://www.dcs.gla.ac.uk/~stephen/papers/CHI93.PDF)) [full text via fetch summary]
- **No product we found evolves its sounds per unit.** Furby scripted a Furbish-to-English shift and the public believed it learned. ([Wikipedia: Furby](https://en.wikipedia.org/wiki/Furby)) LOVOT markets an evolving personality, with no source saying its voice changes per unit. ([Robots Guide, LOVOT](https://robotsguide.com/robots/lovot)) As far as we found, the gap is open.

### The mechanism: a chirp genome with locked identity and drifting accent
Refactor `heirloom/sound/chirps.py` so every chirp renders from a genome stored in the cartridge.

| Gene group | Genes | Behavior |
|---|---|---|
| **Identity (locked)** | note count (1 to 5), contour class (rise, fall, rise-fall, flat, trill), context binding | Never drifts. Rhythm and note count are Brewster's most discriminable cues, so they carry "which word". |
| **Accent (drifts)** | base pitch within a band, pitch excursion, per-note durations (min 0.125 s), FM brightness, vibrato rate and depth, attack | Mean, per-play jitter and drift rate per gene. Jitter gives Cozmo's freshness. Drift moves the mean. |

**Drift signal (implicit, no ratings).** Interactive evolution over sound parameters exists, and user fatigue is its main problem, which forces tiny populations and few explicit judgments. ([Wikipedia: IEC, on Takagi 2001](https://en.wikipedia.org/wiki/Interactive_evolutionary_computation)) [secondary] So skip ratings.
- Warm cue after a play (turn toward, approach, touch pad, laugh, vocal reply): nudge the gene means a small step toward the jittered variant that just played. That is an evolution-strategies step in plain words: try small random variations, keep moving toward whichever ones worked.
- Mute press or being ignored: no step, and mute rolls that chirp back one step.
- Cap total drift per gene (proposed starting point about one just-noticeable step per month). **No sourced rate exists.** Tune in playtest.
- Preference-based Bayesian optimization (picking the next variant from pairwise preferences) is the fancier upgrade. ([Brochu et al., arXiv 1012.2599](https://arxiv.org/pdf/1012.2599)) [record only] Ship the simple step first.

**Minting moment chirps (the familect move).**
- Every recurring context cluster gets a Steels-style score table. When a cluster recurs at least 5 times over at least 2 weeks with no chirp bound, mint one by mutating the nearest existing chirp so the dialect sounds like one family.
- **Homonym filter** (Kirby Exp. 2 in code): a new or drifting chirp may not come within a minimum distance of any other active chirp, measured on rhythm and contour first.
- Vocabulary cap of 12 to 20 active moment chirps plus the core set (design choice).
- Unused bindings decay into an **archive**. The cartridge keeps "the sound it used to make for the kettle" and plays it only on request.
- Ground every chirp in motion. Steels needed pointing. Heirloom's head turn toward the kettle is the pointing. Never learn a chirp from sound alone.

**Push back: the context hash as drafted needs "which known person".** Your practice rules say never learn or store voice identity, and guests can't consent. "The chirp that means Grandma's home" needs Grandma identified somehow. Options, strongest first:
1. Bind to events and owner-taught sounds (door, kettle, the 6 pm arrival window). The practice spine already produces these.
2. Let the owner explicitly tag a moment ("this one's for when Dad gets home") with a gesture or phrase. Owner-asserted, no recognition model.
3. Skip people entirely in the POC.

**Seed authoring.** Use Burtt's trick inside your rules: record a spoken line, extract only the pitch contour and timing, render it through the synth, discard the voice. The droid inherits human-legible intonation without ever speaking in a human voice.

### How the dialect passes down
- Owner A's dialect page freezes into L0 as the **base**. Owner B gets a fresh **delta** page. Drift writes only to the delta, and a weak spring pulls it back toward the base. Steels' turnover finding says slow change keeps the lexicon coherent.
- Expect simplification. B only meets the moments that recur in B's life, which is Kirby's bottleneck. Treat it as the expected outcome and show it. Chirps that never fire for B go dormant and drop to the archive with A's name on them.
- New body, same owner: the genome carries unchanged. Speakers differ, so add a per-body output EQ and loudness offset under `bodies/<body_id>/` (inference). Otherwise the brightness gene shifts for reasons that have nothing to do with use.

---

## Spine 2: keeper habits as seven numbers, updated while the owner sleeps

### What the mimicry evidence says, and where it stops
- **Live mimicry works when unnoticed.** Participants mirrored a confederate's face rubbing without noticing, and mirrored participants liked the confederate more (6.62 vs 5.91). Only 1 of 37 noticed a similar mannerism. ([Chartrand & Bargh 1999](https://pages.ucsd.edu/~pwinkiel/chameleon.pdf)) [full text]
- **A VR agent copying head motion at a 4 s delay** was more persuasive and better liked, and people couldn't detect it. ([Bailenson & Yee 2005](https://vhil.stanford.edu/publications/avatars-and-agents/digital-chameleons-automatic-assimilation-nonverbal-gestures)) [abstract]
- **On robots it gets fragile and creepy.** A Furhat pilot (n=12) copying head and face at 4 s found no significant effect on liking or trust, and one participant "felt like I was being tricked." ([Jonell et al. 2021](https://arxiv.org/pdf/2109.01206)) [full text] Agents replaying people's own gestures: 4 of 6 preferred their own motion, and the 2 who didn't were less extroverted. ([Luo, Neff & Ng-Thow-Hing](https://www.cs.ucdavis.edu/~neff/papers/An%20Examination%20of%20Whether%20People%20Prefer%20Agents%20Whose%20Gestures%20Mimic%20Their%20Own.pdf)) [full text, tiny n]
- **As far as we found, no study tests months-long style absorption on a robot.** The long-timescale version is new ground. The liking rationale carries over. The long-term evidence does not exist yet.

**Design consequence.** Never echo a gesture within seconds. Absorb statistics, never trajectories. Tell the owner it happens. Owners are told the droid learns, so the covert-mimicry studies don't transfer cleanly anyway. Disclosure fits the honest-machine pillar.

### Capture: Quest 3 now, robot camera later
- Quest Movement SDK gives 70 upper-body or 84 full-body joints with position and rotation. Under heavy load including **passthrough**, inside-out body tracking falls back to low fidelity and loses elbows and spine lean. ([Meta Developers, Body Tracking](https://developers.meta.com/horizon/documentation/unity/move-body-tracking/)) [full] Heirloom runs passthrough all the time, so **head pose and hands are the reliable channels**. Torso lean is optional.
- Winter: MediaPipe Pose gives 33 landmarks. Indices 0 to 10 are coarse face points. ([Google AI Edge, Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker)) [full] Use eye or ear lines only to derive head roll, then drop them. No expression model ever runs, which keeps the no-face-emotion rule literally true. World-landmark units and Pi 5 speed are **unverified**.

### The seven style numbers
Computed per gesture in memory, summarized as a daily median, stored as one small vector per keeper.

| Owner feature | How measured | Effort-style axis | Droid dial it shifts |
|---|---|---|---|
| Tempo | peak head and wrist angular speed, gesture rate | Time | `speed`, onset sharpness |
| Amplitude | head pitch/yaw/roll range, wrist excursion | Weight | `size` |
| Smoothness | normalized jerk (filtered, tracking noise inflates it) | Flow | `smooth`, `wobble` |
| Directness | path wander before settling on a target | Space | `hesitate`, path curvature |
| Tilt bias | median head roll at rest | none (extra idiom) | new resting-tilt param |
| Settle time | gesture peak to stillness | none (extra idiom) | new settle param |
| Stillness ratio | share of time below motion threshold | Flow | idle frequency |

- Laban Effort is a dance-notation vocabulary for *how* a body moves (sudden vs sustained, strong vs light, direct vs wandering, bound vs free). It is body-agnostic, which is exactly why it carries across the Reachy-to-custom-droid swap.
- Anticipation raised a PR2's appeal (4.83 vs 4.27) and reaction raised perceived smartness. ([Takayama, Dooley & Ju 2011](https://www.wendyju.com/publications/151r-takayama.pdf)) [full] So **settle and anticipation are where an inherited personality will read most.** Make settle time your hero trait.
- Creature Features maps human motion onto non-human bodies in real time. ([Seol, O'Sullivan & Lee 2013](https://mrl.snu.ac.kr/publications/creatureFeatures/creatureFeatures.htm)) [abstract] Good proof that retargeting to creatures works. It is puppetry, and it marks the line Heirloom stays behind.

### The blend (design proposal, constants are guesses)
- Daily owner estimate `o_day` = robust median. Owner layer `O ← O + α·(o_day − O)` with α ≈ 1/30 per active day (half-life about three weeks). Skip thin days.
- Expressed style = droid base + patina + `w_new·clamp(O_new)` + `w_prev·O_prev`.
- Cap each owner offset at 25 to 35% of the dial span so the droid stays itself. `w_new` ramps 0 to 1 over 4 to 6 weeks, so a new keeper first meets the inherited character.
- **Patina and habits stay separate fields.** Patina is how much it has been used. Habits are whose hands raised it. Same dials, two sources, one total clamp. That keeps the transfer test clean.
- Owner strength dial with an off position. Luo's introverts are the reason.

**Make it noticeable on purpose.** People spot motion-transition differences of only a few frames in human motion ([Wang & Bodenheimer](https://eecs.vuse.vanderbilt.edu/People/bobbyb/pubs/sigposter2005.pdf)) [short poster], but sensitivity to some errors drops on abstract shapes ([Reitsma, Andrews & Pollard 2008](https://ri.cmu.edu/?p=10106)) [abstract]. On a non-humanoid, allow differences of hundreds of milliseconds at the extremes. Added accelerations are easier to detect than added decelerations ([Reitsma & Pollard 2003](https://ri.cmu.edu/?p=8709)) [abstract], so "sharper onsets from the old keeper" may read better than "slower settles". Test both.

### How habits pass down
- On handover, freeze `O_prev` with the outgoing keeper's chosen label. `w_prev` decays to a **floor of 0.2 to 0.3, never zero**. The floor is the whole "still moves a little like Grandpa" effect.
- **Push back on the default layer weights.** Your current fade runs 0.5 to 0 over 56 days. For habits and dialect, a fade to zero deletes the heirloom. Give each plug-in its own fade curve (see the handover table below).
- New body: the seven numbers carry, and each body's adapter maps them to its own joints. The spring transfer test then asks a sharp question: does style survive a body change? Knight & Simmons give you reason to expect yes at low DOF.

---

## Spine 3: the practice as a ribbon, a ritual list, an etiquette and a sound library

### Rhythm: decayed histograms beat deep models at this scale
- CASAS forecast "time until the next activity" with a regression tree on time of day, time since last event and event counts. It beat an SVM in 18 of 25 homes, and the SVM couldn't finish in 12 hours on large windows. Irregular activities (leaving, arriving) stayed hardest. Rare-but-regular events forecast fine (error vs frequency r ≈ 0.0038). ([Minor & Cook](https://eecs.wsu.edu/~bminor/publications/pmc16.pdf)) [full, venue and year unconfirmed]
- Data spanned "a few weeks to about a year" per home, with no learning curve by day. As far as we found, nobody reports how many days a single desk user needs.

**Build:** a `rhythm` page of per-weekday × 96 fifteen-minute bins × state probabilities (present, talking, deep work, break, away), exponentially decayed with about a 2-week half-life. Add a first-order Markov table (a grid of "how often state A leads to state B") over named states: arrive, settle, deep work, break, return, leave. That is the rhythm ribbon, it is human-readable, and it retrains in milliseconds. A small tree forecaster is the upgrade. Skip transformers. On odd days, live signals beat the prior.

### Etiquette: one microphone bit does most of the work
- A single "anyone talking" sensor predicted non-interruptibility at about 76%, matching human observers at about 76.9%. Simple sensors plus time of day reached about 79%. Small sample: 4 office workers, 602 hours. ([Fogarty et al. TOCHI 2005](https://interruptions.net/literature/Fogarty-TOCHI05.pdf)) [full]
- BusyBody trained personal interruption-cost models by occasionally asking users how interruptible they were. ([Horvitz et al. CSCW 2004](https://erichorvitz.com/busybody_cscw.htm)) [landing page, foundational]
- A routine robot asked about 18% of the time and that rescued unusual days. ([Patel et al. 2023](https://ar5iv.labs.arxiv.org/html/2309.06252))

**Build:** an `etiquette` page that learns per-time-bin thresholds from check-ins. The droid's check-in is a small head tilt. Engaged response = good time. Ignored or waved off = bad time. That is BusyBody made non-verbal. Hard rules on top:
- Talk present (local VAD) blocks any self-initiated action. Defer the action, keep it queued.
- Learning may tighten the threshold freely. It may loosen it only within a factory bound. A droid that learns to interrupt more is the reward-hacking direction.
- Aim well under Patel's 18% check-in rate. No source gives the right number.
- Etiquette feeds the earlier architecture's safety mask (slot 6) and the `give_space` arm. It decides *when* the bandit may act at all.
- Typing sound as a deep-work cue: supporting evidence only. Fogarty didn't single out keyboard features, and we found no validated typing-based flow detector.

### Home sounds: teach it the kettle with five examples
- DCASE's few-shot bioacoustic task detects a sound from about 5 annotated examples, and prototypical networks did well. ([Nolasco et al. 2023](https://darchive.mblwhoilibrary.org/entities/publication/8de3aa5a-22ba-4f50-b8f3-cb4cd5b5fd1b)) [landing page] Few-shot detection works from one or a few examples with auto-built negatives. ([Wang et al. ICASSP 2020](https://research.adobe.com/publication/few-shot-sound-event-detection)) [landing page] Going from 5 to 10 shots raised F1 (0.575 to 0.670 in one setup), and quiet sounds near background level were the hard case. ([Wolters et al. 2021](https://arxiv.org/html/2107.13616v2)) [full]
- YAMNet: 521 classes, 1024-d embeddings, mono 16 kHz input, about 3.2M parameters, Apache-2.0 per ST's repackaging (confirm upstream). ([TF YAMNet tutorial](https://www.tensorflow.org/hub/tutorials/yamnet)), ([ST model card](https://huggingface.co/STMicroelectronics/yamnet/blob/0a1a2dcdcc92789e8409d3ff43ef6906438412f1/README.md)) A worked TFLite-on-Raspberry-Pi example exists. ([MathWorks](https://www.mathworks.com/help/audio/ug/audio-event-classification-using-tensorflow-lite-on-raspberry-pi.html)) [not opened] Pi 5 latency is **unbenchmarked**.
- Ubicoustics showed gain, reverb and mixing augmentation helps sound models generalize to real rooms. ([Harrison, Ubicoustics](https://chrisharrison.net/index.php/Research/Ubicoustics)) [project page]

**Build:** a perception plug-in (slot 1 in the earlier architecture) that owns a `sounds` wear page.
- Pipeline: mic → YAMNet → embedding about every half second (frame timing **unverified**) → cosine similarity to each owner prototype (the average of the owner's examples) → fire after N consecutive frames above a per-class threshold.
- Teaching: owner says "that's my kettle" → droid collects 5 to 10 occurrences across days → augments each → also stores a "normal room" background prototype → owner corrects with "not that", which adds negatives.
- Expect kettle vs extractor fan vs tap confusion. Persistence, per-class thresholds and the rhythm prior (kettles happen at 3:30) cut it down.
- YAMNet's generic "Speech" class doubles as the etiquette talk bit.
- Store prototypes only, a few KB per sound. No raw audio. Treat prototypes as sensitive, since nobody has shown YAMNet embeddings can't be inverted.

### Rituals: keep the variations
A `rituals` page holds named sequences ("morning settle", "kettle break") with a start-time distribution, duration, trigger cues and their variations ("Fridays run late"). CraftLink's point is that the improvisations are the practice. Averaging them away erases the owner.

**Push back on the word "apprenticeship".** Robot apprenticeship learning means inverse reinforcement learning of motor skills, which Heirloom doesn't do. "The droid apprentices to your rhythm" works as a metaphor on a slide, labeled as one.

### How the practice passes down
- Rituals and the ribbon pass as **read-only heritage**. The droid offers inherited rituals as optional suggestions ("the old keeper broke for the kettle at 3:30"). Adopted ones copy into the new owner's layer.
- Timing priors and etiquette **reset**. The new owner's day is theirs.
- Sounds pass as **named memories with detection paused** until re-verified in the new room and on the new mic.
- Guests and roommates never transfer. Unknown-person presence pauses learning.
- As far as we found, nobody has studied how people feel about inheriting someone else's routine model. That is a spring interview question.

---

## The spines plug into the wear contract as six plug-ins and one registry

### Shared moment registry (the strongest cross-spine move)
```
practice spine  ->  moment registry  ->  dialect spine binds a chirp
 (ritual, sound,     {moment_id,        habits spine colors the motion
  rhythm state)       name, cues,        bandit picks the response family
                      first_seen,
                      owner_layer}
```
- One `moments` page lists recurring moments with stable IDs. Rituals and taught sounds create them. Dialect binds chirps to moment IDs. The bandit's context bucket from the earlier report can include a moment ID as one more named feature.
- Result: "Grandma's 3:30 kettle break" has a sound it hears, a chirp it makes and a tilt it does, all traceable to one ID and one owner layer.
- Moment IDs make inheritance explainable: "this chirp was minted for moment m_014, first seen with keeper A."

### Contract mapping
Method meanings follow my reading of your contract names: `record` observes an event, `played` hears what the droid just did plus its reward line, `tick` runs on a clock, `apply` shapes outgoing expression. Correct these if your code means something else.

| Plug-in (page) | record | played | tick | apply | explain |
|---|---|---|---|---|---|
| **dialect** (`dialect.json`) | moment occurrences | reward for the chirp variant played | mint, decay, archive (daily) | render genome → chirp with jitter | "minted for m_014, 63% of accent from keeper A" |
| **habits** (`habits.json`) | per-gesture features in RAM | none | nightly median → owner vector, discard features | offsets to patina dials | "settle: 60% yours, 40% previous keeper" |
| **rhythm** (`rhythm.json`) | state changes per bin | none | decay, rebuild Markov table | forecast to context provider | "you usually break around 3:30 on weekdays" |
| **rituals** (`rituals.json`) | sequence matches | adoption of offered ritual | detect new recurring sequences | suggestions to bandit context | "inherited from keeper A, adopted by you" |
| **etiquette** (`etiquette.json`) | check-in outcomes | cold cue after self-initiated action | threshold update | gate into safety mask | "held back: talking detected" |
| **sounds** (`sounds.json`) | taught examples, corrections | none | recalibrate thresholds | detections to bus | "matched 'kettle', taught Oct 30, 41 confirmations" |

All six implement `attach`, `validate`, `health` and `migrate` like the existing dials, patina and words. `health` should report drift against caps (dialect), distance from factory (habits), and false-positive corrections per week (sounds).

**Reward window conflict.** The earlier report proposes a 5 to 8 s reward window. The dialect notes suggest about 3 s for crediting a chirp. Both are design guesses. Use the one reward interpreter (slot 8) and the shared `decision_id`, and let dialect credit only cues inside the first ~3 s while the bandit uses the full window. Log cue timestamps and retune from data.

### Cartridge additions
```
layers/L1/  dialect.json  habits.json  rhythm.json  rituals.json
            etiquette.json  sounds.json  moments.json
layers/L0/  same pages, frozen, with keeper label
bodies/<body_id>/  speaker_eq.json  mic_baseline.json  joint_map.json
archive/    retired chirps, dormant moments (played on request only)
```

### Handover and per-plug-in fade curves
| Page | New owner | New body, same owner | Fade curve |
|---|---|---|---|
| `dialect` core set | Carries | Carries | Locked |
| `dialect` moment chirps | Frozen base + new delta with spring | Genome carries, speaker EQ per body | Floor 0.2 to 0.3 |
| `habits` | Frozen `O_prev` with label | Vector carries, joint map per body | Floor 0.2 to 0.3 |
| `rhythm` | Read-only heritage, new owner starts fresh | Carries | Live prior fades to 0 |
| `rituals` | Offered as suggestions | Carries | Unadopted stay archived |
| `etiquette` | Resets to factory | Carries, talk detector re-checks on new mic | 0 |
| `sounds` | Named memories, detection paused | Re-verify on new mic | Memories keep, detection resets |
| `moments` | Carries with lineage | Carries | Dormant until recurrence |
| guest data, raw features | Never stored | Never stored | n/a |

Before any handover, the outgoing owner gets a review screen to drop specific chirps, rituals, sounds or the whole habits layer. That is "everything it learns is yours" with an eraser.

---

## Risks, with the fix for each

| Risk | Evidence | Fix |
|---|---|---|
| Dialect collapses into catch-all chirps | Kirby Exp. 1 (secondary source) | Homonym filter, identity genes locked |
| Lexicon falls apart at handover | Steels turnover | Frozen base, slow delta, spring |
| Chirps get louder and brighter to win attention | Reward hacking by inference, approach cues are gameable | Clamp loudness, brightness, length. Mute = rollback |
| Repetition fatigue | Cozmo 15 variants | Per-play jitter |
| Noticed mimicry feels manipulative | Jonell "tricked" | Nightly updates, disclosure, strength dial |
| Nobody notices inherited habits | JND and abstract-body data | Exaggerated caps, side-by-side demos, lineage overlay |
| Motion data identifies people | 94.33% ID from 100 s of head and hand motion among 50,000+ users ([Nair et al. 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/nair-identification)) [abstract] | Store 7 numbers, never raw joints. "Far less identifying" is inference, untested |
| Person identity sneaks into contexts | Your own rules | Events, taught sounds, owner tags only |
| Sound false positives at home | No real-home rates found | Persistence, thresholds, rhythm gating, "not that" |
| Interruptibility reads as inferring "intentions" from biometric data | EU AI Act definition covers emotions or intentions from biometrics ([EUR-Lex 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)) | Frame all signals as timing for the droid's own action. Store talk presence and motion counts, never an owner state. Unresolved legal reading |
| Novelty decays over months | Unsourced | Spring fresh-vs-worn test. Moment chirps gain value through history, unproven |

---

## Creative development angles worth chasing

- **Run a Kirby chain with real people.** Owner A raises a virtual Reachy, hands it to B, B to C, with compressed drift. Measure whether the dialect simplifies and which moment chirps survive. As far as we found, nobody has run iterated learning on non-linguistic sounds between people and a robot. This is the most publishable idea in the report.
- **Dialect family tree.** An MR overlay draws each chirp as a branch, colored by the keeper whose layer minted or bent it. Furby proves people believe in growth they can perceive. Showing the genome makes your growth honest.
- **Fossil chirps.** Archived chirps play only on request: "the sound it used to make for Grandpa's door." Fits "memories only on request."
- **Twin droids, one reaction.** Two virtual Reachys raised by different scripted keepers do the same greet. Settle time and tilt differ visibly. Strongest game-dev-readable demo of habits.
- **The kettle answers back.** Teach a sound and the droid mints a chirp for it on the spot. Practice and dialect spines meet in one 20-second demo beat.
- **Seed chirps from Riya's own prosody.** Burtt's method gives the factory dialect a personal origin that never uses a human voice in output.
- **Ritual card at handover.** A printed or MR "inheritance card" listing named rituals, sounds and inherited traits. Reads like the inside cover of a family recipe book.
- **Accent meter on the iris.** The mechanical iris dilates slightly when a moment chirp plays versus a core chirp. A physical cue that this sound belongs to your family (inference, untested).

---

## How this shows up in the schedule (lighter)

**Push back first:** the earlier report already loads week 8 with the bandit and reward interpreter. All three spines in full won't fit. Ship plumbing and one visible behavior per spine, then grow.

- **Week 8, Learning.** Chirp genome refactor plus drift on reward with an accelerated clock. Habits feature extraction from Quest head and hands, logged and summarized per session (session = compressed "night"). Rhythm ribbon from a scripted synthetic week. One taught sound on the laptop with YAMNet. Overlay: chirp drift trace and a habits lineage bar.
- **Week 9, Transfer between two virtual Reachys.** Scripted keeper A with exaggerated settle time and three moment chirps. Hand the cartridge to Reachy B. Show base plus delta for dialect, `O_prev` with floor for habits, rituals offered as suggestions, etiquette reset, kettle paused for re-verify. Automated test: does B's droid still carry A's settle time at the floor after N compressed days?
- **Week 10, 3-person playtest.** Stranger vs owner identification of core vs moment chirps (design read, no stats at n=3). A two-alternative forced choice for habit noticeability ("which droid's settle is different?"), which doubles as your in-house JND test. A mini A to B to C chain if time allows. Demo video: twin droids plus the kettle beat.
- **Winter, real Reachy Mini and Pi 5.** Benchmark YAMNet TFLite and MediaPipe Pose lite on the Pi first, since both are unmeasured. Re-verify taught sounds on the robot's mic array (first real "new body" data). Speaker EQ page for chirp brightness. Arduino touch pad as a warm cue for chirp drift. Joint map for tilt and settle on Reachy and in Isaac Sim for the custom droid.
- **Spring.** Fresh vs worn vs someone else's worn, blinded. Family vs stranger chirp reading (the Pongrácz-beating claim). "Which droid was raised by you?" from motion alone. Custom droid to Reachy Mini: do settle and tilt survive the body change? Interviews on inheriting someone's rituals. Run 3 to 5 sessions before comparing to blunt novelty.

---

## Proposed decisions (continuing from D84)

| # | Proposal |
|---|---|
| **proposed D85** | Two-tier sound: locked core chirps on universal acoustic cues, plus family moment chirps that drift and inherit. |
| **proposed D86** | Chirp genome: identity genes (note count, contour class, binding) locked, accent genes drift within bands with per-play jitter and a per-gene drift cap. |
| **proposed D87** | Mint moment chirps after 5+ recurrences over 2+ weeks, enforce minimum distance between active chirps, cap at 12 to 20, archive on decay. |
| **proposed D88** | Dialect drift uses the shared reward interpreter and `decision_id`. Mute rolls back one step. Loudness, brightness and length are clamped. |
| **proposed D89** | Context and moment features use events, times, taught sounds and owner tags only. No voice or face identity. |
| **proposed D90** | Habits stores at most 7 summary numbers per keeper. Raw joint data never touches disk. Updates run in `tick` overnight, never live. |
| **proposed D91** | Habits map through Effort-style axes into patina dial offsets, kept in a separate field from patina wear. Add resting tilt and settle time to the abstract body vocabulary. |
| **proposed D92** | Habits offset capped at 25 to 35% of dial span, new-owner weight ramps over 4 to 6 weeks, owner strength dial with off. |
| **proposed D93** | Fade curves per plug-in: responses, rhythm and etiquette fade to 0. Dialect and habits fade to a 0.2 to 0.3 floor. Sounds and rituals persist as memories. |
| **proposed D94** | Rhythm = decayed per-weekday 96-bin histograms plus a Markov table. No deep sequence models on the droid. |
| **proposed D95** | Talk presence hard-blocks self-initiated actions. Etiquette learns from check-in outcomes, tightens freely, loosens only within a factory bound. |
| **proposed D96** | Home sounds = YAMNet embeddings plus owner-taught prototypes (5 to 10 examples, background negative, corrections). No raw audio. Prototypes treated as sensitive. |
| **proposed D97** | Practice handover: rituals and ribbon pass as read-only heritage offered as suggestions. Timing priors and etiquette reset. Sounds pass with detection paused until re-verified. Guest data never stored. |
| **proposed D98** | Pre-handover review screen lets the outgoing owner drop any chirp, ritual, sound or the habits layer. |
| **proposed D99** | A shared `moments` registry links rituals, sounds, chirps and bandit context through stable moment IDs with lineage. |
| **proposed D100** | Framing: "it picks up its keeper's habits". No convergence claims, no "apprenticeship learning" claim. |

## Research entries (continuing after the earlier list)

The earlier report listed R80 onward without numbering each item. Read in order, that list ends at R92, so these start at R93. Renumber if your log differs.

| # | Source | Confidence |
|---|---|---|
| R93 | [Steels 2002, crucial factors](https://langev.com/pdf../../pdf/steels02crucialFactors.pdf) | full text via summary |
| R94 | [Steels, Talking Heads book](https://langsci-press.org/catalog/book/49) | catalogue |
| R95 | [Kirby, Cornish & Smith 2008](https://stir.ac.uk/research/hub/publication/687799) | abstract. Numbers secondary via [Nat Geo](https://www.nationalgeographic.com/science/article/language-evolution-witnessed-in-lab-experiments), **verify** |
| R96 | [Read & Belpaeme 2016](https://pearl.plymouth.ac.uk/handle/10026.1/4407?show=full) | abstract |
| R97 | [Read & Belpaeme 2014, context](https://researchportal.plymouth.ac.uk/en/publications/situational-context-directs-how-people-affectively-interpret-robo/) | **title only, unconfirmed** |
| R98 | [Jee et al. 2010](https://dspace.kaist.ac.kr/handle/10203/94821?mode=full) | abstract |
| R99 | [Zhang & Fitter 2023, THRI review](https://api.crossref.org/works/10.1145%2F3583743) | abstract |
| R100 | [Burtt on R2-D2](https://designingsound.org/2009/09/10/ben-burtt-special-star-wars-the-sounds-part-2) | interview |
| R101 | [Gabaldon on Cozmo](https://designingsound.org/2016/11/15/sound-for-robots-an-interview-with-sr-sound-designer-ben-gabaldon/) | interview |
| R102 | [Brewster et al. 1993](https://www.dcs.gla.ac.uk/~stephen/papers/CHI93.PDF) | full via summary |
| R103 | [Pongrácz et al. 2005](https://czaw.org/?p=3568) | abstract |
| R104 | [Ogilvie on familects](https://prospectmagazine.co.uk/views/columns/62168/joy-of-lex-what-family-words-say-about-us) | column, anecdotal |
| R105 | [Furby](https://en.wikipedia.org/wiki/Furby) | Wikipedia |
| R106 | [IEC / Takagi 2001](https://en.wikipedia.org/wiki/Interactive_evolutionary_computation) | **secondary, Takagi not read** |
| R107 | [Brochu et al., preference BO](https://arxiv.org/pdf/1012.2599) | record only |
| R108 | [Chartrand & Bargh 1999](https://pages.ucsd.edu/~pwinkiel/chameleon.pdf) | full |
| R109 | [Tea-makorn & Kosinski 2020](https://www.gsb.stanford.edu/index%2ephp/node/501333) | abstract |
| R110 | [Sundman et al. 2019](https://liu.se/en/news-item/hunden-speglar-agarens-stress) | press release |
| R111 | [Bailenson & Yee 2005](https://vhil.stanford.edu/publications/avatars-and-agents/digital-chameleons-automatic-assimilation-nonverbal-gestures) | abstract |
| R112 | [Jonell et al. 2021](https://arxiv.org/pdf/2109.01206) | full, pilot n=12 |
| R113 | [Luo, Neff & Ng-Thow-Hing](https://www.cs.ucdavis.edu/~neff/papers/An%20Examination%20of%20Whether%20People%20Prefer%20Agents%20Whose%20Gestures%20Mimic%20Their%20Own.pdf) | full, venue unconfirmed |
| R114 | [Knight & Simmons 2016](https://ri.cmu.edu/?p=122282) | abstract |
| R115 | [Takayama, Dooley & Ju 2011](https://www.wendyju.com/publications/151r-takayama.pdf) | full |
| R116 | [Seol et al. 2013, Creature Features](https://mrl.snu.ac.kr/publications/creatureFeatures/creatureFeatures.htm) | abstract |
| R117 | [Meta Movement SDK body tracking](https://developers.meta.com/horizon/documentation/unity/move-body-tracking/) | docs, full |
| R118 | [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) | docs, full |
| R119 | [Nair et al. 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/nair-identification) | abstract |
| R120 | [Reitsma & Pollard 2003](https://ri.cmu.edu/?p=8709) and [Reitsma et al. 2008](https://ri.cmu.edu/?p=10106) | abstracts |
| R121 | [Minor & Cook, forecasting](https://eecs.wsu.edu/~bminor/publications/pmc16.pdf) | full, venue unconfirmed |
| R122 | [Fogarty et al. 2005](https://interruptions.net/literature/Fogarty-TOCHI05.pdf) | full |
| R123 | [Horvitz et al. 2004, BusyBody](https://erichorvitz.com/busybody_cscw.htm) | landing page |
| R124 | [Patel et al. 2023](https://ar5iv.labs.arxiv.org/html/2309.06252) | full |
| R125 | [Nolasco et al. 2023](https://darchive.mblwhoilibrary.org/entities/publication/8de3aa5a-22ba-4f50-b8f3-cb4cd5b5fd1b) and [Wang et al. 2020](https://research.adobe.com/publication/few-shot-sound-event-detection) | landing pages |
| R126 | [Wolters et al. 2021](https://arxiv.org/html/2107.13616v2) | full |
| R127 | [YAMNet tutorial](https://www.tensorflow.org/hub/tutorials/yamnet) and [ST model card](https://huggingface.co/STMicroelectronics/yamnet/blob/0a1a2dcdcc92789e8409d3ff43ef6906438412f1/README.md) | docs. Upstream license **unconfirmed** |
| R128 | [Ubicoustics](https://chrisharrison.net/index.php/Research/Ubicoustics) | project page |
| R129 | [Batra et al. 2025, CraftLink](https://arxiv.org/abs/2506.10891) | abstract, venue unnamed |

**Do not cite yet:** Turcsán et al. 2011 owner-dog personality matching, Sümegi et al., Zajonc 1987 couples, the "Kerry" familect survey, MavHome and Mozer's Neural Network House, Argall et al. 2009 LfD survey, Masuda et al. and Ribeiro & Paiva on Laban and animation. All unverified this round.

**Gaps, as far as we found:** no sourced drift rate or annoyance threshold for chirps, no long-term habituation data for robot sounds, no robot study of month-scale motion style absorption, no JND data for robot head tilt or settle time, no learning curve by day for a single desk user's routine, no real-home false-positive rates for user-taught sounds, no Pi 5 timings for YAMNet or MediaPipe, no study of people inheriting someone else's routine model.

---

## Conclusion

Underneath, the three spines share one data structure seen three ways: a list of moments that matter to a household, each with a sound, a way of moving and a place in the day, each stamped with whose layer it came from. Build the moment registry first and the rest becomes bookkeeping you can explain on an overlay.

The sharpest change from the earlier architecture is the fade curve. A bandit's inherited preferences should wear away, because a stranger's likes shouldn't steer the droid. Accent and habits should never fully wear away, because that trace *is* the heirloom. Getting that one asymmetry right, and showing it, is what lets Heirloom answer its core question with something better than yes or no.
