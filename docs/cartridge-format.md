# Cartridge format (v1 design brief)

The cartridge is everything Heirloom has learned, in one folder the owner keeps. Later it's a USB drive in a cassette shell. Move the cartridge and you move the wear (Rule 6). The body holds nothing.

Status: draft for Riya's review, Oct 20. Replaces v0. Covers D37, D41, D43, D45, D46, D47.

---

## Rules the format must follow

1. **Open and readable.** Plain JSON, JPEG and WAV. Any computer can open it. No robot-specific data (one brain, any body).
2. **Wear only lives here.** Module files (reactions, expressions, character.json) never change from use. The cartridge stores *drift* on top of them.
3. **Layers, one per owner.** Oldest first. Nothing is erased unless the owner chooses (Rule 3).
4. **Rhythms by default (D43).** Every piece of content (photo, voice memory) carries `requested: true`. The loader refuses content without it.
5. **Retired means retired (D45).** Retired memories are listed by id and never surface again.
6. **Honest about simulation (D46).** Simulated layers say so, with the household profile and seed.
7. **Versioned.** `format_version` goes up when the format changes. Old versions must stay readable.

---

## Folder

```
cartridge/
  personality.json     who it is now: droid info + layers
  journal.json         photo and voice memory entries
  journal/             photos (JPEG), named by date and time
  recordings/          voice memories (WAV), only when asked (D33, D43)
  history.json         every handoff and every body it has been seated in
```

Personality and journal stay separate, so transfer can be tested with or without memories.

---

## personality.json

```json
{
  "format_version": 1,
  "droid": {
    "id": "hl-7f3a",
    "born": "2026-10-20",
    "awake_hours": 26280
  },
  "layers": [
    {
      "id": "L1",
      "owner": "first home",
      "since": "2014-03-02",
      "until": "2026-10-20",
      "source": { "type": "simulated", "profile": "loud_family", "seed": 42 },
      "weight": "keep",
      "memories": "on_request",
      "dials":   { "sass": -0.10, "boldness": 0.15, "energy": 0.05, "curiosity": 0.20, "warmth_speed": 0.10 },
      "patina":  { "wave": { "uses": 1840, "last_used": "2026-10-19" } },
      "dialect": { "hello": { "genome": { "pitch": 0.62, "speed": 0.55, "glide": 0.30, "notes": 3, "wobble": 0.12 }, "score": 0.8, "uses": 900 } },
      "habits":  { "check_in_hour": { "counts": [0, 0, 0, 0, 0, 0, 2, 9, 4] } },
      "regulars": [ { "id": "R1", "head_height_m": 1.62 } ]
    },
    {
      "id": "L2",
      "owner": "Riya",
      "since": "2026-10-20",
      "until": null,
      "source": { "type": "lived" },
      "weight": "active",
      "memories": "open",
      "dials": {}, "patina": {}, "dialect": {}, "habits": {}, "regulars": []
    }
  ]
}
```

**Fields**
- `owner` is a label the owner gives the layer ("Grandma's kitchen"), never an account (Rule 2).
- `dials` are drift from the base character, per layer.
- `patina` counts uses per expression. Wear `w = 1 - exp(-uses / 40)`.
- `dialect` is one chirp genome per meaning, pulled by warm responses (D48).
- `habits` are rhythms only: counts and timings, never what was said.
- `regulars` are people it knows in the household, by physical cues only (height now, voice and rhythm later). No names, no faces.

---

## Two controls per layer (proposed)

Rule 3 has three words (keep, rest, wipe) and the Wear System has four (keep, blend, fade, wiped). They mix two different questions. Splitting them is cleaner:

| Control | Values | Means |
|---|---|---|
| `weight` | active, keep, blend, fade | How much this layer's wear shapes behaviour |
| `memories` | open, on_request | Whether its photos and voices surface on their own |

- **Rest** = `memories: on_request`. The wear can still count, but the memories stay quiet (D45, scenario 1).
- **Wipe** = the layer is deleted from the file, and its journal entries with it. The handoff ritual is the only place this happens, and it asks first.

---

## Effective personality (how layers blend)

Weights: active 1.0, keep 1.0, blend 0.5, fade starts at 0.5 and shrinks to 0 over about 8 weeks.

- **Dials:** `drift = sum(weight x layer drift)`, then clamped to `wear_limit` (0.25, D37). This clamp is D41: praise can never push past it.
- **Patina:** effective uses = `sum(weight x uses)`, so a worn wave stays worn for the new owner.
- **Dialect:** genomes are averaged by `weight x uses`. The new owner hears the last family's voice at first (Wear System v0).
- **Habits and regulars:** only the active layer acts on them. Old regulars are remembered (shy recognition), not expected.

---

## journal.json

```json
{
  "format_version": 1,
  "entries": [
    { "id": "J0001", "kind": "photo", "file": "journal/2024-12-25_0912.jpg",
      "taken": "2024-12-25T09:12", "layer": "L1", "requested": true, "caption": null },
    { "id": "J0002", "kind": "voice", "file": "recordings/2025-03-14_1830.wav",
      "taken": "2025-03-14T18:30", "layer": "L1", "requested": true, "pairs_with": "J0001" }
  ],
  "retired": ["J0007"]
}
```

- `requested` must be true (D43). No content is saved without the owner asking.
- `retired` lists memories retired with "not now" during surfacing (D45). Retired items stay on the cartridge (nothing is erased without choice) but never surface again.
- This quarter the photos are preloaded (D47). Live capture waits for winter.

---

## history.json

```json
{
  "handoffs": [ { "from": "L1", "to": "L2", "date": "2026-10-20", "choices": { "L1": "keep" } } ],
  "seated_in": [ { "body": "unity:reachy_a", "from": "2026-10-20T22:00" } ]
}
```

- Every handoff is logged, with what the new owner chose for each layer.
- `seated_in` records every body it has run in. That's the week 9 transfer proof: one cartridge, two Reachys.

---

## Build plan (week 8)

1. `heirloom/cartridge/` module: load, save, validate (the rules above), blend to an effective personality. `health()` hook like every module.
2. Brain reads the effective personality at startup. Character dials add drift.
3. `tests/test_cartridge.py`: round trip, blend maths, wear_limit clamp, refuses unrequested content, retired items never surface.
4. Time-skip simulator writes Day 1, Year 1 and Year 12 cartridges per household profile (D46).

---

## Riya's calls

- [ ] Split each layer into `weight` + `memories` (above)? Or keep one status word?
- [ ] Does wiping a layer also delete its photos and voices? (proposed: yes, after the ritual shows them one last time)
- [ ] Is "fade over 8 weeks" right, or should fade be slower?
- [ ] Layer label: does the owner name it, or does it default to a date ("2014 to 2026")?
