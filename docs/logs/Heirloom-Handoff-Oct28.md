# Heirloom Handoff, Oct 28, 2026

Read this first in a new chat. It covers the Oct 27 night session. For everything before that, read `claude/Heirloom-Handoff-Oct27.md` (still valid except where this file says otherwise).

Riya's working style: concise, direct, personality-driven. No em dashes, no semicolons, no performative framing, no "it's this, not that" phrasing. Push back with reasons. Credible, verified research, flag uncertainty, say "as far as we found". Never tell her to stop or take a break. Run commands start with `cd E:\HEIRLOOM\brain` then `.venv\Scripts\activate` (forgetting the venv gives "No module named numpy"). Remind her to `git add -A`, commit and `git push`. Log decisions and research in `E:\HEIRLOOM\docs\logs\`. Don't crowd this Project with docs.

---

## 1. Where things stand

- Riya filmed (or is filming) Oct 28 for a progress video due Tuesday Nov 3. She then can't work for ~3 days.
- Shot list: `E:\HEIRLOOM\docs\shoot-oct28.md` (sections A base features, B routines + family chirp with demo clock, C passed down, D fresh vs worn, E PC B-roll, F learning loop, optional).
- Decision log now runs to **D106**. D101 wheels dropped, D102 no move to the real Reachy Mini (Riya's call, the project plan still needs updating, ask her to confirm), D103 demo clock + moment overlay, D104 learning loop, D105 dialect drift, D106 keeper habits. D74 to D100 stay reserved for the research proposals. D74, D75, D77, D78, D79 (learning loop), D86, D88 (drift), D90, D92, D93-habits (habits) are now built as v0 and logged under D104 to D106.
- Tests: everything passes except `test_shh` 5/6 (Riya's own exercise). New suites: test_demo_moment 8, test_learning 13, test_dialect_drift 7, test_habits 12.
- Unity scripts changed several times tonight (HeirloomLink.cs, WearOverlay.cs) and were **never compiled** (Claude can't compile Unity). First thing: check the console.
- Last commit Riya confirmed: "Dialect drift (D105)...". Habits (D106) and the ROUTINES rename were written to disk after that and may not be committed yet.

## 2. Built Oct 27 night

**Demo clock (D103).** `run.py --clock 9:58` fakes the time of day so a routine (moment) fires on camera. Overlay says "demo clock". Panel shows NOW + family chirp + lineage + a ROUTINES list (moments, renamed from HABITS on screen). `scripts/demo_cartridges.py` rebuilds `cartridges/demo/` (fresh, desk_student_year1, desk_student_passed_on, loud_family_year12). Only real waves or voice trigger moments, never number keys.

**Chirp variety fix.** genome.py got three new breeding moves (pickup, stutter, hold). 40 droids now breed 5 distinct family hellos (was 2), curious 5 (was 1). Measured, **not yet heard**.

**Learning loop v0 (D104), `--learn` only.** Thompson sampling over authored moves for wave / good / heart (reaction files list `choices`). Bucket = cue × time of day. Reward: thumbs up / heart within 6 s = 1, "no" / "not now" / "shh" / middle finger = 0, silence or another command = skip. Quiet-only moves for 2 min after a miss. Fading 0.98, cap 30. Inherited tallies count at 0.3 × layer weight, max 10. Log: `<cartridge>/logs/decisions.jsonl`. Prior softened (designed move 2.5/3.5, others 1/2.5) because praise-only owners barely moved the first version. **Open for Riya: a fresh droid now plays its designed move only ~60% of the time. OK?** `scripts/learn_sim.py` prints fake-owner curves.

**Dialect drift (D105), `--learn` only.** Each family chirp play is varied (pitch ±3%, lengths ±8%, wobble ±20%). Warm reaction nudges the stored chirp 10% toward what played. Identity locked (note count + directions). Caps ±12% pitch, ±20% length. Homonym filter (never closer to another chirp, ancestors excluded). Only the active keeper's copy drifts. Pace: always-warm-to-higher home +2.2% after 30 mornings, +8.9% after 120.

**Keeper habits (D106), `--learn` only.** Wrist + head motion in memory, consolidated into 7 numbers when it hears good night ("dreaming"). Moves 1/30 per day, new keeper ramps over 35 days, cap 30%, old keeper fades to a 0.25 floor over 180 days, per-layer strength 0..1. Synthetic test: tempo, amplitude, stillness, tilt are reliable. Directness weak. Smoothness and settle unmeasurable at 30 Hz with jitter smoothing, so TRUST = 0 for them until checked on real hands. Unity now sends head roll (sign unchecked). Overlay "moves like: ...".

**Meaning check.** Riya's on-camera lines scored 20/20. Added exact phrases for "give me a minute" and "time for bed". `meaning_check.py --file scripts/my_lines.txt` tests her own lines. Teaching phrase "beep boop buddy" sits at 0.45 toward offended: pick one under 0.40 (candidates in the last chat: zoop zoop, bleep bloop, hey noodle, yo pickle).

## 3. Discussed, not built

- **Microduck** (Pollen + Hugging Face, $399, pre-orders Aug 27 2026, "Made to move · Ready to learn"). Learns motor skills you train in sim and publish to everyone. Heirloom learns one household and keeps it. Put it on the precedent slide as a contrast. Avoid "learns" alone in the pitch. Watch the cream colourway overlap: lean on oxblood, worn metal, repairs.
- **Web simulator like Microduck's:** not worth it this quarter. Maybe a 2D time-skip web page in spring (slider through years, hand it down). Riya said no for now.

## 4. Open items (priority order)

1. Unity console check, then shoot per the shot list. Headset checks for the new overlay lines, `--learn`, habits roll sign.
2. Riya listens: dialect_listen (new variety), drifted chirps.
3. Answer: fresh droid ~60% designed move OK? D102 confirm + update the plan.
4. Measure Quest hand jitter at rest (log a minute of still hands). Then decide habits TRUST for smoothness/settle.
5. Hardware plan + parts list for the satellite program (week 10). Riya says it won't take long. Lee Cody meeting prep.
6. Still open from Oct 27: renumber research entries after R79, recheck Fu et al. 2025 and Kirby numbers, older carried items (D43 question, shh.py, presence events, handoff ritual direction, deck/FigJam updates, roommate photo privacy note).
7. Not built from the reports: tone/prosody (D76, EU emotion-recognition risk), named intents (D80), per-body pages (D82), migrate() (D83), practice rhythm spine, mute rollback for drift (needs the toggle), handoff review screen.
