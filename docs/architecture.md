# Architecture rules

Reachy Mini is a test body. The final output is a custom droid. These rules keep Reachy from getting baked in.

## The rules

1. **Robot SDKs are imported in exactly one place:** their adapter in `brain/heirloom/body/`. `reachy_mini` never appears anywhere else in the brain.
2. **The brain speaks Heirloom units.** Degrees, Heirloom channel names, positive pitch looks up. Adapters convert to each robot's units and sign conventions.
3. **Bodies declare what they can do.** Reachy has no iris, light or projector. The brain still sends those channels, and an adapter ignores what it doesn't have. In MR, Unity draws the missing parts (iris, projector beam) on top of the virtual Reachy.
4. **Expressions are Heirloom clips.** Keyframes on Heirloom channels, stored in `brain/expressions/`. Pollen's emotion clips can be converted into this format as placeholders, never played directly by the brain.
5. **The cartridge format is Heirloom's own.** Plain JSON and JPEG. Nothing robot-specific inside (see `cartridge-format.md`).
6. **Unity listens to the brain, never to the robot.** The MR app gets body pose, brain state and learned values from the brain's own WebSocket. Unity swaps the 3D model (Reachy now, custom droid later) without changing the protocol.

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
| NullBody | fall | prints commands. Unity is the only visual |
| ReachyBody (sim) | fall | validates the real Reachy API |
| ReachyBody (lab robot) | winter | same adapter, real hardware |
| DroidBody | winter to spring | Pi 5, smart servos, iris servo, LEDs, projector |

The transfer test in spring moves one cartridge from DroidBody to ReachyBody. That only works because neither body owns the brain.
