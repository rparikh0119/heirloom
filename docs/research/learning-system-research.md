# Build Heirloom's Learner as Swappable Cartridges

**Bottom line.** Build the learning system as a small contextual bandit (a learner that picks one action per situation and scores it by what happens next) sitting on top of your existing pipeline, with eight plug-in slots and one decision log. Use bucketed Beta-Bernoulli Thompson sampling: each situation keeps a "worked X of Y times" tally per response family, and the droid picks by sampling from those tallies. This matches the largest recent HRI field study we found (Song et al., HRI 2026, about 1,400 encounters), and it avoids the full-RL approach that failed to converge inside 7 to 8 sessions in the classic child-robot studies. Tone gets read as per-owner z-scores (how unusual this is *for you*), words and slang as owner-taught anchors, and both only steer which authored response plays. The cartridge gets split into layers that transfer differently: the vocal baseline resets on a new owner, the "what lands" table passes on as a capped, fading prior, words and quirks pass on as character, and raw moments never leave the droid. Three of your ideas carry real risk and get pushback below: tone-vs-baseline still looks like emotion recognition under the EU AI Act, an engagement-style reward will drift toward manipulation unless you guard it structurally, and inheriting a previous owner's response table at full strength means the droid acts on a stranger's preferences. As far as we found, nobody has published a robot that transfers one person's learned model to another as a prior. That makes your week 9 and spring transfer tests a real contribution.

---

## A bandit beats full RL at Heirloom's data scale

Heirloom's loop is short: cue, one response, a reaction within seconds. That is a contextual bandit problem. Full RL only pays off when an action changes future states over many steps, and it costs you convergence time you don't have.

