# Prep for Oct 22: NOT APPLIED YET

These files are ready-to-apply versions of tomorrow's two laptop changes. Nothing in the running brain uses them until they're copied into place. All tests pass with them (cartridge 13/13, dials 14/14, reactions scenario passes).

| File here | Goes to | What changes |
|---|---|---|
| `dials.py` | `brain/heirloom/wear/dials.py` | Settling learning (D50, proposed). Each nudge moves a dial a fraction of the way toward the limit, so it changes fast at first, then slows, and lands at the balance of how it's treated |
| `test_wear_dials.py` | `brain/tests/test_wear_dials.py` | Tests updated for settling, plus a new balance test |
| `sim.py` | `brain/heirloom/sim.py` | Households v2: totals from Bentley 2018, novelty curve over 3 weeks, quieter after year 1, weekend bump. New `month1` snapshot |
| `quiet_solo.json`, `loud_family.json`, `enthusiast.json`, `shelved.json` | `brain/sim/households/` | Four households with a `sources` list each. The mix of moments is labelled as a design assumption |

## Time skip results with both changes (seed 42)

| Household | Month 1 | Year 1 | Year 12 | Year 12 sulk / notice |
|---|---|---|---|---|
| Quiet solo | barely changed | calmer (energy 0.39), curious 0.59 | energy 0.38, curious 0.74 | 6.3 s / 2.63 m |
| Loud family | bolder (0.54) | bold 0.68, sass 0.55 | bold 0.71, sass 0.63 | 6.8 s / 2.92 m |
| Enthusiast | bolder, bouncier | bold 0.70, curious 0.72 | curious capped 0.75 | 6.0 s / 2.89 m |
| Shelved | like quiet solo | almost frozen after month 2 | 548 moments in 12 years | 6.0 s / 2.56 m |

Out of the box: every dial 0.50, sulk 6.0 s, notices you at 2.50 m.

## What this shows (read before tomorrow)

1. **Homes now end up different, and Year 1 differs from Year 12.** The settling fix works.
2. **The dials are a weak demo signal.** A 6.0 s vs 6.8 s sulk is hard to see. That's by design (Rule 4: the core barely changes), so **patina has to carry the fresh vs worn moment**. This makes patina the most important build of week 7 to 8.
3. **Curiosity still climbs in every home** because nothing lowers it. That needs the `glance_ignored` presence event.
4. **Rule 5 (absence leaves a trace) has no code yet.** The shelved droid just freezes, with no shyness.
