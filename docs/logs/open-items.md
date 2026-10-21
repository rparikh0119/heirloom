# Open Items

Anything that could fall through the cracks. Tick when done.

**Research**
- [x] Verify the Roomba naming study (R12) → Sung et al. 2007, UbiComp, 21 of 30 owners named theirs
- [ ] Verify the aibo funeral details (R13)
- [ ] Find a source for the indoor solar estimate (T05)
- [ ] Verify the DLP2000 specs (T04)
- [ ] Find a source for Tamagotchi's neglect design (R16)
- [ ] Check local speaker recognition speed on a Pi 5 (T07)
- [ ] Read Quartz / Kakoudaki (R05), Reactor (R06), r/movies WALL-E (R08)
- [ ] Identify IEEE paper 9223478 (R07)
- [ ] Check chosen gestures and touch (wave, head pat) for cultural differences (R14)

**Design calls (Wear System)**
- [x] Can layers be copied? → No (D17)
- [x] Per-person learning? → Yes, through nuance (D18)
- [x] Neglect? → Yes, shy then recovers, can't die (D19)
- [x] Hold switch? → Cut (D21)
- [x] What counts as a warm response, per channel? → v0 (D48)
- [ ] Does wear fade, or is it permanent? (leaning permanent)
- [ ] What does the handoff ritual look and sound like?
- [ ] How rare is memory surfacing?
- [x] Core temperament traits → five dials (D22)
- [x] Is every droid born different, or one designed personality? → one designed personality (D37)
- [ ] Demo droid dial settings
- [ ] Does it hold a grudge if you keep offending it? (D26)
- [ ] Naming: does the owner name it, and does that become the wake word? (D27)
- [ ] FigJam fixes: Scenario 7 points to "Rule 8" (now Rule 7). The behavior tree still mentions the hold switch (R7)

**Build**
- [x] Headset test of the Presence scene (passthrough + hands) → works over Link, Oct 18
- [x] Reachy sits slightly inside the desk in MR → fixed Oct 18
- [ ] Log the bugs seen in the first headset test
- [x] Talk and Gesture v0: voice listener tested with the laptop mic, and in Unity
- [ ] Talk and Gesture v0: hand gestures (brain-side, D28), built and passing synthetic tests. Test with real hands and tune thresholds
- [ ] Left Quest controller not connecting (battery or re-pair)
- [x] Reachy antennas not showing in Unity → visible and moving in the Oct 18 recording
- [ ] Head-yaw and base-yaw directions on the Reachy simulator (only pitch confirmed there)
- [ ] Write the Wear System design brief
- [x] Wear System risks R-1 to R-8 answered (D40 to D47)
- [ ] Cartridge v1 format brief (must cover D43, D45, D46)
- [ ] Check whether the Quest passthrough camera API works over Link

**Gaps found Oct 21 (wear system)**
- [x] Test key presses pollute the cartridge → keys ignored unless --learn-from-keys
- [x] Nothing calls health() → run.py prints a health report at startup
- [ ] Wear can't be seen: send effective dials in the state message, overlay toggle with five bars (needs headset)
- [ ] Presence events: noticed, stayed_close, left, glance_ignored (unblocks boldness up, curiosity down, D44, D48)
- [ ] Shared warm/cold signal after each reaction (before dialect)
- [ ] Brain accepts a pretend date (for the time skip)
- [ ] Handoff ritual design brief (week 7 or 8, blocks the week 9 station). No settings menu
- [ ] Update architecture.md and modularity-brief.md for the cartridge + wear plug-ins
- [ ] Replace the v0 example cartridge (brain/cartridges/example)
- [ ] Decide: commit cartridges/riya to git (backup) or gitignore it

**Hardware**
- [ ] Update the hardware sheet: supercapacitor, NiMH pack, modular connectors, ID chips
- [ ] Which Reachy Mini the lab has (Lite or Wireless), how many, can two be reserved in winter
- [ ] Contents of the lab sensor kit
- [ ] Projector choice
- [x] Rolling vs turntable → rolls (D23)
- [x] Power for a rolling droid → rechargeable lithium allowed (D39)
- [ ] Cliff sensors + wheel module
- [ ] Internal packaging: block out every component at real size (Blender boxes or foam) before any more styling. Likely total height 25 to 30 cm, not 18 cm
- [ ] Verify sizes: ReSpeaker XVF3800 board, Dynamixel XL330, laser pico module, Reachy Mini overall height
- [ ] Modular design language to explore with the ID collaborator: stacked modules joined by one standard twist-lock collar, like a camera lens bayonet mount (any head fits any neck fits any base)

**Collaboration and class**
- [ ] ID collaborator: scope, timeline, winter-break modelling handoff
- [ ] Next assignment / progress check (likely within ~2 weeks, not yet released)
- [ ] Update speaker notes on deck slides 8, 11, 13
- [ ] Real quarter calendar and due dates
- [ ] Devlog post: tonight's reactions clip
