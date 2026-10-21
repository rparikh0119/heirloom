# Cartridge format (v1)

The cartridge holds everything Heirloom has learned. Move it and the wear moves with it (Rule 6). The body holds nothing.

Status: Oct 21. Replaces the long Oct 20 draft. Covers D37, D41, D43, D45, D46, D47.

## The plot test

Every kind of wear must answer yes to: **does it change what the next owner meets?**
- Yes: dials, patina, dialect
- Not wear: habits and regulars (belong to the current owner only, later), journal and voice memories (memory, its own plug-in, later)

## The core

```
cartridge/
  cartridge.json      version, droid id, list of layers
  layers/
    L1/               one folder per owner, oldest first
      dials.json      each wear plug-in owns one file
      patina.json
  history.json        handoffs, and every body it has run in
```

A layer in `cartridge.json`:
```json
{ "id": "L1", "label": "first home", "since": "2014-03-02", "until": null,
  "source": { "type": "simulated", "profile": "loud_family", "seed": 42 },
  "weight": "keep", "memories": "on_request" }
```

- `weight` (active, keep, blend, fade): how much this layer's wear counts. 1, 1, 0.5, then fading to 0.
- `memories` (open, on_request): whether its memories surface on their own. "Rest" = on_request (D45).
- `source`: lived or simulated, with profile and seed (D46).

The core only loads, saves, adds layers and logs history. It knows nothing about any specific kind of wear.

## The plug-in contract

Each kind of wear is one file in `brain/heirloom/wear/`:

| Job | What it does |
|---|---|
| `record(event)` | updates the active layer (e.g. patina counts a wave) |
| `blend(layers)` | combines all layers by weight into one effective value |
| `validate(data)` | checks its own file |
| `health()` | reports problems, like every module |

## Rules

1. Open files only (JSON, later JPEG and WAV). No robot-specific data.
2. Wear only lives here. Reactions, expressions and character.json never change from use.
3. Unknown files are kept untouched. Old and new brains can open each other's cartridges without losing anything.
4. A missing plug-in file means "nothing learned yet". Never an error.
5. Content (photos, voice) is only saved when asked (D43). Enforced by the memory plug-in when it exists.
6. `format_version` goes up when the core changes. Old versions stay readable.

## Plug-ins

**dials** (week 8). Drift per dial per layer. Blend = weighted sum, clamped to wear_limit 0.25 (D37, D41).

**patina** (week 8). Uses per expression. Wear `w = 1 - exp(-uses / 40)`. Worn = quicker, smoother, more confident.

**dialect** (if time). One chirp genome per meaning, pulled by warm responses (D48). First cut if behind (D47).

**memory** (week 9 or 10, preloaded photos). Journal, retired list (D45), requested flag (D43).

## Riya's calls

- [ ] Does wiping a layer also delete its memories?
- [ ] Is fade over about 8 weeks right?
- [ ] Who names a layer: the owner, or a date by default?
