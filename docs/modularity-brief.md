# Modularity Brief v0 (Oct 18) · Approved by Riya, step 1 built

## Goal
Adding anything to Heirloom (a gesture, a mannerism, a word, a feature, a body part) means **adding a module**, never editing the core brain. The software version of the twist-lock collar.

## Problem today
- Reactions are one growing `if/elif` chain in `brain.py`.
- Every gesture lives inside one function in `gestures.py`.
- Expressions and chirps are hard-coded in Python.
- Events are bare strings, so they can't carry extra info (tone of voice, which hand, a recording).

Already modular: bodies (Body interface, `reachy+unity`), and perception sources feeding one stream of events.

## The shape
```
SENSES  ->  EVENT BUS  ->  BRAIN CORE  ->  BODY
(plug-ins)  (one stream)   (modes + reactions)  (any body, reports its parts)
```

| Module type | What it is | Lives in | Example |
|---|---|---|---|
| **Sense** | Turns the world into events | `heirloom/perception/` | voice, tone, hands, keys, later camera, touch pad, mute switch |
| **Gesture** | One detector per file, plugged into the hands sense | `heirloom/perception/gestures/` (step 2) | `thumbs_up.py`, `heart.py`, Riya's `shh.py` |
| **Reaction** | What it does when an event arrives: motion, sound, mode change, when it's allowed | `reactions/*.json` (data) | `good.json` → happy + happy chirp |
| **Mode** | Behaviour with its own timeline and rules (needs code) | `heirloom/modes/` | sulk, sleep, back off, listening |
| **Expression** | Keyframed motion | `expressions/*.json` (data) | `sulk_recoil.json`, made with the pose recorder |
| **Capability** | A bigger feature with its own commands and storage | `heirloom/capabilities/` | voice memories, photo journal, projector |
| **Character** | Temperament dials (D22) that scale every reaction | `character.json` | sass 0.8 → longer sulks |
| **Body** | A physical or virtual body that reports which parts it has | `heirloom/body/` | Reachy, Unity, the custom droid |

## Rules
1. The core never names a specific sense, gesture, reaction, capability or body. It loads whatever is in the folders.
2. Events carry data: `{name, source, strength, data}`. Example: `{name: "good", source: "voice", data: {tone: "soft"}}`.
3. Parts are optional. A body reports its channels. A reaction that needs antennas on a body without antennas plays the rest and skips that part. **Swap the head module and the brain adapts.**
4. Every module can be tested alone (like `test_gestures.py`).
5. Learned things go in the cartridge, never in module files. Modules are the born-with character (Rule 4: the core never changes).

## Who builds what
- Claude: core loader, event bus, converting today's code into modules.
- Riya: `shh.py` gesture (first solo module), the pose recorder (Unity), new reactions as JSON, later voice memories.

## Decisions (Oct 18)
1. Reactions are JSON files. Anything with behaviour over time is a mode (Python), started by a reaction.
2. Missing body parts are skipped silently. "Noticing" them is not worth it. Instead: a later **self-maintenance** feature, where Heirloom indicates when something isn't working. Every module gets a `health()` hook now so that feature has something to plug into.

## Build steps
1. **Done:** events with data, mode plug-ins (`heirloom/modes/`), reaction files (`brain/reactions/`), core brain that names nothing specific. Riya writes the remaining reaction files (`tests/test_reactions.py` tracks them).
2. Gesture detectors as plug-ins, one file each. Riya writes `shh.py`.
3. Expressions as JSON files + the pose recorder in Unity (Riya).
4. Character dials (`character.json`) scaling reactions.
5. Capabilities: voice memories first.
