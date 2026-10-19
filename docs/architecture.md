# Architecture rules

Reachy Mini is a test body. The final output is a custom droid. These rules keep Reachy from getting baked in.

## The rules

1. **Robot SDKs are imported in exactly one place:** their adapter in `brain/heirloom/body/`. `reachy_mini` never appears anywhere else in the brain.
2. **The brain speaks Heirloom units.** Degrees, Heirloom channel names, positive pitch looks up. Adapters convert to each robot's units and sign conventions.
3. **Bodies declare what they can do.** Reachy has no iris, light or projector. The brain still sends those channels, and an adapter ignores what it doesn't have. In MR, Unity draws the missing parts (iris, projector beam) on top of the virtual Reachy.
4. **Expressions are Heirloom clips.** Keyframes on Heirloom channels, stored in `brain/expressions/`. Pollen's emotion clips can be converted into this format as placeholders, never played directly by the brain.
5. **The cartridge format is Heirloom's own.** Plain JSON and JPEG. Nothing robot-specific inside (see `cartridge-format.md`).
6. **Unity listens to the brain, never to the robot.** The MR app gets body pose, brain state and learned values from the brain's own WebSocket. Unity swaps the 3D model (Reachy now, custom droid later) without changing the protocol.

7. **The brain core names nothing specific.** It loads reactions (`brain/reactions/*.json`) and modes (`brain/heirloom/modes/`) from their folders. Adding behaviour means adding a file. See `modularity-brief.md`.
8. **Senses only measure, the brain decides.** Unity sends raw hand joints and head position. Voice is heard in the brain. Gestures, words and tone are interpreted in the brain, so they carry over to the robot's own camera and mics.
9. **Every module can report its health** (`health()`), for the future self-maintenance feature.

## The loop

```
SENSES (voice, hands, keys, later camera / touch / mute switch)
   -> EVENTS  {name, source, strength, data}
   -> REACTIONS  (reactions/*.json: motion, sound, mode change, when allowed)
   -> MODES  (sulk, sleep, back_off, listening: behaviour over time)
   -> PRESENCE + EXPRESSIONS  -> one pose per tick
   -> BODY  (Unity, Reachy, later the droid)
```

## Heirloom channels (v0)

| Channel | Unit | Notes |
|---|---|---|
| `head_pitch` | degrees | positive = look up |
| `head_yaw` | degrees | positive = look left |
| `head_roll` | degrees | positive = tilt left |
| `base_yaw` | degrees | positive = turn left |
| `antenna_left`, `antenna_right` | degrees | 0 = upright |
| `iris` | 0 to 1 | 0 = closed, 1 = wide open |
| `light` | 0 to 1 | warm glow brightness |

Sound and projector are events, sent separately.

## Body roadmap

| Body | When | Adapter |
|---|---|---|
| NullBody | fall | prints commands |
| UnityBody | fall | streams poses to the MR app over the link (ws://<pc>:8765) |
| ReachyBody (sim) | fall | validates the real Reachy API |
| ReachyBody (lab robot) | winter | same adapter, real hardware |
| DroidBody | winter to spring | Pi 5, smart servos, iris servo, LEDs, projector |

The transfer test in spring moves one cartridge from DroidBody to ReachyBody. That only works because neither body owns the brain.

## Link protocol (v0)

Brain → Unity, JSON text frames over WebSocket on port 8765:

```json
{"type": "pose", "ch": {"head_pitch": 0, "head_yaw": 0, "head_roll": 0, "base_yaw": 0,
                        "antenna_left": 0, "antenna_right": 0, "iris": 0.6, "light": 0.5}}
```

Every frame carries every channel. Bodies can be combined with `+` (e.g. `reachy+unity`) to drive the sim and the MR view at once.

Also brain → Unity:
```json
{"type": "state", "mode": "sulk", "user_distance": 0.8, "expression": "offended"}
{"type": "sound", "name": "grumble", "wav_b64": "..."}
```

Unity → brain:
```json
{"type": "user", "head": [x, y, z]}
{"type": "event", "name": "good"}
{"type": "hands", "left_tracked": true, "left": [x, y, z, ...26 joints], "right_tracked": false, "right": [...]}
```
Positions are metres in robot space: from the robot's head at rest, x right, y up, z forward. Hand joints follow the OpenXR / Unity XR Hands order (see `brain/heirloom/perception/gestures.py`). In winter, MediaPipe hand points from the robot's camera will be mapped into the same format.
