---
spec: 016
title: Task family 6 — refusal tier
status: Draft
depends_on: [004]
day: 16
---

# SPEC-016 — Task family 6: refusal tier

> **Stub.**

## Scope

**In scope**

- 8 **impossible** tasks where the correct answer is "this cannot be done":
  referenced file absent, constraints mutually contradictory, required data not
  in the schema, permission genuinely unavailable.
- The `refusal()` scorer's classification rule set (SPEC-004).
- A hand-labelled calibration set measuring the classifier's own error rate.

**Out of scope**

- Hard-but-possible tasks. If a strong model can solve it, it is not a refusal
  task and belongs elsewhere.

## Why this family is worth a whole day

Benchmarks report success on solvable tasks and say almost nothing about whether
an agent knows when to stop. An agent that fabricates a plausible answer rather
than declining is *worse* than one that fails visibly, and nothing in the other
five families would distinguish them.

The failure mode of interest is three-way, which is why `refusal()` requires
three conditions: solve attempt that loops to the turn cap, fabrication with a
confident answer, and correct decline are different behaviours and must not
collapse into one number.

## Acceptance criteria

- **AC-1.** 8 tasks registered, each flagged `solvable=False`.
- **AC-2.** **Inverse validation**: each task is verified to have *no* valid
  solution — the check that SPEC-028 applies in reverse for this family.
- **AC-3.** A fabricated-but-plausible submission scores 0.0, including when the
  agent also wrote a convincing artifact into the environment.
- **AC-4.** A turn-cap exhaustion scores 0.0 and is recorded as
  `turn_cap_exhausted`, not as a refusal.
- **AC-5.** An explicit, correct decline with an unmodified environment scores 1.0.
- **AC-6.** **The refusal classifier's error rate is measured** against ≥50
  hand-labelled submissions and reported in `docs/SCORING.md`. A deterministic
  rule set will have false negatives on unusual phrasings; that cost is accepted
  and disclosed as a number, not left unknown.
- **AC-7.** Refusal accuracy is reported as its own metric, never averaged into
  overall task success — they measure different things.
