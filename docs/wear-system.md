# The Wear System (v0 design)

Heirloom's signature idea in code: **every interaction leaves a trace, traces build up in layers, the layers shape how it behaves, and the layers can be passed on.**

The brain built so far (presence, reactions, chirps, modes) is the canvas. Wear is what makes a 10-year-old Heirloom different from a new one.

## Design target

**The everyday person:** never opens a settings menu, never reads a manual. Every choice happens through the droid itself and its physical controls. Approach: "solve for one, extend to many."

## Rules (every learning behaviour must follow these)

1. **It learns your warmth.** It learns which responses mean "warm" in your home: voice, gestures, body language, distance, touch.
2. **Relationships, not accounts.** Learning belongs to the household or place. No logins, no profiles. Inside the household it learns its regulars through nuance (voice, height, rhythm). Strangers are guests. It can get you wrong and do a double-take.
3. **Nothing is erased unless you choose.** Every layer can be kept, rested (kept but quiet) or wiped.
4. **The core never changes.** Its temperament is fixed for life. Always recognisably itself, always predictable.
5. **Absence leaves a trace.** Time apart changes it. It's shy at first, then warms back up faster than a new droid. It can never die.
6. **Ownership changes through a ritual.** Moving the cartridge is the handoff. You see its history before you choose what to keep. Only one droid ever holds the wear.
7. **It isn't built to please you.** It has moods, preferences and opinions. That's what makes its affection mean something.

## Scenarios (the rules must survive all of these)

| # | Scenario | Answer | Rules |
|---|---|---|---|
| 1 | The owner dies | The grandchild rests Grandma's layer. Kept, never erased, memories only when invited | 3, 4, 6 |
| 2 | A family shares one droid | One household. Inside it, it learns its regulars. Strangers are guests | 1, 2 |
| 3 | Sold to a stranger | It shows a few moments from its past. The stranger chooses keep, rest or wipe | 3, 6 |
| 4 | Split household | Only one droid keeps the wear. Journal photos can be copied | 3, 6 |
| 5 | Different bodies and abilities | Warmth through any channel. Wear changes style, never meaning | 1, 4 |
| 6 | Different cultures | It learns a home's warmth instead of assuming one | 1 |
| 7 | Neglect | Shy after time on the shelf, warms back up fast. It remembers you. It can't die | 5, 7 |
| 8 | Wear is fundamental | It changes slowly enough that it never feels like a different droid | 4 |
| 9 | An institution | The household layer becomes a place layer: the classroom's droid | 1, 2 |

## Four faces of wear

| | What wears in | What you notice | Physical analogy |
|---|---|---|---|
| **Patina** | Motion | Expressions it uses often get smoother, quicker, more confident. Rarely used ones stay stiff and hesitant | Brass wearing through to bare metal where hands touch |
| **Dialect** | Sound | Chirps drift toward what the household responds to warmly. Each home ends up with its own vocabulary | Family nicknames and inside jokes |
| **Rings** | History | Each owner's learning is its own layer. Visible as rings in MR. A new owner can keep, blend or fade each one | Tree growth rings |
| **Memory** | The journal | Old photos surface on their own at quiet moments: this week last year, the first day it met you | A grandparent bringing out the album |

## Data model: cartridge v1

```
personality.json
  droid:   name, born, awake_hours
  layers:  one per owner, oldest first
    owner, since, until
    status: active | keep | blend | fade | wiped      (how much it still counts)
    patina:  { expression: { uses, last_used } }
    dialect: { meaning: { genome, score, uses } }      (genome = chirp recipe settings)
    habits:  { setting: bandit stats }                 (check-in timing etc.)
    moments: [ { photo, taken, tag } ]                 (links into journal/)
journal/   photos (JPEG) + journal.json
```

The **effective personality** is a weighted blend of all layers: active and keep count fully, blend counts half, fade shrinks over weeks, wiped counts zero.

## Mechanisms

**Patina.** Wear per expression: `w = 1 - exp(-uses / 40)` (0 = brand new, about 1 after a few hundred uses).
- Duration shrinks up to 30% (confident). Amplitude grows slightly.
- Easing goes from stiff (a small hesitation at the start, linear moves) to smooth (eased).
- A tiny household "flair" (offsets seeded from the layer) so two worn droids don't move identically.

**Dialect.** Each meaning (hello, happy, notice...) has a chirp genome: pitch, speed, glide range, number of notes, wobble.
- Every play is a small mutation of the current genome.
- A warm response within a few seconds (praise, waving back, staying close, later a touch) pulls the genome toward that variant. Cold responses ("not now", walking away) push away from it.
- Over months the sounds drift into a household dialect. A new owner inherits the old genome, so they hear the last family's voice.

**Rings.** A new owner starts a new layer through a handoff ritual. The MR overlay shows rings around the base: one per owner, thickness = time together, each owner a different colour. Selecting a ring shows what it holds.

**Memory.** At quiet idle moments, if a journal photo matches the date or time of day (anniversary, same hour), it projects it with a soft "remember" chirp. Rare by design, so it stays special.

## The time skip

Wear needs years, and a demo has minutes. A **simulator** runs a synthetic household through months of interactions at high speed and writes a worn cartridge ("12 years with one family"). That makes wear visible instantly, and it powers the pitch's time-skip hook and the spring "fresh vs worn" playtest.

## Build order

1. Cartridge v1 + layers (save, load, blend)
2. Patina in the expression player
3. Dialect: chirp genomes, mutation, reward
4. Time-skip simulator
5. Rings overlay in MR
6. Journal + memory surfacing (webcam now, Quest camera later, projected on the desk)
7. Handoff ritual + transfer to a second Reachy (keep / blend / fade)
8. Real inputs: voice, gestures, touch (headset, then hardware)

## Open design questions (Riya's calls)

- What counts as a **warm response**, per channel?
- Does wear ever **fade** if unused, or is it permanent like patina on metal? (leaning permanent)
- What does the **handoff ritual** look and sound like?
- How rare should **memory surfacing** be?
- **Core temperament:** which traits, and how many?
