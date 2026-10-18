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
