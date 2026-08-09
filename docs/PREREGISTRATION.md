# Pre-registration

> **Status: DRAFT — not yet binding.**
>
> This document becomes binding when it is committed with its status changed to
> `REGISTERED` on **Day 22**, before any `seed_regime='primary'` row exists.
> The commit hash of that change is cited in the paper.
>
> [SPEC-029 AC-5](../specs/SPEC-029-power-and-prereg.md) enforces the ordering by
> comparing the commit timestamp against the earliest primary result row. If any
> primary data predates registration, the check fails and the paper cannot claim
> pre-registration.

Registering costs about an hour. It converts *"we did not choose the conclusion
after seeing the data"* from an assurance into a checkable fact, which is one of
the strongest honesty signals available to an independent researcher.

---

## 1. Hypothesis

The widely repeated claim under test:

> *The harness matters as much as the weights.*

Stated as a testable comparison:

> **H1.** On a fixed task suite at fixed context policy, varying the agent
> harness produces a **larger** spread in task success than varying the model.

The comparison is between **two effect magnitudes**, not a decomposition of
variance. This distinction determines the estimator (§3) and is the reason
two-way ANOVA is rejected.

---

## 2. Design (fixed before data)

- **Pooled primary grid:** 8 models × 3 harnesses × 20 tasks.
  - Harnesses: `single_shot`, `react`, `react_retry`.
  - Models: 3 local (Lane A) + 5 hosted free-tier (Lane B).
  - Balanced in cells; replicates 5 (Lane A) / 2 (Lane B).
- **Context policy:** identical across every pooled cell, capped at 8,192 tokens.
- **Seed regime:** `primary` only, from `data/seeds/primary-v1.json`.
- **Scoring:** deterministic — final-state comparison and exact match. **No LLM
  judge.**
- **Task suite:** the frozen core-20 (`data/suites/core-20.json`), selected on
  baseline data only, before any primary sweep.

Full rationale in [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md).

---

## 3. Primary analysis

**Cluster bootstrap, clustering on task template.**

Per resample of task templates (with replacement):

```
harness_range = mean over models   of ( max − min accuracy across harnesses )
model_range   = mean over harnesses of ( max − min accuracy across models )
statistic     = harness_range − model_range
```

**Estimand:** the difference between the harness range and the model range.
**Reported:** point estimate and 95% percentile bootstrap CI.

Clustering is on the **template**, not the generated instance; seeds are
replicates nested within a template. The resulting interval answers *"would this
hold on a fresh draw of tasks from this generator?"*

Unequal replicates between lanes are handled by explicit, documented weighting —
not silent reweighting.

---

## 4. Secondary analysis

**Mixed-effects logistic regression**, `success ~ model + harness + (1|task)`,
binomial family.

Reported alongside the bootstrap as corroboration. **If the two disagree, the
disagreement is reported, not resolved by choosing.** They rest on different
assumptions — the bootstrap is assumption-light but sensitive to having only 20
clusters; the GLMM handles the binary outcome and unequal replicates properly but
assumes a parametric random-effect structure. Divergence is information about the
design's limits, and suppressing it would be the exact failure this document
exists to prevent.

---

## 5. The suppression estimate (block A3)

Every pooled cell runs capped at 8K, to remove the confound between the model
axis and context policy. But the mechanism by which `plan_execute` and
`react_reflect` are supposed to help **is carrying more context**, so the control
may suppress the very effect being measured.

Block A3 pairs capped against uncapped runs across the **full five-harness axis**
(same task, seed, harness, model — differing only in policy) and estimates that
suppression.

**Pre-declared reporting rule:**

> If A3 shows the cap materially suppresses `plan_execute` or `react_reflect`,
> the pooled estimate is reported as a **directional lower bound on the harness
> effect**, with the suppression quantified, **in the abstract — not a footnote**.

---

## 6. Pre-declared outcomes

All three are registered now. Each is a publishable result; none is a failure.

| # | Criterion | The claim the paper makes |
|---|---|---|
| **1** | CI on the statistic **excludes 0, positive** | The claim holds: scaffold choice moves task success more than model choice, at these scales and at fixed cost. |
| **2** | CI **contains 0** | **The null.** The claim that the harness matters as much as the weights does not hold on affordable models at this task scale. Reported as a measured null, with the MDE from §7 so a reader can distinguish "no effect" from "insufficient power". |
| **3** | CI **excludes 0, negative** | The claim inverts: model choice dominates scaffold choice. |

Each is reported together with the §5 suppression estimate, because a floored
harness effect changes how outcome 2 must be read.

**Outcome 2 is a different paper, and one to be prepared to write** — not one to
discover the need for on Day 32.

---

## 7. Power

The minimum detectable effect difference at 80% power is computed on **Day 20**,
before the sweep, by Monte-Carlo over the actual bootstrap procedure (not a
closed-form approximation), across a sensitivity range of plausible baseline
accuracies.

**The MDE is reported in the paper regardless of outcome.** Without it, outcome 2
is uninterpretable — an interval containing zero means nothing if the design
could never have excluded it.

> _Filled Day 20 from [SPEC-029](../specs/SPEC-029-power-and-prereg.md)._
>
> | Baseline accuracy | MDE @ 80% power |
> |---|---|
> | | |

---

## 8. Stopping rule

**The sweep runs to its planned size.** It is not stopped early on a favourable
interim result, and it is not extended in search of one.

The only permitted deviation is the **pre-declared cut ladder** in
[EXPERIMENT_DESIGN.md §7](EXPERIMENT_DESIGN.md), which is triggered by *GPU-time
overrun* and never by results. Its steps are fixed in advance, they touch only
blocks A2 and A3, and **A1 — the pooled grid carrying the primary analysis — is
never cut**. Any cut applied is recorded in the results and reported.

---

## 9. What would falsify H1

Stated explicitly so it cannot be quietly reinterpreted:

- A CI on the statistic containing 0 falsifies H1 as stated (outcome 2).
- A CI excluding 0 on the negative side falsifies it more strongly (outcome 3).
- H1 is **not** rescued by switching to a different estimand, by dropping a
  model or harness after seeing results, by expanding the task suite post hoc, or
  by moving to the extended five-harness axis if the three-harness pooled grid
  shows nothing.

Analyses beyond §3–§5 are permitted and welcome, but any not registered here is
labelled **exploratory** in the paper.

---

## 10. Deviations

Any departure from this document is recorded below with its date and reason,
rather than silently applied.

| Date | Deviation | Reason |
|---|---|---|
| | | |
