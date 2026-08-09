# Experimental design

The question:

> **Does the scaffolding around a model matter more than the model — measured on
> hardware and APIs people can actually afford?**

This document fixes the design that answers it. Everything here is decided
**before** any data exists, because most of these choices constrain what the data
can mean. The formal commitments are in [PREREGISTRATION.md](PREREGISTRATION.md).

---

## 1. Why an ablation and not a leaderboard

HAL and AstaBench already publish accuracy-versus-cost leaderboards for agents.
Another leaderboard would be a product, not a finding.

What nobody has cleanly measured is the **two-dimensional grid**: hold the model
fixed and vary the scaffold, then hold the scaffold fixed and vary the model. The
popular claim that "the harness matters as much as the weights" asserts a
comparison between those two effects without ever measuring it. That comparison
is the contribution. The leaderboard is how it is presented.

---

## 2. Two lanes

"Affordable compute" has two distinct populations, and each gets a lane. Neither
is a compromise for the other.

| | **Lane A — consumer hardware** | **Lane B — free-tier APIs** |
|---|---|---|
| Question | *What works on a GPU a student owns?* | *What works on a free API key?* |
| Runtime | Ollama on an RTX 4060, 8 GB | Groq · Gemini · Cerebras · OpenRouter |
| Constraint | GPU throughput | Daily token and request quota |
| Carries | The headline ablation, the full 5-harness axis, the compaction ablation | The cost/Pareto claim across a diverse hosted model set |
| Seeds | 5 | 2 |

**The lanes contend for nothing.** One is GPU-bound, the other is API-quota-bound
and runs in CI. They run concurrently, which is what puts the headline finding on
Day 32 rather than the last day.

Every published claim is attributed to the lane that supports it.

---

## 3. The grid

Both lanes share a **20-task core suite** and a **3-harness common subset**
(`single_shot`, `react`, `react_retry`).

### Blocks

| Block | Grid | Context policy | Trajectories | GPU-h |
|---|---|---|---|---|
| **A1** — pooled-grid contribution | 3 models × 3 common harnesses × 20 tasks × 5 seeds | capped 8K | 900 | ~17.5 |
| **A2** — extended harness axis | 3 models × 2 extra harnesses × 20 tasks × 5 seeds | capped 8K | 600 | ~11.7 |
| **A3** — compaction ablation | 2 models × **all 5 harnesses** × 20 tasks × 3 seeds | **`none`** | 600 | ~22.5 |
| **Lane B** | 5 models × 3 harnesses × 20 tasks × 2 seeds | capped 8K | 600 | — |
| | | | **2,700** | **~51.7** |

### The pooled primary grid

**A1 + Lane B = 8 models × 3 harnesses × 20 tasks**, every cell under an
identical context policy. Balanced in cells; unequal in replicates (5 seeds in
Lane A, 2 in Lane B), which the analysis handles explicitly rather than by
silent reweighting.

Eight models spanning 3B local to hosted frontier-adjacent is a real model axis.
An earlier draft of this design used two 3B local models, which would have made
"harness beats model" an artefact of choosing two models that were never going to
differ.

---

## 4. The context-policy control, and the risk it creates

**This is the most consequential design decision in the project.**

Cerebras' free tier caps context at **8,192 tokens**. Lane A on a 4060 has no such
constraint. If the pooled grid mixed capped and uncapped runs, the model axis
would be **confounded with context policy** — Lane B models could score lower
because their histories were truncated, not because they are less capable, and
the headline comparison would be invalid.

So: **every cell in the pooled grid runs an identical 8K-capped policy**, Lane A
included, even though Lane A does not need it.

### The risk

The mechanism by which `plan_execute` and `react_reflect` are supposed to help
*is carrying more context* — more turns, more accumulated observations, room to
self-critique. **Cap everything at 8K and the control may erase precisely the
advantage being measured**, producing "harness barely matters" as an artefact of
the experimenter's own design choice.

### The mitigation

Block **A3** crosses the compaction ablation on the **full harness axis** — all
five harnesses, uncapped, paired cell-for-cell against the capped runs (same
task, same seed, same harness, same model, differing only in policy).

A3 trades a model for two harnesses deliberately: the effect of interest is a
**harness × policy interaction**, not a model × policy one. The 3B model is
dropped as the least likely to exploit long context or self-critique coherently.

### The reporting rule, pre-declared

> If A3 shows the cap materially suppresses `plan_execute` / `react_reflect`, the
> pooled estimate is reported as a **directional lower bound on the harness
> effect**, with the suppression quantified — **in the abstract, not a footnote**.

A null result under a suppressing cap means something different from a null
result without one, and a reader must not be able to conflate them.

---

## 5. Analysis

### Primary: bootstrap, clustered by task template

