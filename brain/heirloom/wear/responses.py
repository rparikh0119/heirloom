"""Responses wear: the learner (learning loop v0, proposed D74, D75, D78, D81).

It learns which authored move lands, per situation. A situation (bucket) is what you did and the
time of day: "wave|morning". For each bucket it keeps a "worked X of Y times" tally per move, and
picks by Thompson sampling: it draws a guess from each tally and plays the best guess. Moves that
clearly don't land stop being tried. Moves it's unsure about still get tried now and then.
(Bucketed Beta-Bernoulli Thompson sampling, as in Song et al. HRI 2026. No full RL: Gordon 2016 and
Park 2019 didn't converge in 7 to 8 sessions.)

It only ever picks among the moves a reaction file lists ("motion" + "choices"). It never makes
a move up (D75). The reaction's chirp stays the same, so what it means stays readable.

    factory prior   the authored move starts at 2.5 of 3.5 (HEAD), every other choice at 1 of 2.5.
                    A fresh droid mostly does what it was designed to do, and tries something new
                    now and then
    fading          every time a bucket learns, its old evidence is multiplied by GAMMA, so no move
                    can run away with it and old habits can be unlearned (discounted TS)
    cap             no move holds more than CAP worth of evidence in one bucket (growth cap, D78)
    anytime         learned with no clock (a time skip household without a routine) goes in "wave|anytime"
                    and always counts, at every hour. Other hours' lessons for the same cue lean in (POOL)
    quiet mask      for QUIET_S after a cold reaction, only quiet moves are allowed (intrusion, D78)
    passed down     an old keeper's tallies count at INHERIT x their layer weight, at most
                    INHERIT_CAP per move: a lean the new keeper overrides in about 10 reactions (D81)

Page per layer (layers/L1/responses.json), evidence beyond the prior:
    {"schema": "heirloom.wear.responses/1",
     "buckets": {"wave|morning": {"happy": [5.2, 0.9], "hello": [1.0, 2.0]}}}     [worked, didn't]
"""
from __future__ import annotations

import random

from .base import Wear

SCHEMA = "heirloom.wear.responses/1"
HEAD = 1.5            # the authored move's head start (prior 1+HEAD worked, 1 didn't)
OTHER_PRIOR = (1.0, 1.5)
# Oct 27 sweep (15 fake owners each, learn_sim.py logic). Owners who only ever praise are the hard
# case, because silence is no reward and nothing ever counts against the default:
#   HEAD 3, others 1/2 (first try)   fresh says its designed hello 85%   praise-only owner gets the favourite 10%
#   HEAD 2, others 1/2               75%                                  40%
#   HEAD 1.5, others 1/1.5 (chosen)  65%                                  80%
# Owners who also say "no" reach 100% in all three. A design call: how often a fresh droid strays.
GAMMA = 0.98          # fading per lesson in a bucket. Half-life about 34 lessons (report: ln 0.5 / ln gamma)
CAP = 30.0            # most evidence one move can hold in one bucket
INHERIT = 0.3         # how much an old keeper's tallies count (times their layer weight)
INHERIT_CAP = 10.0    # at most this much inherited evidence per move
POOL = 0.3           # lessons for the same cue at other times of day count this much...
POOL_CAP = 10.0       # ...at most this much per move
QUIET_S = 120.0       # after a cold reaction, quiet moves only for this long
QUIET_MAX = 0.2       # "quiet" = intrusion at or under this
DRAWS = 400           # draws used to estimate each move's chance of being picked (for the log)

# How much each move intrudes on you (D78). Authored judgement, not learned.
INTRUSION = {"listen": 0.0, "sheepish": 0.2, "curious": 0.3, "hello": 0.4, "love": 0.5, "happy": 0.6,
             "stretch": 0.5, "yawn": 0.3, "offended": 0.8}


