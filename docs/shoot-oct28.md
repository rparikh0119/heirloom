# Shoot · Oct 28 · progress video for Tuesday

*Every working base feature, in the order that needs the fewest restarts.*

Every terminal starts with:
```
cd E:\HEIRLOOM\brain
.venv\Scripts\activate
```

---

## 0. Before the headset goes on (10 min)

1. `python scripts\demo_cartridges.py`. Rebuilds the four demo droids so their simulated years end today. Run it again between takes of shots 9 and 10 if you want a clean state.
2. Unity: open the project, check the console has no red errors (HeirloomLink.cs and WearOverlay.cs changed last night). Press Play once without the headset to see the panel.
3. **Recording test, 15 seconds.** Run shot 1, record with the Quest's own capture, then check the clip on the PC. You need to see three things: passthrough, the robot, and the chirps audible. Over Link it's possible the headset capture misses the PC app or its audio. As far as I know this isn't reliable either way, so test it before filming anything else. If it fails, fall back to the Unity Game view in OBS plus a phone filming you from behind.
4. OBS (optional): record the terminal too. The `[event]`, `[understood]`, `[moment]` and `[learned]` lines make strong B-roll for a non-robotics audience.
5. Overlay: press **W** (Game view focused) to show or hide the wear panel. Keep it hidden for the feature shots and show it for shots 8 to 11.

---

## A · Base features (one run, worn droid)

```
python scripts\run.py --body unity --voice --mic 2 --cartridge cartridges\demo\desk_student_year1
```
A worn droid moves fluently, so the features read better. Heads up: if you film between about 9:20 and 10:45 am for real, a real wave will also trigger the 10 am moment. That's fine, just don't be surprised.

| # | Shot | Do / say | What should happen |
|---|---|---|---|
| 1 | Presence | Walk in from across the room, sit at the desk. Lean left and right. Step away. | Notice chirp at about 2.7 m, head and base follow you, glances around when you leave. |
| 2 | Hands | Wave. Thumbs up. Beckon. Palm out. Heart with both hands. | hello, happy, curious, backs off, love. |
| 3 | Voice, exact | "hello", "good job", "come here" | Same reactions, no wake word needed up close. |
| 4 | Voice, any phrasing | "you're such a good little robot", "I'm so proud of you" | Understood by meaning (terminal shows `[understood] ... (meaning 0.6x)`). |
| 5 | It asks instead of guessing | "what's the weather like" | Head tilt, "huh?" chirp. |
| 6 | It learns your word | "beep boop buddy" → huh? → wave within 6 s → say "beep boop buddy" again | "oh, got it" chirp, then it answers the phrase as hello. Terminal shows `[learned]`. |
| 7 | Sulk and forgive | Middle finger (or "get lost"). Then thumbs up. Then "I'm sorry" or a heart. | Turns away and sulks, ignores praise, forgives on sorry or heart. |
| 8 | Sleep and wake | "good night". Thumbs up. "good morning". | Yawns and sleeps, ignores praise, stretches awake. |
| 9 | Voice memory | "remember this", then say one sentence. Then "let me hear it". | Records, "recorded" chirp, plays it back through the tape filter between two soft chirps. |
| 10 | Photo | Two-hand frame (or "take a picture"). Then "show me a memory". Then "not now" while it projects. | Countdown beeps, shutter, photo projected on the desk, "not now" retires that photo for good. |

---

## B · Habits and the family chirp (the new stuff)

Overlay on (W).

**B1. Contrast, any wave is just hello**
```
python scripts\run.py --body unity --voice --mic 2 --cartridge cartridges\demo\desk_student_year1 --clock 14:00
```
Wave with your hand (a real wave, number keys never count). Core hello chirp. Panel shows "14:00 demo clock" and the ROUTINES list, nothing lit.

**B2. Same wave at its usual time**
```
python scripts\run.py --body unity --voice --mic 2 --cartridge cartridges\demo\desk_student_year1 --clock 9:58
```
Wave. Panel lights **NOW wave around 10:03**, "family chirp", "seen on ~200 days since Oct 2025". The chirp is the family version of hello. The NOW line stays up for 1.5 to 2.5 minutes, so there's time to frame it.

Say it on camera or in the edit: the time is faked so it can be filmed now, and the panel says "demo clock".

---

## C · Passed down (preview of week 9)

```
python scripts\run.py --body unity --voice --mic 2 --cartridge cartridges\demo\desk_student_passed_on --clock 9:58
```
The same droid, handed to a new keeper today. Before you wave, the ROUTINES list shows the old keeper's routines marked "· L1". Wave. Panel: **NOW wave around 10:03**, "family chirp, passed down", "passed down from keeper L1 · a student at a desk". It greets the new keeper with the first keeper's hello.

This is the core question of the project, answered on camera: what it learned comes with it.

---

## D · Fresh vs worn, side by side

Two terminals, Unity scene with both droids.
```
python scripts\run.py --body unity --voice --mic 2 --port 8765 --cartridge cartridges\demo\fresh
python scripts\run.py --body unity --port 8766 --cartridge cartridges\demo\loud_family_year12
```
Only one brain gets the mic. Use hands for the worn one, or give each its own take. Wave at each, thumbs up at each. Fresh is stiff and hesitant, worn is fluent with the home's flourish. Overlay on shows FRESH vs LOUD FAMILY YEAR 12 dials and patina bars.

---

## E · B-roll from the PC (no headset, any time)

- `python scripts\time_skip.py --profile desk_student --years 1`. The "habits it noticed" lines.
- `python scripts\dialect_listen.py`, then play `00_all_in_a_row.wav` over the B shots.
- `python tests\test_wear_moments.py`. A screen of PASS lines.
- `python scripts\learn_sim.py`. Learning curves for 30 fake owners, including a droid passed to a new keeper.

---

## F · Learning loop (optional, first time it's on camera)

```
python scripts\run.py --body unity --voice --mic 2 --cartridge cartridges\demo\fresh --learn
```
Overlay on. Wave, wait for its answer, then thumbs up only when it answers with the **happy wiggle** and say "no" for anything else. Leave about 5 seconds between waves. In the fake-owner sim the wiggle wins most waves after 10 to 20 of these, so plan on a long take and cut it down. The panel shows "trying something new" and "landed (thumbs up)" / "missed ("no")" as it goes. After a "no" it only answers quietly for 2 minutes. That's a guard, not a bug.

Family chirp drift: run `desk_student_year1 --clock 9:58 --learn`, wave, then thumbs up right after the family hello. The panel shows "family chirp drifted: +0.x% pitch". One step is tiny on purpose, so this is a panel shot, not an audio one.

It's untested in the headset. If it misbehaves, skip it and use the sim as B-roll instead:
`python scripts\learn_sim.py` (about a minute, prints the learning curves).

---

## Skip

- Rolling (dropped with the wheels, sim experiment only).
- The shh gesture (`shh.py` is still your exercise). Saying "be quiet" works.
