---
spec: 031
title: Full statistics module — CIs, GLMM, variance components
status: Draft
depends_on: [024]
day: 29
---

# SPEC-031 — Full statistics module

> **Stub.** Split from SPEC-024, which shipped the bootstrap core on Day 19 so
> the power analysis could run against it. This spec adds everything the headline
> report needs beyond that one contrast.

## Scope

**In scope**

- Bootstrap CIs for every reported quantity: per-cell accuracy, per-harness
  marginal, per-model marginal, per-family breakdown, refusal accuracy.
- The confirmatory mixed-effects logistic regression,
  `success ~ model + harness + (1|task)`, binomial, via statsmodels.
- Variance components from the GLMM, as the corroborating readout.
- Reporting helpers that emit numbers with N and CI attached, for SPEC-021's
  charts and SPEC-030's LaTeX macros.

**Out of scope**

- The headline contrast — SPEC-024 owns the estimator, SPEC-025 the report.

## Design note

**Disagreement between the bootstrap and the GLMM is reported, not resolved by
choosing.** They rest on different assumptions: the bootstrap is assumption-light
but sensitive to the cluster count (20 task templates is not many), while the
GLMM handles the binary outcome and unequal replicates properly but assumes a
parametric random-effect structure. If they diverge, that divergence is
information about the design's limits and belongs in the paper.

## Acceptance criteria

- **AC-1.** Every reported quantity has a CI computed by the SPEC-024 resampler,
  clustered identically.
- **AC-2.** The GLMM converges on the pooled grid; non-convergence fails loudly
  with diagnostics rather than returning a silent fallback.
- **AC-3.** Variance components are reported with their interpretation stated —
  they corroborate the contrast, they are not the headline.
- **AC-4.** Bootstrap and GLMM results are reported side by side, with any
  disagreement flagged.
- **AC-5.** All outputs carry N and lane attribution.
- **AC-6.** Reporting helpers emit LaTeX macros consumed directly by the paper,
  satisfying SPEC-030 AC-3.
- **AC-7.** Reproducible from the results store plus a seed.
- **AC-8.** Refuses to pool across seed regime or context policy (SPEC-024 AC-5).