def time_of_day(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


class ResponsesWear(Wear):
    name = "responses"

    def __init__(self) -> None:
        self.brain = None

    def attach(self, cartridge, brain) -> None:
        super().attach(cartridge, brain)
        self.brain = brain

    # ---------- the learner ----------
    def tallies(self, bucket: str, arms: list[str], default: str) -> dict[str, dict]:
        """Per move: alpha/beta to sample from, plus own and inherited evidence (for explain).
        Evidence for one situation = its own bucket + what it learned with no clock ("wave|anytime") +
        a weaker lean (POOL) from the same cue at other times of day, at most POOL_CAP. So a lesson at
        10 am never hides twelve years of "they love the wiggle", and a new keeper's learning isn't
        split four ways by the clock."""
        active = self.cart.active.id
        weights = self.cart.weights(getattr(self.brain, "today", None))
        pages = {layer.id: self._page(layer.id) for layer in self.cart.layers}
        cue = bucket.split("|")[0]

        def evidence(page: dict, arm: str) -> tuple[float, float]:
            b = page["buckets"]
            s = f = 0.0
            for key in {bucket, f"{cue}|anytime"}:
                ev = b.get(key, {}).get(arm)
                if ev:
                    s, f = s + ev[0], f + ev[1]
            ps = pf = 0.0
            for key, arms_ in b.items():
                if key.split("|")[0] == cue and key not in (bucket, f"{cue}|anytime") and arm in arms_:
                    ps, pf = ps + POOL * arms_[arm][0], pf + POOL * arms_[arm][1]
            if ps + pf > POOL_CAP:
                ps, pf = ps * POOL_CAP / (ps + pf), pf * POOL_CAP / (ps + pf)
            return s + ps, f + pf

        out = {}
        for arm in arms:
            a0, b0 = (1.0 + HEAD, 1.0) if arm == default else OTHER_PRIOR
            own = evidence(pages[active], arm)
            inh_s = inh_f = 0.0
            inh_from = []
            for layer in self.cart.layers:
                if layer.id == active:
                    continue
                es, ef = evidence(pages[layer.id], arm)
                if es + ef > 0:
                    w = INHERIT * weights.get(layer.id, 0.0)
                    inh_s, inh_f = inh_s + w * es, inh_f + w * ef
                    inh_from.append(layer.id)
            total = inh_s + inh_f
            if total > INHERIT_CAP:
                inh_s, inh_f = inh_s * INHERIT_CAP / total, inh_f * INHERIT_CAP / total
            out[arm] = {"alpha": a0 + own[0] + inh_s, "beta": b0 + own[1] + inh_f,
                        "own": own, "inherited": (inh_s, inh_f), "from": inh_from}
        return out

    def propose(self, bucket: str, default: str, arms: list[str], masked: set[str], seed: str,
                estimate: bool = True) -> dict:
        """Pick a move. Returns chosen, probs (one per arm, masked = 0), explored, and the tallies."""
        allowed = [a for a in arms if a not in masked] or [default]
        tal = self.tallies(bucket, arms, default)
        rng = random.Random(seed)
        draw = {a: rng.betavariate(tal[a]["alpha"], tal[a]["beta"]) for a in allowed}
        chosen = max(allowed, key=lambda a: draw[a])
        est = random.Random(seed + ":probs")
        wins = {a: 0 for a in allowed}
        for _ in range(DRAWS if estimate else 0):          # the time skip skips the odds (no log, years of decisions)
            d = {a: est.betavariate(tal[a]["alpha"], tal[a]["beta"]) for a in allowed}
            wins[max(allowed, key=lambda a: d[a])] += 1
        mean = {a: tal[a]["alpha"] / (tal[a]["alpha"] + tal[a]["beta"]) for a in allowed}
        best = max(allowed, key=lambda a: mean[a])
        return {"chosen": chosen, "probs": [round(wins.get(a, 0) / DRAWS, 3) for a in arms] if estimate else [],
                "explored": chosen != best, "tallies": tal}

    def learn(self, bucket: str, arm: str, reward: int) -> None:
        """One lesson: it worked (1) or it didn't (0). Fades the bucket's older lessons first."""
        lid = self.cart.active.id
        page = self._page(lid)
        b = page["buckets"].setdefault(bucket, {})
        for ev in b.values():
            ev[0], ev[1] = ev[0] * GAMMA, ev[1] * GAMMA
        ev = b.setdefault(arm, [0.0, 0.0])
        ev[0 if reward else 1] += 1.0
        total = ev[0] + ev[1]
        if total > CAP:
            ev[0], ev[1] = ev[0] * CAP / total, ev[1] * CAP / total
        for a in b:
            b[a] = [round(b[a][0], 3), round(b[a][1], 3)]
        self.cart.write_page(lid, self.name, page)

    def explain(self, bucket: str, arm: str, default: str, arms: list[str]) -> str:
        """One plain line: "wave · morning → happy · worked 5 of 6 (2 from L1)"."""
        cue, tod = bucket.split("|")
        t = self.tallies(bucket, arms, default)[arm]
        s, f = t["own"]
        is_, if_ = t["inherited"]
        n, worked = s + f + is_ + if_, s + is_
        if n < 0.5:
            how = "designed default" if arm == default else "never tried here"
        else:
            how = f"worked {worked:.0f} of {n:.0f}"
            if is_ + if_ >= 0.5:
                how += f" ({is_ + if_:.0f} from {', '.join(t['from'])})"
        return f"{cue} · {tod} -> {arm} · {how}"

    # ---------- contract ----------
    def validate(self, data: dict, where: str) -> None:
        if not data:
            return
        if data.get("schema") != SCHEMA:
            raise ValueError(f"{where}: schema should be {SCHEMA!r}, found {data.get('schema')!r}")
        for bucket, arms in data.get("buckets", {}).items():
            if "|" not in bucket:
                raise ValueError(f"{where}: bucket {bucket!r} should look like \"wave|morning\"")
            for arm, ev in arms.items():
                if not (isinstance(ev, list) and len(ev) == 2 and all(isinstance(x, (int, float)) and x >= 0 for x in ev)):
                    raise ValueError(f"{where}: {bucket} {arm} should be [worked, didn't], two numbers 0 or more")

    def health(self) -> tuple[bool, str]:
        n = sum(len(self._page(l.id)["buckets"]) for l in self.cart.layers)
        return True, f"{n} situations learned"

    def _page(self, lid: str) -> dict:
        page = self.cart.read_page(lid, self.name)
        page.setdefault("schema", SCHEMA)
        page.setdefault("buckets", {})
        return page
