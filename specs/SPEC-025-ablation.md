---
spec: 025
title: Ablation — range contrast, GLMM, and the suppression estimate
status: Draft
depends_on: [024]
day: 27
---

# SPEC-025 — Ablation analysis

> **Stub.** Implemented Day 27 against partial data; run for the headline on
> Day 32 once A1 and Lane B are complete.

## Scope

**In scope**

- The primary analysis: bootstrap range contrast over the pooled 8 × 3 × 20 grid.
- The confirmatory analysis: mixed-effects logistic regression,
  `success ~ model + harness + (1|task)`, binomial.
- The **suppression estimate** from block A3: how much the 8K context cap
  depresses `plan_execute` and `react_reflect` relative to uncapped.
- A report mapping the result onto one of the three pre-declared outcomes.

**Out of scope**

- Choosing the outcome after seeing data. The three outcomes and their claims are
  fixed in `docs/PREREGISTRATION.md`, committed Day 22.

## The suppression estimate is not optional

Every pooled cell runs capped at 8K to remove the model/policy confound. But the
mechanism by which the reflective harnesses help *is carrying more context*, so
the control may erase the very advantage being measured. Block A3 pairs capped
against uncapped on the full harness axis to quantify that.

Pre-declared reporting rule: **if the cap materially suppresses those harnesses,
the pooled estimate is reported as a directional lower bound on the harness
effect, with the suppression quantified** — in the abstract, not a footnote. A
null result under a suppressing cap means something different from a null result
without one, and the paper must not let a reader conflate them.

## Acceptance criteria

- **AC-1.** The primary contrast and its CI are computed over the pooled grid,
  primary seed regime only, capped policy only.
- **AC-2.** The GLMM converges and its fixed effects are reported alongside the
  bootstrap; disagreement between the two is reported, not reconciled by choosing.
- **AC-3.** The suppression estimate is computed from **paired** A3 cells — same
  task, seed, harness, model, differing only in policy.
- **AC-4.** The report states which of the three pre-declared outcomes obtains,
  citing the prereg commit hash.
- **AC-5.** Every reported number carries N, its CI, and its lane attribution.
- **AC-6.** The analysis is reproducible from the results store and a seed: same
  inputs, same numbers.
- **AC-7.** A null result (CI containing 0) produces a complete report, not an
  error path — this is a pre-declared publishable outcome and the code must treat
  it as a first-class result.
- **AC-8.** Refuses to run if any pooled cell is empty or if policies are mixed.