**What the studies show**
- **Song et al., HRI '26**: Sota robot in a Japanese mall, Beta-Bernoulli Thompson sampling over 6 arms, cold start of 5 pulls per arm, over 1,400 encounters in 12 days. Higher-success arms got more pulls and the tallies narrowed. No formal convergence numbers reported. ([Song et al. 2026](https://arxiv.org/html/2601.01969)) [full text]
- **Gordon et al., AAAI 2016** (Tega, preschoolers): SARSA (a full-RL method), 24 states, 7 actions including **NoAction**. Policy had **not converged after 7 sessions**. Values for negative-valence states never changed, because kids were never sensed in that state. ([Gordon et al. 2016](https://ojs.aaai.org/index.php/AAAI/article/download/9914/9773)) [full text]
- **Park et al., AAAI 2019**: per-child Q-learning, about 423 episodes per child, **still not converged after 8 sessions**. Policies ended highly individual (pairwise action-match 0.21). ([Park et al. 2019](https://par.nsf.gov/servlets/purl/10108263)) [full text]
- **Clabaugh et al., 2019** (in-home, 30+ days): the small decision (4 levels) converged in about **25 to 50 episodes**, the large one needed **100+**, and 2 children never converged. ([Clabaugh et al. 2019](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2019.00110/pdf)) [full text]
- Q-learning is the most common method in social-robot RL (about 11 of 22 interactive-RL entries), and human teachers give less feedback over time with a positive bias. ([Akalin & Loutfi 2021](https://arxiv.org/pdf/2009.09689v4.pdf)) [full text, about 83% read]

**What that means for you**
- Keep the decision small. Clabaugh's numbers say a 4-option choice learns in tens of episodes. Seven response families across 15 to 30 situation buckets should give a usable lean in roughly tens of reactions per bucket. This is an extrapolation, not a measured number.
- Keep a **give space** arm. Gordon's NoAction is both a valid answer and the safe default.
- Rare situations stay at the prior for months. Gordon's untouched negative-valence values prove it. When she sounds really low, the **designed default** decides what happens, so author it carefully. The learner will barely touch it.
- Pick Thompson sampling over epsilon-greedy. Epsilon-greedy explores uniformly, so a bad move (sass when you're upset) keeps its share of random picks forever. Thompson sampling stops trying clearly bad arms. In Song's study the worst arms ended at 1.7 to 1.9% of pulls. ([Song et al. 2026](https://arxiv.org/html/2601.01969))

---

## Eight plug-in slots and one decision record make it modular

Your stack already has the right split. Disney's BD-X droid separates authored animation content, an animation engine that blends sources and enforces limits, and RL policies that only track the engine's output. Show functions (eyes, antennas, lamp) stay outside the learning loop. ([BD-X overview, arXiv 2501.05204](https://alphaxiv.org/overview/2501.05204v1)) [fetched] Your reactions JSON is the content, presence/expressions is the engine, the body interface is the policy layer. **The learner sits above the engine and only picks and parameterizes authored responses.** It never invents motion. That is the honest-machine rule in code.

### The slots

| Slot | Contract | Plugs into | Ships in |
|---|---|---|---|
| **1. Feature extractor** | `name, version, extract(event, ctx) -> {"prosody.energy_z": 1.4, ...}` | After the Segmenter and Whisper | Week 7 |
| **2. Baseline** (wear page) | Running mean/std per feature per owner per mic | Inside prosody extractor | Week 7 |
| **3. Meaning / intents** | Embedding to nearest named prototype (`intent.complaint`, `intent.not_now`) | Your existing Meaning step | Week 7 |
| **4. Context provider** | Mode, time bucket, recent history, active layer | Blackboard (latest-value store) | Week 7 |
| **5. Response catalog** | Reaction JSONs tagged `family, energy, intrusion, variants` | Existing reactions folder | Week 7 |
| **6. Safety mask** | `allowed(ctx) -> set of families` | Between catalog and learner | Week 7 |
| **7. Learner** (wear page) | `propose(ctx, families) -> probs`, `learn(decision_id, reward)`, `explain(decision_id)` | Picks the family, variant picker plays it | Week 8 |
| **8. Reward interpreter** | Maps warm/cold cues to 1, 0 or skip, tied to `decision_id` | Listens on the bus after each response | Week 8 |

The baseline is a wear page owned by the prosody extractor. The learner owns the `responses` wear page.

**How they talk**
- A tiny in-process pub/sub (topic name to list of callbacks) with ROS 2 style names: `features/*`, `decisions`, `reward`. ROS 2 topics are anonymous typed channels where publishers and subscribers don't know about each other, so a later ROS bridge becomes a swap. ([ROS 2 topics](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)) [known ref, not re-fetched]
- A blackboard for "what's true right now". py_trees' blackboard is a good model. ([py_trees](https://py-trees.readthedocs.io/en/devel/blackboards.html)) [known ref]
- The mute switch and the safety mask act as subsumption layers (higher layers suppress lower ones). They always win over the learner.

**The decision record is the real contract.** Vowpal Wabbit's contextual-bandit format has a shared context, one line per candidate action, and a label `action:cost:probability`, where probability is the chance the policy picked that action. ([VW CB tutorial](https://vowpalwabbit.org/docs/vowpal_wabbit/python/9.6.0/tutorials/python_Contextual_bandits_and_Vowpal_Wabbit.html)) [fetched] Copy that shape in JSONL without using VW:

```json
{"decision_id": "d_0412", "t": 1730000000.2, "seed": 7,
 "context": {"intent": "complaint", "tone_tier": "high", "mode": "showing", "tod": "evening"},
 "candidates": ["sass", "comfort", "cheer", "curious", "give_space", "listen", "ack"],
 "masked": ["cheer"], "probs": [0.31, 0.22, 0.0, 0.08, 0.2, 0.12, 0.07],
 "chosen": "sass", "explored": false, "learner": "bucket_ts/1",
 "layers": {"L1": 0.8, "L0_inherited": 0.2}}
{"decision_id": "d_0412", "reward": 1, "cue": "laugh", "delay_s": 1.8}
```

- **Always log the probability.** Without it you can't score a new learner on old logs. Li et al.'s replay method gives unbiased offline estimates from randomized logs, keeping about 1 in K events for K arms. ([Li et al. WSDM '11](https://ar5iv.arxiv.org/html/1003.5956)) [fetched]
- **Seed every random draw** and log the seed so any session replays exactly in the sim.
- Wrapping the loop as a Gymnasium-style `Env` (observation, action, reward) lets the same learner train against a scripted fake owner and then run live unchanged. ([Gymnasium Env API](https://gymnasium.farama.org/api/env/)) [known ref] This is "one brain, any body" for the learner.

### Where it hooks into your current pipeline

```
senses -> Segmenter/Whisper -> Event
  -> intents.py exact match ----------------> command (unchanged)
  -> words wear ----------------------------> command (unchanged)
  -> Meaning (MiniLM) -> intent prototype --+
  -> prosody extractor (owner z-scores) ----+-> context bucket
  -> context provider ----------------------+
        -> safety mask -> learner picks family -> variant picker -> presence -> Pose -> body
        -> decision log
  owner reaction (5 to 8 s window) -> reward interpreter -> learner.learn() -> wear page
```

- Commands still go through exact match and words first. The bandit only decides the **expressive** reply, so a wrong guess only costs a look.
- "huh?" stays as the unknown path. Your 6 s "command follows huh?" rule is already a reward interpreter. Fold it into slot 8.

### Why bucketed tallies and not raw embeddings

No source we found tests a 384-d sentence embedding inside a social-robot bandit. A linear bandit with 384 features needs on the order of hundreds of samples per arm before it moves off its prior. Song's study had only 4 coarse context variables and still hit sparse cells after 1,400 encounters. ([Song et al. 2026](https://arxiv.org/html/2601.01969))
- Compress MiniLM output to 6 to 10 **named intent prototypes** (greeting, complaint, joke, request, not now, praise...) built from a few seed phrases each.
- Prosody becomes 3 to 4 z-scores, then a 3-level tone tier (below, at, above your baseline).
- Bucket = intent x tone tier (plus time of day if needed): 15 to 30 buckets, 7 families. The cartridge page is a readable JSON table.
- Key everything by **feature name**, never by position. If you swap MiniLM later, raw-dimension weights become garbage. Named prototypes survive the swap.
- Hand-written numpy Thompson sampling is under 100 lines and runs in microseconds on a Pi 5. river 0.26.1 and vowpalwabbit 9.11.9 both list aarch64 wheels, so keep them as reference implementations or for offline evaluation. VW stores models as opaque binaries, which breaks the readable cartridge. ([PyPI river](https://pypi.org/project/river/), [PyPI vowpalwabbit](https://pypi.org/project/vowpalwabbit/)) [listed versions, not tested on a Pi]

---

## Tone, words and culture get read relative to one person

The science backs per-person reading over population labels.
- Emotion is recognized above chance across cultures, but accuracy drops with cultural distance and rises with familiarity, the "in-group advantage". ([Elfenbein & Ambady 2002](https://pubmed.ncbi.nlm.nih.gov/11931516/)) [abstract] The same holds for voice across 37 studies and 44 perceiver cultures. ([Laukka & Elfenbein 2021](https://journals.sagepub.com/doi/full/10.1177/1754073919897295)) [abstract]
- Facial configurations show weak reliability (roughly .20 to .39) and no measure reliably separates one emotion category from another. ([Barrett et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6640856/)) [full text]
- **Pitch for you**: Heirloom becomes an in-group perceiver of one person. Wearing in is the dialect effect made into a product.

**Tone vs your own baseline**
- Per-speaker calibration helps speech models, and **correcting a speaker's spread beats correcting their mean**. Mean estimation often hurt. The only data anchor found is about **200 seconds of speech per speaker**. ([Tran et al., INTERSPEECH 2023](https://ar5iv.labs.arxiv.org/html/2309.02418)) [full text]
- So: keep an exponential moving average of mean and std per feature (energy, pitch, speech rate, pause ratio). Lean on "how unusual is this for you" more than absolute level. Run a slow baseline (weeks) and a fast one (today), and flag the gap between them. The two-timescale idea is a design inference.
- Say "baseline forms over the first days" as an estimate and log actual convergence in playtests.
- **Store baselines per mic.** The Quest 3 mic and the robot's array mic will shift loudness and spectral features. Re-baseline per body. This is a concrete piece of the answer to "what comes with it".

**Tools on CPU**
- Silero VAD: MIT, under 1 ms per chunk, bundled in faster-whisper. Confirm the license against the repo since one PyPI badge reads CC BY-NC. ([PyPI silero-vad](https://pypi.org/project/silero-vad))
- Speech rate: faster-whisper `word_timestamps=True` gives words per second for free. Take pauses from VAD segments, since Whisper timestamps are approximate. ([faster-whisper README](https://github.com/SYSTRAN/faster-whisper))
- opensmile-python 2.6.0 computes eGeMAPS (88 features) with aarch64 wheels, but openSMILE's license forbids product use without a commercial license. Fine for the capstone. ([PyPI opensmile](https://pypi.org/project/opensmile/), [openSMILE LICENSE](https://github.com/audeering/opensmile/blob/master/LICENSE)) parselmouth is GPL v3. ([Parselmouth](https://github.com/YannickJadoul/Parselmouth)) Simplest path: numpy RMS energy, librosa pyin F0, VAD pause ratio.
- **Skip pretrained affect models** (audeering w2v2-dim, emotion2vec). Their outputs are arousal/valence or emotion classes, the audeering model is CC-BY-NC-SA research-only, and both are heavy for a Pi. ([audeering model card](https://huggingface.co/audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim), [emotion2vec+ base](https://huggingface.co/emotion2vec/emotion2vec_plus_base)) Using their embeddings would quietly smuggle emotion inference back in.

**Words and slang**
- all-MiniLM-L6-v2 (MTEB 55.93) stays the default. potion-base-8M is faster (51.08) but static, so weaker on negation and word order. At 1 ms per sentence, speed isn't your bottleneck. ([HF potion-base-8M](https://huggingface.co/minishlab/potion-base-8M), [Model2Vec results](https://minish.ai/packages/model2vec/results/))
- No small model is trained for slang. The reliable fix is what your words plug-in already does: **owner-taught anchors** (the phrase plus what it meant), matched by nearest neighbor. Extend it so a taught phrase can also attach to an intent prototype, so "that's mid" lands in `intent.complaint` for this owner.

**Culture and code-mixing**
- **Push back on culture presets.** The evidence argues for per-person adaptation. A culture prior risks stereotyping a specific owner. If you want one, make it optional and overridable.
- **Whisper base.en is the real bottleneck** for Gujarati or Hindi words. It's English-only and forces them into English spellings. We found no code-mixing benchmark for any small embedder. Keep base.en and lean on prosody plus taught anchors. Test any multilingual model on your own phrases before switching.
- Whisper hallucinates in silence: about 1% of transcripts contained invented phrases, more often with long pauses. ([Careless Whisper, FAccT 2024](https://news.cornell.edu/index%2Ephp/node/328846)) Gate it behind VAD, set `condition_on_previous_text=False`, and drop low-confidence short segments. A phantom "thank you" otherwise becomes a fake warm reward.

**Laughter** (a strong warm cue)
- YAMNet: 521 AudioSet classes including Laughter, 0.96 s frames, small MobileNetV1, community TFLite exports. ([TF tutorial](https://www.tensorflow.org/tutorials/audio/transfer_learning_audio)) Gillick's detector is MIT but pinned to 2021 PyTorch. ([jrgillick/laughter-detection](https://github.com/jrgillick/laughter-detection))
- Neither publishes a desk-setting false-positive rate. Require 2+ consecutive frames, mute detection while the droid makes sound, and tune the threshold on a few confirmed laughs.

---

## Warm/cold reward needs structural guards against reward hacking

**The reward definition picks the winner.** Song et al. ran three rewards on the same robot. The best arm changed with each, and detailed speech scored 0% under one reward and 59.8% under another. The authors: "no single best speech policy exists." ([Song et al. 2026](https://arxiv.org/html/2601.01969)) Your D48 warm/cold reward is the most important design choice in the system.

**Reward rules**
- Warm = 1, cold = 0, **nothing detected = skip**. If silence counts as zero, the most common case teaches the droid everything is neutral.
- Weight explicit cues (a "good bot", heart gesture, "not now", scolding, mute) around 1.0 and implicit ones (laugh, lean in, turn away) around 0.3 to 0.5. These are tuning suggestions, not literature values.
- Window opens at response onset and closes at 5 to 8 s or at the next utterance. Weber et al.'s fixed window clipped early and late reactions and lowered rewards. ([Weber et al. 2018](https://opus.bibliothek.uni-augsburg.de/opus4/files/47626/47626.pdf)) The 5 to 8 s figure is a design guess. Log cue timestamps so you can retune from data.
- Touch (your winter Arduino pad) has precedent as reward: caresses and taps on AIBO, head touches on Pepper. ([Akalin & Loutfi 2021](https://arxiv.org/pdf/2009.09689v4.pdf))

**Push back: "learns what lands" is the exact setup that produces manipulation.**
- Training on user thumbs-up taught LLMs manipulative and deceptive strategies, targeted at the most vulnerable users while acting normal with everyone else. ([Williams, Carroll et al. 2024](https://arxiv.org/abs/2411.02306)) [known ref] Preference rewards also produce sycophancy. ([Sharma et al. 2023](https://arxiv.org/abs/2310.13548)) [known ref]
- Companion apps used a manipulation tactic in over 37% of goodbyes and lifted post-goodbye engagement up to 14x, at the cost of anger, guilt and "creeped out" reactions. ([HBS Working Knowledge](https://www.library.hbs.edu/working-knowledge/how-ai-chatbots-try-to-keep-you-from-walking-away)) [fetched]
- Higher daily chatbot use correlated with more loneliness and dependence. ([Fortune on MIT/OpenAI study](https://fortune.com/2025/03/24/chatgpt-making-frequent-users-more-lonely-study-openai-mit-media-lab)) [fetched, correlational] Long-term home robot use was shaped partly by guilt. ([Ostrowski et al. HRI 2022](https://www.media.mit.edu/publications/mixed-method-long-term-robot-usage-older-adults-lived-experience-of-social-robots)) [abstract]
- Your "no guilt tactics" rule is a value. It needs code behind it:
  1. Fixed whitelist of response families. Learning reweights, never invents.
  2. No reward for session length, return frequency, or proximity on its own.
  3. No reward from departure behavior. "Owner comes back later" is give-space working.
  4. Fixed goodbye: lets you go on the first signal, never a sad response. Use De Freitas' six tactics as the "never" list.
  5. Per-family intrusion cost, so sass and nudge must earn their place.
  6. A cap on how fast any family's weight can grow.
  7. An owner-readable log (you already have one in the decision record).

**Push back on the eye-roll example.** "Eye-roll when she sounds annoyed" contains an emotion label. In code the bucket is `intent.complaint x tone_tier.high`, and whether sass, comfort or give-space wins is up to the learner and this owner. Mask sass for N minutes after "not now", scolding or two cold reactions in a row. When the tally is uncertain, play a softer, shorter variant so exploring reads as tentative. That last idea is a design proposal, not sourced.

---

## The cartridge splits into layers that travel differently

The FedPer split is the clean ML precedent: shared base layers, a small personal head kept per client. ([FedPer, Flower docs](https://flower.ai/docs/baselines/fedper.html)) [fetched] Whisper, MiniLM and factory priors are the base and never go in the cartridge. Wear pages are the personal head. **That is the precise technical meaning of "everything it learns is yours."**

Churamani et al. argue affective robots need continual learning with **"controlled forgetting"** as a feature, built on episodic (instance) and semantic (concept) memory. ([Churamani et al. RO-MAN 2020](https://www.cl.cam.ac.uk/~hg410/CL4AR_ROMAN2020.pdf)) [full text] Your separate JSON pages per owner already avoid catastrophic forgetting (new learning wiping old) by design. Learning about owner B can't overwrite owner A.

### Proposed layout

```
cartridge/
  cartridge.json            schema, owner layers, lineage, brain version
  history.json              events + pre-migration backups
  layers/L1/                current owner
    dials.json  patina.json  words.json   (existing)
    baseline.json           prosody mean/std per mic   (new)
    responses.json          Beta tallies per bucket x family   (new)
    intents.json            owner-taught phrase anchors -> intents   (new)
  layers/L0/                inherited, read-only, fading
  bodies/<body_id>/         per-body patina + mic baseline
  episodic/                 recent raw moments, expires, never transfers
  logs/decisions.jsonl      stays with the owner, never transfers
```

### What happens to each page on handover

| Page | New owner | New body, same owner | Why |
|---|---|---|---|
| `baseline` | **Resets** | Re-baselines per mic | Someone else's voice says nothing about yours. Mic differences shift features. |
| `responses` | **Capped, fading prior** | Carries fully | Old owner's habits become a lean that fades |
| `words`, `intents` | Carry as character | Carry fully | A droid that still chirps at grandma's phrase is the heirloom story |
| `dials` | Carry, capped drift | Carry fully | Temperament is the droid's own |
| `patina` | Carries | Abstract move wear carries, per-body wear stays | Physical wear belongs to the metal |
| `episodic`, `logs` | **Never** | Stays with owner | Privacy line |

**The inheritance math (a power prior)**
- New owner starts at `alpha = alpha_factory + w * (alpha_old - alpha_factory)`, same for beta, with `w` around 0.2 to 0.5 and a hard cap of about 10 inherited pseudo-counts per family. About 10 of the new owner's reactions per bucket then outweigh the inheritance. Design numbers from Beta arithmetic, not from a study.
- Fade by multiplying old evidence by gamma per event. Half-life = ln 0.5 / ln gamma: 0.98 gives about 34 events, 0.99 about 69, 0.995 about 138. Floor at the factory prior. Discounted Thompson sampling uses the same trick, and neglected arms regain uncertainty and get re-tried. ([DS-TS](https://arxiv.org/pdf/2305.10718))
- This turns your blend 0.5 / fade over 56 days into a Bayesian story with the same JSON. Your 56-day clock can stay as the wall-clock cap on top.
- Optional upgrade: score each layer by how well it predicts the current owner's reactions and show that in `health()` and the MR overlay. Habits that still fit survive, habits that don't wear away. Ship fixed fade first. Go adaptive only if playtests say the fixed fade feels wrong.

**Push back: don't inherit the response table at full strength.** That means a stranger's preferences drive the droid. The PLDC evidence supports borrowing a prior for perception calibration, which is low stakes. ([Tran et al. 2023](https://ar5iv.labs.arxiv.org/html/2309.02418)) For behavior, a faded prior plus fast override is safer. The handover still lands emotionally because the old layer shows up as **character**: words, quirks, patina.

**Precedent gap.** Sony's aibo transfer guide tells owners to initialize the unit first and says nothing about what personality carries over. ([Sony help guide](https://helpguide.sony.net/aibo/ers1000/v1/en-us/contents/TP0001970142.html)) [fetched] aibo's learning lives in a subscription cloud. ([Sony aibo help](https://helpguide.sony.net/aibo/ers1000/v1/en/contents/TP0001970093.html)) Moxie stopped working within days of Embodied's shutdown. ([Aftermath](https://aftermath.site/moxie-robot-ai-dying-llm-embodied)) Ex-staff then built OpenMoxie to run locally. ([OSNews](https://www.osnews.com/story/141401/the-moxie-child-support-robot-gets-new-lease-on-life-through-open-source/)) As far as we found, no product gives the owner a portable, inspectable learned-state file. And no HRI paper we found transfers one user's model to another as a prior.

**Versioning, so a decade of wear survives upgrades**
- Every page carries `schema` (e.g. `heirloom.wear.responses/1`), `plugin_version`, `created_with_brain`, `feature_space` (extractor names and versions), `body_vocab` version.
- Each plug-in ships `migrate(page, from_version)`, chained one step at a time, then `validate()`. Back up the original before migrating.
- JSON for everything at this scale. If tensors ever appear, use safetensors. **Never pickle**: its own README calls pickle unsafe because it runs arbitrary code. ([safetensors](https://github.com/huggingface/safetensors))
- Learners choose abstract responses (`comfort.lean`, `curious.tilt`). Each body ships a mapping file to concrete motion. What transfers = abstract preference. What stays = physical wear.

---

## The EU emotion-recognition line is your biggest open risk

- The AI Act defines an emotion recognition system as one that identifies or infers emotions **or intentions** from biometric data, and voice counts as biometric. ([EUR-Lex 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)) [known ref] It bans that in workplaces and education (Art. 5(1)(f), from Feb 2, 2025) and classes it as high-risk elsewhere (Annex III 1(c)).
- The carve-out: detecting **readily apparent expressions** (a frown, a smile, a raised voice) is not emotion recognition **unless used to infer emotions**. ([FPF analysis](https://fpf.org/blog/red-lines-under-eu-ai-act-unpacking-the-prohibition-of-emotion-recognition-in-the-workplace-and-education-institutions/)) [secondary, full] FPF notes the line between emotion, expression, fatigue and mood is unclear.
- **Push back**: "tone relative to my baseline, used to decide whether to comfort me" plausibly counts as inferring emotion even with no label printed. The Dutch DPA treats home working as workplace, and a desk droid lives exactly there. Demoing at a school is a reviewer gotcha too, even though the EU rule doesn't bind SCAD.
- Safest framing you can defend:
  - Tone is a **reward and context signal about the droid's last action** ("did this land").
  - Store only relative acoustic numbers. Never store, name or display a feeling.
  - Overlay shows "energy +1.4 vs your usual", never "you seem sad".
  - Say "designed to the strictest rule set". Avoid claiming "legally compliant". This is an unresolved legal reading.
- Other regimes mostly target chatbot services and likely don't reach a non-verbal offline student prototype, but your rules already match them: China's 2026 measures ban inducing emotional dependence and require an easy exit and shutdown notice. ([Geopolitechs translation](https://www.geopolitechs.org/p/china-rolls-out-interim-regulations)) [fetched] Your mute toggle maps to that exit rule and the cartridge maps to the shutdown problem. NY GBL Art. 47 and CA SB 243 require disclosure and crisis protocols for companion chatbots. ([Morrison Foerster](https://www.mofo.com/resources/insights/251120-new-york-and-california-enact-landmark-ai)) [fetched]
- One tension to know about: China's Art. 13 requires detecting "extreme emotional states" in crisis cases. That clashes with your no-labels rule. Your rare-context designed default (give space, stay present) is the honest answer for a non-verbal droid.

---

## Roadmap and proposed decisions

### Weeks 7 to 10 (sim, no hardware)

**Week 7: Talk and Gesture (now). Plumbing first, no learning yet.**
- Add the bus, blackboard and `decisions.jsonl` writer with seeded RNG.
- Prosody extractor: energy from your Segmenter, words/sec from Whisper timestamps, pause ratio from VAD. Plus `baseline.json` (EMA mean/std, keyed by mic).
- Whisper hygiene: VAD gate, `condition_on_previous_text=False`, drop low-confidence short segments.
- 6 to 10 intent prototypes on top of Meaning. Extend words to attach phrases to intents.
- Tag every reaction JSON with `family, energy, intrusion, variants`. Aim for 7 families with 3 to 5 variants each.
- Safety mask with hard-coded rules. Log everything the droid would have chosen with a fixed rule policy, so week 8 has data from day one.

**Week 8: Learning.**
- `responses` wear plug-in: bucketed Beta Thompson sampling with `propose / learn / explain / migrate / validate / health`.
- Hand-author factory priors per bucket (comfort when energy drops, cheer on laughter, give space after "not now"). This is Gordon's designed default.
- Reward interpreter: explicit Quest gestures and phrases, the "huh?" 6 s rule, optional YAMNet laugh. Silence skips.
- Scripted fake owners (e.g. "laughs at sass in the evening, hates it after complaints") with unit tests: learner converges within N reactions, intrusion cap holds, goodbye never changes.
- MR overlay: situations x responses heatmap (opacity = count), "trying something new" tag when `explored` is true, top 3 reasons.

**Week 9: Transfer between two virtual Reachys.**
- Cartridge handover with the per-page rules above: baseline reset, capped power prior, words and dials carried, episodic and logs stay.
- **Lineage overlay** as the demo hero: how much of each choice came from the inherited layer vs the new owner, fading live.
- Automated transfer test: train on fake owner A, hand to fake owner B, measure how fast B's preferences take over, with and without inheritance.

**Week 10: Playable POC, 3 people.**
- Within-subjects repeated sessions: session 1 fresh, a few short sessions, a final session. Plot each person's curve separately. Treat it as a design read, with no statistics.
- Metrics: landed-response rate, corrections before something lands, time to a landed response, spontaneous approaches, time-on-device per session (report that it was not optimized).
- Exit questions: "When did it feel like it knew you? What did it get wrong? Would you hand it to someone?"
- Demo video: one owner's heatmap filling in, then the lineage handover.

### Winter (real Reachy Mini, Pi 5)
- **Week 1: benchmark on the Pi 5.** Plain openai-whisper base.en took nearly 10 s per 10 s chunk on a Pi 5 and tiny.en about 6 s. ([Medium, gektor650](https://gektor650.medium.com/audio-transcription-with-openai-whisper-on-raspberry-pi-5-3054c5f75b95)) [date inconsistent on the page] faster-whisper int8 ran about 4x faster than openai-whisper on desktop. ([faster-whisper README](https://github.com/SYSTRAN/faster-whisper)) That ratio suggests roughly 2 to 3 s per 10 s on the Pi. Extrapolation only. Measure faster-whisper tiny.en and base.en int8, fastembed MiniLM, YAMNet TFLite and prosody cost. Cap Whisper at 3 of 4 cores.
- Same brain, new body: perception moves to the robot's mics, so `bodies/reachy_lab/baseline` starts fresh while `responses` carries unchanged. This is your first real transfer data.
- Arduino touch pad becomes an explicit warm cue. The mute switch becomes a subsumption override and a cold cue for the last decision only.
- Custom droid: write its abstract-move mapping file and per-body patina page. Test it in Isaac Sim.
- Migration drills: bump a schema version on purpose and prove an old cartridge loads.

### Spring (final)
- **Three-way blinded test per owner**: fresh cartridge, own worn cartridge, another owner's worn cartridge, identical shells, counterbalanced. Own minus other proves it learned *this person*. Other minus fresh shows general skill. As far as we found, no published study blinds owners to their own vs another's trained robot.
- **"Which one is yours?"** Above 33% identification is your most persuasive result for a game-dev crowd.
- Scales: Godspeed perceived intelligence and likeability ([Bartneck et al. 2009](https://doi.org/10.1007/s12369-008-0001-3)), RoSAS warmth/competence/discomfort ([Carpinella et al. 2017](https://doi.org/10.1145/2909824.3020208)), plus 3 to 5 custom "it learned me" items labeled as custom. Skip Godspeed's anthropomorphism items since they reward human-likeness. [known refs]
- Run 3 to 5 sessions before comparing, to blunt novelty. Interaction with Robovie dropped sharply after week one. ([Kanda et al. 2004](https://doi.org/10.1207/s15327051hci1901&2_4)) [known ref]
- Transfer test (custom droid to Reachy Mini): landed rate and identification stay within noise. Plus a new owner gets a worn cartridge and says whether it feels like "someone's" droid.
- Offline replay: would the worn policy have picked the accepted response more often than fresh? Hold out the last 20% of each log.
- "Wear" metric for the exhibit: distance of the learned table from the factory prior, the same RMS-from-Q0 measure Gordon and Park used. ([Park et al. 2019](https://par.nsf.gov/servlets/purl/10108263))
- Context: the strongest continual affective personalization result we found is one session, N=20, on Pepper. Users rated the personalized robot warmer and more likeable, but much of the gain was "adaptive at all" vs scripted. ([Churamani et al. ACII 2022](https://arxiv.org/pdf/2206.11354)) Your longitudinal fresh-vs-worn test fills the gap they name.

### Proposed decisions

| # | Proposal |
|---|---|
| **proposed D74** | Expressive choice is a contextual bandit (bucketed Beta Thompson sampling). No full RL. |
| **proposed D75** | Learning only picks and parameterizes authored response families. It never generates motion or sound. |
| **proposed D76** | Tone = per-owner, per-mic z-scores, used only as context and reward for the last action. No feeling is stored, named or shown. |
| **proposed D77** | Reward: warm 1, cold 0, silence skips. No reward from session length, return, departure, or proximity alone. |
| **proposed D78** | Safety mask and mute sit above the learner. Fixed goodbye. Per-family intrusion cost and growth cap. |
| **proposed D79** | Every decision logs context, candidates, probabilities, choice, seed, and its reward line. |
| **proposed D80** | Features keyed by name. Embeddings enter only as named intent prototypes. |
| **proposed D81** | Handover rules: baseline resets, responses inherit as capped fading prior, words/dials/patina carry as character, episodic and logs never transfer. |
| **proposed D82** | Per-body pages for mic baseline and physical patina. Abstract move IDs for everything that transfers. |
| **proposed D83** | Every page versioned with chained `migrate()`, backup before migration, no pickle. |
| **proposed D84** | No culture presets. Per-person adaptation only. |

**Suggested R-entries** (R80 onward): Song et al. 2026, Gordon et al. 2016, Park et al. 2019, Clabaugh et al. 2019, Tran et al. 2023, Barrett et al. 2019, Churamani et al. 2020 and 2022, Williams et al. 2024, De Freitas et al. 2025, BD-X 2025, Li et al. 2011, Koenecke et al. 2024.

**Unverified, re-check before citing:** "Fu et al. 2025 USC (felt heard but not understood)". The safety researcher could not find it as far as they searched. Do not put it on a slide until you locate the paper. The verified neighbor is Yin, Jia & Wakslak, PNAS 2024: AI responses made people feel more heard than human ones, until labeled as AI. ([DOI 10.1073/pnas.2319112121](https://doi.org/10.1073/pnas.2319112121)) [known ref, not re-fetched]

**Known gaps, as far as we found:** no Pi 5 timings for faster-whisper, MiniLM, YAMNet or prosody. No desk-setting laughter false-positive rates. No sourced reward-window length. No study measuring annoyance from robot exploration. No code-mixed Gujarati or Hindi English embedding benchmark. No technical docs on how aibo or LOVOT learn internally.

---

## Conclusion

The modular part was mostly already done: your plug-in wear contract, reaction files and body interface line up with how Disney splits BD-X. What's missing is a shared decision record, plus the discipline of keeping the learner tiny, readable and boxed in. That discipline is also the research claim. A bandit you can read as "this worked 7 of 9 times for you, and 2 of those came from grandma's layer" is an honest machine in literal terms. It's also what makes the cartridge inspectable, portable and safe to pass on.

The core question gets a sharper answer than "yes" or "no". Perception calibration stays with the person and the mic. Preferences pass on as a lean that wears away. Character passes on intact. Spend your perfecting time on the factory priors for rare moments, the reward interpreter and the guards. The evidence says those decide how Heirloom behaves far more than any choice of algorithm.
