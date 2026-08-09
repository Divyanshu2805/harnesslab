# ADR 0007 — Cluster bootstrap on task template, not two-way ANOVA

**Status:** Accepted · **Date:** 2026-08-09

## Context

The headline is *"scaffold choice shifted task success by X points versus Y for
model choice"*. The phrase "variance decomposition" invites two-way ANOVA over
model × harness.

Two problems with that reflex.

First, **ANOVA's assumptions do not hold here**: task success is **binary**, not
continuous and roughly normal, and the pooled grid has **unequal replicates**
across lanes (5 seeds in Lane A, 2 in Lane B).

Second — and more fundamental — **the claim is not actually a variance
decomposition.** It compares *two effect magnitudes*. Those are different
estimands, and choosing the analysis to match the phrase rather than the claim
would answer a question nobody asked.

The method also has to be chosen **before** the grid is built, because it
determines what the grid must look like.

## Decision

**Primary: cluster bootstrap, clustering on task template.** Per resample:

```
harness_range = mean over models   of ( max − min accuracy across harnesses )
model_range   = mean over harnesses of ( max − min accuracy across models )
statistic     = harness_range − model_range
```

Reported: point estimate and 95% percentile CI on that difference.

**Secondary: mixed-effects logistic regression**, `success ~ model + harness +
(1|task)`, binomial — correct for a binary outcome, tolerant of unequal
replicates, and yielding a variance-component readout that corroborates the
bootstrap.

## The clustering unit is the point

Clustering on the **task template**, not the generated instance. Seeds are
replicates *nested within* a template.

This makes the interval answer: **"would this hold on a fresh draw of tasks from
this generator?"** — rather than the much weaker "would this hold on more seeds
of these same 20 tasks?"

It is the conservative choice. It produces wider intervals, and it is the
question a reviewer is actually asking.

## Consequences

**Good.** The estimator matches the claim exactly, and needs no distributional
assumptions about a binary outcome.

**Good.** Disagreement between bootstrap and GLMM is **reported, not resolved by
choosing**. They fail in different ways — the bootstrap is sensitive to having
only 20 clusters, the GLMM assumes a parametric random-effect structure — so
divergence is information about the design's limits.

**Cost, and it is the binding one.** Twenty task templates is **not many
clusters**. Interval widths will show it. This is precisely why the Day 20 power
check exists, why it Monte-Carlos over the real bootstrap rather than a
closed-form approximation, and why the MDE is reported regardless of outcome —
without it, an interval containing zero is uninterpretable.

**Cost.** Slower than a closed-form test, and it must run thousands of times
inside the power simulation, hence
[SPEC-024 AC-7](../../specs/SPEC-024-bootstrap-core.md)'s performance
requirement.

## Alternatives rejected

**Two-way ANOVA.** Binary outcome, unbalanced replicates, and — decisively — the
wrong estimand.

**Bootstrap clustered on the generated instance.** Narrower intervals that
answer a weaker question, and would overstate confidence.

**GLMM alone as primary.** Handles the outcome correctly but requires trusting a
parametric random-effect structure on 20 clusters, and its output is a
coefficient rather than the range contrast the claim is about.

**Report both effects with separate CIs and eyeball the overlap.** Comparing two
intervals is not a test of their difference; non-overlap is sufficient for
significance but not necessary, and this is a common error. The CI is computed
**on the difference**.
