# Heirloom Rework Plan · Oct 22

*What the Oct 20 to 21 research changes, what it leaves alone, and tomorrow's order of work.*
Sources are R19 to R69 in `logs/research-log.md`. Ready-to-apply code is in `prep/oct22/`.

---

## 1. The verdict

The core idea survives and gets sharper. Body-to-body memory transfer already exists (LOVOT, RoBoHoN, aibo). What no one offers, as far as we found, is a companion that **keeps what it learned when it passes to a new person**. Sony erases an aibo's memory before it goes to a new home. LOVOT's memory dies with its subscription. Families have asked for a second-life path (Zhao 2026). That gap is Heirloom's.

Three things need real rework: the positioning, the handoff design (it ignores the previous owner's privacy), and how wear shows up in the demo (the dials are too subtle to carry it).

---

## 2. What breaks

**B1 · "Move to a new body" is not new.**
LOVOT (ghost transfer), RoBoHoN (farewell and reunion rituals), aibo (memory moved on repair) all do it for the same owner (R43, R48, R49, R50).
→ Lead with passing between people. Name the precedent openly. Say "as far as we found," never "no one does this."

**B2 · The cartridge hands a stranger the last owner's life.**
Sony erases aibo memory before fostering for a reason: the previous owner's faces, voices and habits shouldn't travel to strangers. Heirloom's handoff only lets the *receiver* choose (keep, blend, fade). The *giver* has no say, and after a death nobody can ask them.
→ Two-key handoff (D53): the giver decides what may pass, the receiver decides what to keep.

**B3 · "It learns you" is a weak selling point.**
Long-term AIBO owners ranked learning and memory about half as important as interaction (R45). Pleo lost families because its promised growth was invisible (R44).
→ Wear has to be felt in seconds, through motion and sound. The pitch should say "wears in," never "learns."

**B4 · The dials can't carry the demo.**
With the settling fix and realistic households, a loud family's droid after 12 years sulks 6.8 s instead of 6.0 s and notices you at 2.9 m instead of 2.5 m (`prep/oct22/README.md`). That's correct for Rule 4 (the core barely changes) and nearly invisible to a playtester.
→ Patina carries the fresh vs worn moment (D55). Patina moves up to week 7 to 8 as the most important build.

**B5 · The time skip's numbers were invented.**
Fixed in prep: totals from Bentley 2018, novelty over 3 weeks (Cagiltay 2022, Weiss 2021), quieter after year 1 (Luka, R10), weekend bump. The *mix* of moments is still a design assumption, labelled in every file.

**B6 · A pillar is contradicted.**
"Luka lasts because it has a job." The Luka study shows families kept it for years *after* its job ended, as a keepsake (R10).
→ Revised pillar: robots last when they become part of the family's story.

**B7 · Rule 5 has no code.**
The shelved household (Shen 2025: nobody used the robot past 6 months) just freezes. Absence leaves no trace yet, and neither does the shy-then-warm return.

**B8 · The most common real handoff is missing.**
Shen 2025 saw grandparents hand their robot to grandchildren while alive. The Wear System covers death, sale and splits, never a living gift.
→ Scenario 10 (D54).

**B9 · Weak-robot behaviour can slide into guilt.**
Okada's robots invite help. A droid that keeps asking becomes Tamagotchi (D44, R26, R39).
→ Boundary rule (D56).

**What holds (don't redo):** architecture, cartridge core, plug-in contract, D40 to D49, local-only privacy, grumpier sass. The research backs all of it. China's July 2026 rules now ban companion AI that fosters dependence or caters excessively (R58), which supports Rule 7, D41 and D44.

---

## 3. Creative opportunities

**C1 · The Introduction (trust passed hand to hand).**
When the old owner is present and warm toward the newcomer, the droid warms to the newcomer faster. A grandparent hands it over, waves at the grandchild, and the droid reads that as permission. It makes the living handoff a moment you can *see*, and it's playtestable in week 9: Riya hands the droid to a classmate.
*Design hypothesis, not research. Loosely like a child checking a parent's reaction before trusting a stranger.*

**C2 · The Will (形見分け, katamiwake).**
In Japan, a person's belongings are shared out as keepsakes after they die. Heirloom's owner marks moments over the years as "pass on" or "keep with me," with a physical gesture and no menu. At a handoff only "pass on" moments travel. Solves B2, pairs with D43 and D45.

**C3 · Hesitant when new, sure when worn.**
Okada: hesitation and wobble (ヨタヨタ) read as alive and invite people in (R51). Patina already says a fresh droid moves stiffly. Combine them: a fresh Heirloom pauses and wobbles before it acts, and a worn one answers instantly with its home's flourish. Same wave, two droids, visible in one second. This is the week 9 shot.

**C4 · Carry a piece forward.**
Behaviour moves on the cartridge. Physical wear stays in the old body. Design one "heirloom part" with the ID collaborator (iris ring or faceplate) that moves to the new body, worn metal and all. Precedent: aibo parts donated from funeral units for repairs (R43), kintsugi.

**C5 · Where your hands go, it shines.**
Wenwan walnuts and 経年変化: value comes from being handled (R54, R67). Make physical and behavioural wear rhyme: the touch points you use most polish to bare metal, and the interactions you use most become the most fluent. The MR overlay can show the "handled" map.

**C6 · Warmer words for the choices.**
Zhao's families used "resting" and "visiting another family" (R47). Rename the handoff choices in the ritual: keep → **carry**, blend → **soften**, fade → **let rest**. Code names stay.

**C7 · A thank-you bow.**
Okada's trash robot bows (ペコリ) before and after you help (R51). A small bow after a warm response joins the D48 loop.

**C8 · Memory left open (hold carefully).**
Talking-Bones forgets part of a story and children fill it in (R51). Heirloom could start an everyday memory and leave a gap for the owner. Never grief memories (D45). Idea only.

---

## 4. Proposed decisions (Riya's calls tomorrow)

| # | Proposal | Ready? |
|---|---|---|
| D50 | Settling learning for dials | Code in `prep/oct22/`, tests pass |
| D51 | Households v2 anchored to research, 4 profiles, mix labelled as assumption | Code in `prep/oct22/` |
| D52 | Positioning: Heirloom keeps what it learned when it passes to a new person. Name LOVOT, RoBoHoN, aibo as precedent | Text below |
| D53 | Two-key handoff: giver's will + receiver's choice (C2) | Needs cartridge flags + ritual design |
| D54 | Scenario 10: passing down while alive, with The Introduction (C1) | Design |
| D55 | Patina carries the fresh vs worn demo, dials stay subtle | Changes build order |
| D56 | Weak-robot boundary: hesitation is a fresh-droid trait that fades with wear (C3). It invites help once, never repeats, never sulks if ignored | Design rule |
| D57 | Pillar revisions (below) | Text below |
| D58 | Wake word stays as the voice gate for now. Revisit with owner naming. NICOBO shows a companion can skip one (R52), but Vosk in a loud room needs it | Hold |

**D52 positioning line options:**
1. "Every companion robot today either remembers you and stays, or moves to a new home and forgets. Heirloom remembers when it changes hands."
2. "Other robots move your memories to a new body. Heirloom passes its memories to a new person."
3. "Built to be inherited."

**D57 pillar revisions:**
- *Trust is earned over time:* add Hancock 2011 (performance predicts trust) and Scassellati's "day two" quote (R63).
- *Honest machines are loved:* add Mori 1970 primary (R65), Okada (R51), NICOBO (R52), Qian 2026 (more social presence reduced enjoyment, R60).
- *We keep what holds our story:* add wenwan walnuts (R54), A-FUN keeping scratches (R43), aibo funerals verified (R46), Roomba naming verified (R22).
- *Companion robots die with their companies:* add LOVOT memory erased on cancel (R47), Moxie shut down twice (R63), Sony's 7-year support window (R43).
- *Luka:* replace with "robots last when they become part of the family's story" (R10, R47, R61).
- *New, why now:* China's July 2026 rules ban dependence-building companion AI (R58). Pew 2026: majorities expect AI to put personal data at risk (R33).

---

## 5. Tomorrow

**Afternoon · headset (about 2 hours)**
0. *Laptop, 15 min.* Riya decides D50 and D51. Claude copies `prep/oct22/` into place, runs tests and the time skip.
1. **Wear overlay** (open item). Brain sends the dials in the `state` message. Unity overlay gets a toggle showing five small bars.
2. **Fresh vs loud-family Year 12** on the desk, one after the other. Expect the difference to be faint. That confirms D55.
3. **Direct the hesitation** (C3). Riya gives notes on how a fresh droid should pause and wobble on 2 expressions (wave, happy). Claude animates. This is the "new" end of patina.

**Night · laptop**
4. Riya's calls on D52 to D58. Claude logs them.
5. **Handoff ritual brief:** pick a direction (`docs/handoff-ritual-brief.md`, drafted tonight).
6. **Patina plug-in:** start the "worn" end (confidence, speed, household flourish).
7. FigJam: copy D39 onward and the research highlights.
8. Reading when there's energy: Mori 1970 (free on IEEE Spectrum), re-download the Okada J-STAGE paper.

**Still open, later this week:** presence events (`stayed_close`, `glance_ignored`, `left`), Rule 5 absence code, shared warm/cold signal, architecture.md update.
