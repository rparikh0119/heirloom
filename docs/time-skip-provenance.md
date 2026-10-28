# Time Skip · Where Every Number Comes From

*The rule: no number without a source. Updated Oct 22, 2026.*

The time skip (`brain/scripts/time_skip.py`) runs the real brain and the real wear code. Only the household is synthetic. Every number that describes people is declared in its household file as one of three kinds, and **the loader refuses any household with an undeclared number** (`tests/test_time_skip.py` checks this).

| Kind | Means | How it's used |
|---|---|---|
| **data** | Measured in a cited study, with the arithmetic shown | Used as is |
| **unknown** | No study gives it. Written as a range bounded by what is known | A single run uses the middle. A sweep runs the whole range |
| **scenario** | What the household *is* (the mix of moments) | A condition ("in a home where..."), never a claim about real homes |

Heirloom's own rules (which moments nudge which dial, how far, the cap) are **design**, not claims about people. They live in `brain/wear/dials.json` and `brain/heirloom/wear/dials.py`.

## The numbers

| Number | Kind | Source and derivation |
|---|---|---|
| Moments per day | unknown | Bentley et al. 2018, Table 6. Bounded by a cluster's sessions/day and commands/day: light 2.30 to 2.61, medium 2.36 to 5.55, super 5.93 to 30.44. A Heirloom moment is neither a speaker session nor a command, and a companion could fall outside this range. Which cluster a household uses is part of its scenario |
| Weekend multiplier | data | Bentley et al. 2018: weekend share of commands s (single-person homes 0.238, homes of 3+ 0.380, super users 0.30, light users 0.23). Per weekend day w = 5s / (2(1 − s)): 0.781, 1.532, 1.071, 0.747. Command share used as moment share |
| Novelty peak | unknown, 1.5 to 3.0 | The only measured magnitude: Cagiltay et al. 2022, weekly use fell about 2.2x from week 1 to week 4 (converting "once a week" = 1, "a few times" = 3, "daily" = 7). The conversion is an interpretation and the robot was a children's tutor, so the range stays wide |
| Novelty length | unknown, 14 to 28 days | Weiss et al. 2021 (Vector, drop after 2 weeks), Bajones et al. 2019 (3 weeks), Cagiltay et al. 2022 (still falling in week 4) |
| Long-term floor | unknown, 0.2 to 0.8 (enthusiast 0.5 to 1.0) | Zhao & McEwen 2025: Luka use "low but stable" by years 3 to 4. Family recall, no number. Enthusiast: Kertész & Turunen 2017, owners kept AIBOs for years, frequency not measured |
| Long-term decline start and end | unknown, day 270 to 450 / day 1,095 to 1,460 | Zhao & McEwen 2025: "sharp drop after the first year", "low and stable by years 3 to 4" (recall) |
| Shelved floor | data, 0 | Shen & Guan 2025: 0 of 47 homes used the robot past 6 months, and a robot on display counted as abandoned |
| Shelved decline | unknown, day 30 to 60 / day 60 to 90 | Shen & Guan 2025: 15 of 47 used it less after 1 to 2 months, 19 stopped after 2 to 3 months |
| Mix of moments | scenario | No study measures how often people wave at, praise or insult a companion robot. Replace with real proportions from the week 10 playtest |
| Routine (desk_student) | scenario | No study measures when people greet a desk robot. Replace with logged times from real use after week 10 |
| Taste (loud_family, desk_student, D107) | scenario | Which authored move the home warms to, how often it praises a move it likes or says no to one it doesn't, higher or lower chirps. No study measures how people react to a companion robot's choices. The reactions are extra events on top of the mix. Replace with logged reactions from the week 10 playtest |
| Keeper style (loud_family, desk_student, D107) | scenario | The habits wear's seven numbers for whoever handles it most, plus day-to-day spread. No study gives desk-gesture norms on Quest hand tracking (as far as we found). Replace with measured keepers after a hand-tracking check |

Not used: company claims such as bibo's 60+ interactions a day (active users only), Voicebot's 2.79 uses a day (self-reported).

## What can be claimed (30-run sweep across every unknown, Oct 22, family re-run Oct 27)

Oct 27: the loud family gained a taste (D107), so it now praises moves it likes and says no to others. Its row was re-swept: every claim still holds, family sass rose ~0.02 and family energy ~0.12 (the extra praise). Quiet solo re-swept unchanged.

Every claim below is conditional on the household scenarios and Heirloom's own rules. None is a claim about how real families behave. Each one held across the full range of every unknown.

| Claim | Evidence (lowest to highest across 30 runs) |
|---|---|
| Different homes wear the same droid into different characters | Year 12 sass: family 0.63 to 0.66, quiet solo 0.53 to 0.56, enthusiast 0.50. Energy: quiet solo 0.35 to 0.40, family 0.62 to 0.67. No overlap |
| Wear keeps changing after year 1 without racing to the cap | Family sass: year 1 0.55 to 0.59, year 12 0.63 to 0.66 |
| The dial changes alone are too small to see in a demo | Largest change: sulk 6.0 s → 6.9 s, notice distance 2.5 m → 2.9 m. Patina has to carry the fresh vs worn moment (D55) |
| A shelved droid freezes, with no trace of the absence | All dials stop moving after month 2. Rule 5 has no code yet |
| Curiosity only climbs | Year 12 curiosity 0.69 to 0.75 in every active home. Nothing lowers it until `glance_ignored` exists |

## How to check it yourself

```
cd E:\HEIRLOOM\brain
python tests\test_time_skip.py
python scripts\time_skip.py --sweep 30
```
