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

**D05 · Power, avoiding lithium** · Oct 16 · Decided
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

**D14 · A fixed core temperament** · Oct 16 · Proposed
- Choice: each droid is born with traits that never change (sass, shyness, curiosity). Wear adds flavour on top.
- Why: R02 (loyal through change, sass), R09 (stable core), avoids a people-pleaser.

**D15 · Process: brief before build, logs on FigJam** · Oct 16 · Decided
- Every feature gets a one-page brief (thesis link, research, feel, test) signed off by Riya before code.
- Logs live on the FigJam board (Riya maintains). Plain-text copies in docs/logs/.
