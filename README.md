# Heirloom

A small desk companion droid built to be kept for decades and passed down. It keeps your family's journal, adapts to your habits, runs locally, and stores everything it learns on a memory cartridge you own.

SCAD ARVR 455 capstone by Riya Parikh, RP.Studiio.

## One brain, any body

Heirloom's brain never talks to a specific robot. It talks to a **Heirloom body**: a small set of channels in Heirloom's own units (head pitch, yaw and roll, base yaw, antennas, iris, light, sound, projector). Each robot gets a thin adapter.

```
                 Quest 3 MR app (Unity)
        voice, hands, body in  ·  droid, overlay, projection out
                          ⇅  WebSocket (Heirloom protocol)
                    Python brain  (no robot code)
     state machine · perception · learning · cartridge · expressions
                          ⇅  Body interface
   ┌──────────────┬───────────────────┬──────────────────────┐
   NullBody       ReachyBody           DroidBody
   Unity only     Reachy Mini sim      custom droid
   (fall)         + lab Reachy         (spring, Pi 5 + servos)
                  (fall test, winter)
```

**Reachy Mini is a test body.** It's used for behavior testing this fall and winter. The final droid is my own. See `docs/architecture.md` for the rules that keep Reachy from leaking into the brain.

## Repo layout

| Folder | What lives there |
|---|---|
| `unity/HeirloomMR/` | Unity 6 project, the Quest 3 mixed reality app |
| `brain/heirloom/` | The brain. Robot-agnostic |
| `brain/heirloom/body/` | Body interface plus one adapter per robot. The only place robot SDKs are imported |
| `brain/expressions/` | Expression clips in Heirloom's own format |
| `brain/cartridges/` | Memory cartridges: `personality.json` plus `journal/` |
| `brain/scripts/` | Small runnable test scripts |
| `docs/` | Architecture, cartridge format, hardware breakdown, devlog, deck |

## Setup

### Git
1. Install [Git LFS](https://git-lfs.com), then run `git lfs install` once.
2. Models, textures, audio, video, decks and spreadsheets go through LFS automatically (`.gitattributes`).

### Unity
1. Unity Hub → New project → **Universal 3D (URP)**, Unity 6 LTS, with **Android Build Support**.
2. Name it `HeirloomMR`, location `E:\HEIRLOOM\unity`.
3. Edit → Project Settings → Editor: **Version Control = Visible Meta Files**, **Asset Serialization = Force Text**.
4. Install the **Meta XR All-in-One SDK**. Enable passthrough and hand tracking.

### Brain (Python 3.11 or 3.12)
```
cd brain
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .            # brain only, no robot
pip install -e .[reachy]    # add the Reachy Mini test body
```

Test with no robot:
```
python scripts\hello_body.py --body null
```
Test on the Reachy Mini simulator (start `reachy-mini-daemon --sim` in another terminal first):
```
python scripts\hello_body.py --body reachy
```

## References

**Reachy Mini (test body only)**
- SDK and docs: https://huggingface.co/docs/reachy_mini (Apache 2.0)
- Emotions library: https://huggingface.co/datasets/pollen-robotics/reachy-mini-emotions-library (Apache 2.0). Placeholder expressions only, convert into Heirloom clips
- Dances library: https://huggingface.co/datasets/pollen-robotics/reachy-mini-dances-library
- Conversation app, for its layered motion system (breathing, move queue, reactive wobble): https://github.com/pollen-robotics/reachy_mini_conversation_app (Apache 2.0)
- REST and WebSocket API: https://huggingface.co/docs/reachy_mini/main/API/rest-api

**Quest 3 and Unity**
- Passthrough Camera API: https://developers.meta.com/horizon/documentation/unity/unity-pca-documentation
- MR Utility Kit (desk detection), Interaction SDK (hand pose detection), Movement SDK (body tracking): part of Meta XR All-in-One
- NativeWebSocket: https://github.com/endel/NativeWebSocket
- URP Decal Projector for the fake projector (built into Unity)

**Brain**
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Vosk (small fixed phrase sets): https://alphacephei.com/vosk/
- openWakeWord: https://github.com/dscripka/openWakeWord

**Character and context**
- Disney Research BD-X droid paper, RSS 2024 (expressive robot motion)
- wire-pod, the fan revival of Anki Vector: https://github.com/kercre123/wire-pod

## Status
Fall quarter, weeks 6 to 10. No hardware.
