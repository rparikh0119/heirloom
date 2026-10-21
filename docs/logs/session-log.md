# Session Log

---

## Oct 16, 2026 (evening session)

**Built**
- Repo on GitHub (github.com/rparikh0119/heirloom) with Git LFS. Unity 6.3 project with Meta XR SDK, OpenXR, Presence scene (camera rig, passthrough, hand tracking).
- Reachy Mini model imported, physics stripped, posed directly from the brain.
- Brain ↔ Unity link (WebSocket, both directions). Brain drives the Reachy simulator and Unity through the same body interface.
- Presence: breathes, notices a person within 2.5 m, looks at them with head and base, glances around when alone.
- State overlay above the robot.
- Reactions (keys 1–6 standing in for gestures and voice): hello, happy, back off, sleep, wake, curious. Chirps synthesised in the brain and played from Reachy's head.

**Broke, and why**
- Git refused the E: drive (no ownership records) → `safe.directory`.
- Simulator closed instantly → its media server choked on PC audio → `--no-media`.
- Installing reachy-mini aborted → it needs a newer pip, and Windows blocks pip upgrading itself → `python -m pip`.
- NativeWebSocket clashed with Meta's Voice SDK → own client.
- "Look up" turned the head sideways → URDF part frames point in odd directions → measure axes from the robot root.
- An indentation slip in Python → fixed.

**Learned**
- Sense → think → act loop. Changing one dial at a time. Easing makes motion feel alive.

**Reflection**
- We moved fast on table-stakes behaviour (2018 Vector territory) and lost sight of the core idea. Course correction: the Wear System, research and decision logs, and a design brief before any new feature.

**Next**
- Review these logs. Write the Wear System brief. Answer the four design calls.

---

## Oct 18, 2026

**Built**
- Quest 3 over Meta Horizon Link: first headset test. Reachy sits on the real desk in MR, follows your head, every reaction triggers. Slightly sunk into the desk.
- Talk and Gesture v0 brief (D25). Brain side: offline voice listener (Vosk) with a wake word (D27) and intent phrases. New reactions: scold ("no"), offended + sulk + forgive (D26), listening perk-up. Every mode now eases in and out. Keys 7 to 9 added in Unity.

**Broke, and why**
- Left controller won't connect → not needed, hands work.

**Next**
- Test voice with a real mic. Hand poses in Unity. Fix desk height.

---

## Oct 20 to 21, 2026 (laptop, no headset)

**Built**
- Wear System risks R-1 to R-8 researched and decided (D40 to D48). D39 (lithium) added to the log.
- Cartridge format v1 cut to one page: a small core plus wear plug-ins, with the plot test ("does it change what the next owner meets?").
- Cartridge core (`heirloom/cartridge/core.py`) with 13 tests: layers, handoff, weights, fade, unknown files kept, safe saves.
- Dials wear plug-in (`heirloom/wear/dials.py`, rules in `brain/wear/dials.json`), grumpier when mistreated (D49). Brain runs with `--cartridge`.
- Unity key presses no longer leave wear. Startup health report.
- Time skip v1 (`scripts/time_skip.py`): households live years in seconds.

**Broke, and why**
- Time skip showed fixed nudges race every dial to the cap within a year. Fix prepared (settling learning, prep/oct22).
- Household numbers were invented. Rebuilt from Bentley 2018 and novelty research (prep/oct22).
- Ran tests from the repo root by mistake → run them from `brain\`.

**Research**
- About 50 new sources (R19 to R69), many found by Riya, including Chinese and Japanese work.
- Big finding: LOVOT, RoBoHoN and aibo already move memory into new bodies. Sony erases aibo memory before a new home. Heirloom's gap is passing what it learned to a new person.
- Okada's weak robots, wenwan walnuts and 経年変化 give the wear story its cultural grounding.

**Learned**
- Search wider and in other languages, follow citation chains, and never claim something doesn't exist without looking hard.

**Next**
- docs/rework-plan-oct22.md. Afternoon headset, night laptop.
