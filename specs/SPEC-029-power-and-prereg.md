---
spec: 029
title: Power analysis and pre-registration
status: Draft
depends_on: [024]
day: 20
---

# SPEC-029 — Power analysis and pre-registration

> **Stub.** Two deliverables on two days: the power check lands **Day 20**, while
> the grid is still adjustable; `docs/PREREGISTRATION.md` is committed and
> timestamped **Day 22**, before any sweep data exists.

## Why the power check is Day 20 and not later

The headline compares two effect magnitudes. If the true effects are close —
say 8 points of harness effect against 5 of model effect — **20 tasks × 5 seeds
may simply be unable to separate them**, and no amount of careful analysis
afterwards recovers that. Discovering it on Day 32 is unrecoverable; discovering
it on Day 20 leaves three responses open, all cheap:

1. expand the core suite to 30 tasks,
2. add seeds,
3. pre-declare the minimum detectable effect and report it honestly.

The check Monte-Carlos **over the SPEC-024 bootstrap itself** rather than using a
closed-form approximation, because the bootstrap is what will actually be run and
its clustering on task template is what determines the achievable precision.

## Why pre-registration is worth an hour

It is one of the strongest honesty signals available to an independent
researcher, and it costs almost nothing. Committing the hypothesis, the analyses,
the estimand, and the null criteria to git **before** any data exists, then citing
the commit hash in the paper, converts "we did not p-hack" from an assurance into
a checkable fact.

## Scope

**In scope**

- `analysis/power.py` — simulate binomial cell outcomes under assumed accuracies,
  run the real bootstrap, report power and the **minimum detectable effect
  difference at 80% power**.
- A grid-adjustment decision recorded on Day 20.
- `docs/PREREGISTRATION.md`: hypothesis, primary analysis, secondary analysis,
  estimand, the three pre-declared outcomes, null criteria, stopping rule.

## Acceptance criteria

- **AC-1.** The simulator generates cell outcomes under specified true
  accuracies and recovers known power on a case with an analytic answer.
- **AC-2.** MDE at 80% power is reported for the planned grid (8 × 3 × 20, 5
  primary seeds Lane A / 2 Lane B).
- **AC-3.** A sensitivity table reports MDE across plausible baseline accuracies
  — power depends heavily on where the cells sit, and a single number would
  mislead.
- **AC-4.** The Day-20 decision is recorded: grid unchanged, or expanded, or MDE
  pre-declared — with reasoning.
- **AC-5.** `PREREGISTRATION.md` is committed **before** any `seed_regime='primary'`
  row exists, verified by a test comparing the commit timestamp to the earliest
  primary row.
- **AC-6.** The prereg names all three outcomes, including the null, with the
  claim each supports.
- **AC-7.** The prereg states the stopping rule — the sweep runs to its planned
  size and is not stopped early on a favourable interim result.
- **AC-8.** The commit hash is recorded where the paper can cite it.

## Power result

> _Filled Day 20._
>
> | Baseline accuracy | MDE @ 80% power | Decision |
> |---|---|---|
> | | | |