The headline claim compares two effect magnitudes, which is a **contrast
comparison**, not literally a variance decomposition. The estimator computes it
directly. Per bootstrap resample of task templates:

- **harness range** = mean over models of (max − min accuracy across harnesses)
- **model range** = mean over harnesses of (max − min accuracy across models)
- **statistic** = harness range − model range

The reported quantity is a confidence interval on that difference.

**Clustering is on the task template, not the generated instance.** Seeds are
replicates nested within a template. Resampling templates makes the interval
answer *"would this hold on a fresh draw of tasks from the generator?"* — the
conservative reading, and the one a reviewer wants.

### Secondary: mixed-effects logistic regression

`success ~ model + harness + (1|task)`, binomial family. Correct for a binary
outcome, tolerates the unequal replicates between lanes, and yields a variance-
component readout that corroborates the bootstrap.

**Disagreement between the two is reported, not resolved by choosing.** They rest
on different assumptions — the bootstrap is assumption-light but sensitive to
having only 20 clusters; the GLMM handles the outcome properly but assumes a
parametric random-effect structure. Divergence is information about the design's
limits.

### Rejected: two-way ANOVA

Assumes a continuous, roughly normal outcome — task success is binary — and
requires a balanced grid, which the unequal seed counts across lanes violate.

---

## 6. Power — checked Day 20, while the grid is still adjustable

If the true effects are close (say 8 points of harness effect against 5 of model
effect), **20 tasks × 5 seeds may be unable to separate them**, and nothing done
afterwards recovers that.

`analysis/power.py` Monte-Carlos **over the real bootstrap** — not a closed-form
approximation — and reports the **minimum detectable effect difference at 80%
power**, with a sensitivity table across plausible baseline accuracies (power
depends heavily on where the cells sit).

Three responses, all cheap on Day 20 and impossible on Day 32:

1. expand the core suite to 30 tasks,
2. add seeds,
3. pre-declare the MDE and report it honestly.

---

## 7. Execution order and the cut ladder

### Lane A runs A1 → A3 → A2

Priority-ordered so that cuts are cheap:

- **A1** is the headline and completes in ~2.5 nights. The primary result exists
  early even if everything after it collapses.
- **A3** tells you whether the headline is floored by your own control, so it
  outranks the secondary harness axis.
- **A2** is the most expendable and runs last.

### Cut ladder, applied at the Day 30 checkpoint

After three nights, measured throughput is extrapolated. If Lane A projects past
Day 33, apply **in order**:

| Step | Action | Saves |
|---|---|---|
| 1 | A3 seeds 3 → 2 | ~7.5 GPU-h |
| 2 | A2 seeds 5 → 3 | ~4.7 GPU-h |
| 3 | A2 drops the 12B model | ~6.7 GPU-h |

Combined, ~19 h — taking 52 h down to ~33 h ≈ 4–5 nights. **A1 is never cut.**

The 12B model alone is ~61% of Lane A's GPU time, which is why the ladder targets
it last but hardest.

---

## 8. The three pre-declared outcomes

Committed in [PREREGISTRATION.md](PREREGISTRATION.md) before any sweep, so the
conclusion is not chosen after seeing the data.

| # | Result | What the paper claims |
|---|---|---|
| 1 | Harness range > model range (CI excludes 0, positive) | The popular claim holds; scaffold choice dominates model choice at fixed cost. |
| 2 | Harness ≈ model (CI contains 0) | **The null — and publishable.** The claim that the harness matters as much as the weights does not hold on affordable models at this task scale. |
| 3 | Harness range < model range | The claim inverts; model choice dominates. Equally a finding. |

Outcome 2 is a *different paper*, and one to be **prepared** to write — not one to
discover the need for on Day 32. Each outcome is reported alongside the §4
suppression estimate, because a floored harness effect changes how outcome 2 is
read.

---

## 9. What this design cannot answer

Stated here so it is not discovered as a criticism later; expanded in
`LIMITATIONS.md`.

- **Only deterministically scorable tasks.** No open-ended generation, because
  scoring those needs a judge model and that reintroduces the bias the project
  exists to avoid. See [adr/0004](adr/0004-no-llm-judge.md).
- **Small local models.** Lane A tops out around 12B at 4-bit on 8 GB. Conclusions
  about scaffold effects at frontier scale are not supported.
- **Low N on quota-starved providers.** Groq's 70B (100K TPD) and OpenRouter
  (50 RPD) appear at low N, disclosed wherever they are reported.
- **Five harnesses, one implementation each.** A negative result about
  `react_reflect` is about *this* implementation, not about reflection as an idea.
- **20 clusters.** Twenty task templates is not many for a cluster bootstrap, and
  the interval widths will show it. This is why the power check exists.
