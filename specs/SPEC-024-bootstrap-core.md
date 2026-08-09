---
spec: 024
title: Bootstrap core — resampler and range-contrast estimator
status: Draft
depends_on: []
day: 19
---

# SPEC-024 — Bootstrap core

> **Stub.** Deliberately split from the full statistics module (SPEC-031) and
> scheduled **early**, because SPEC-029's power analysis Monte-Carlos *over* this
> procedure and cannot run before it exists. An earlier plan revision had the
> power check on Day 18 and the statistics on Day 25 — a dependency that resolved
> on paper and was unrunnable in practice.

## Scope

**In scope**

- The cluster bootstrap resampler, clustering on **task template**.
- The range-contrast estimator: harness range, model range, and the difference
  between them.
- A deterministic RNG path so a published interval is reproducible.

This spec depends on **nothing**. It is generic statistics over a results table
shape and is developed and tested entirely on **synthetic** data (AC-2, AC-3),
which is what lets it land on Day 19 alongside the suite selection rather than
after it — and therefore what lets SPEC-029's power analysis run on Day 20.

**Out of scope**

- CIs on every reported quantity, the GLMM, variance components — SPEC-031.
- The ablation report itself — SPEC-025.

## The estimator

Per bootstrap resample of task templates:

- **harness range** = mean over models of (max − min accuracy across harnesses)
- **model range** = mean over harnesses of (max − min accuracy across models)
- **statistic** = harness range − model range

The reported quantity is a CI on that difference. This matches the claim being
made — a comparison of two effect magnitudes — rather than a variance
decomposition, which is a different thing that the popular phrasing invites.

**Clustering on the template, not the instance**, is deliberate: seeds are
replicates nested within a template, so resampling templates makes the interval
answer *"would this hold on a fresh draw of tasks from the generator?"* That is
the conservative reading and the one a reviewer wants.

## Acceptance criteria

- **AC-1.** The resampler clusters on task template; seeds within a template move
  together, verified by inspecting resample composition.
- **AC-2.** On synthetic data with a known ground-truth contrast, the estimator
  recovers it within Monte-Carlo error.
- **AC-3.** Coverage: over repeated synthetic draws, the nominal 95% interval
  covers the truth at ~95%.
- **AC-4.** Deterministic given a seed — the same data and seed reproduce the
  same interval byte for byte.
- **AC-5.** Refuses to pool across `seed_regime` (SPEC-023 AC-5) or across
  `context_policy`, raising rather than silently averaging.
- **AC-6.** Handles the unbalanced replicate counts between lanes (5 primary
  seeds in Lane A, 2 in Lane B) without silently reweighting; the weighting is
  explicit and documented.
- **AC-7.** Runs on the pooled grid's shape in seconds, since SPEC-029 will call
  it thousands of times.
