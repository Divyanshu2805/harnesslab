---
spec: 028
title: Solvability validation and reference solutions
status: Draft
depends_on: [012, 013, 014, 015, 016]
day: 18
---

# SPEC-028 — Solvability validation

> **Stub.** A **gate**: no task reaches a sweep until it passes.

## Why this exists

**A task no model completes is indistinguishable from a broken task.** A suite
containing broken tasks silently compresses every accuracy number toward zero,
and the compression is invisible — it looks like models being bad rather than
like a bug in a target derivation. Worse, it damages the headline: a floor
effect suppresses *all* harness differences equally, which manufactures a null
result.

Validation runs before the core-20 selection (SPEC-017) so that only eligible
tasks are selectable.

## Scope

**In scope**

- A programmatic reference solution for every non-refusal task, committed and run
  in CI.
- Inverse validation for the refusal tier.
- The strong-model check, with its quota booked as a named ledger reservation.
- A committed validation report recording both outcomes and a disposition per
  task.

**Out of scope**

- Choosing which validated tasks enter the core suite — SPEC-017, which selects
  only from tasks passing here.
- Fixing tasks found broken. That is a change to the owning family's spec.

## Two checks, answering different questions

1. **Programmatic reference solution (primary).** A scripted tool-call sequence
   per task that the scorer must score 1.0. Deterministic, and it doubles as the
   SPEC-004 regression test — the same artifact proves the scorer works and the
   task is achievable. **Failing this means the task is broken**: fix or cut.

2. **Strong-model check (secondary).** A capable hosted model solves the task at
   least once. This asks whether the task is achievable *by an LLM agent*, which
   is a different question from whether it is achievable in principle. **Passing
   (1) and failing (2) is a legitimately hard task**, and is exactly the kind of
   task the hard tier wants — it is recorded, not cut.

**Refusal-tier tasks are the deliberate exception**, validated inversely: assert
that no valid solution exists and that `refusal()` fires correctly.

## Budget

The strong-model check is ~53 tasks × ~8 calls ≈ 424 calls, budgeted at **2× for
re-runs of initial failures ≈ 850 calls**. Against Gemini Flash-Lite's 1,000 RPD
that is tight, not free. It is booked in the SPEC-006 ledger as a **named
reservation owning the whole day**, with Groq `llama-3.1-8b-instant` as the spill
target and Day 17's buffer as overflow. Without the reservation, a nightly smoke
run at 02:00 would consume the quota and Day 18 would fail at task 40 of 53.

## Acceptance criteria

- **AC-1.** Every non-refusal task has a programmatic reference solution scoring
  exactly 1.0, at every primary seed.
- **AC-2.** Every non-refusal task has a mutated reference scoring exactly 0.0 —
  the task discriminates.
- **AC-3.** Every refusal task is verified to have no valid solution, and
  `refusal()` fires on a correct decline.
- **AC-4.** The strong-model check is run and its outcome recorded per task.
  Tasks passing (1) and failing (2) are flagged **hard**, not removed.
- **AC-5.** Any task failing (1) is fixed or cut, and the disposition is recorded.
- **AC-6.** The check's quota consumption is booked as a named reservation and
  recorded in the ledger.
- **AC-7.** A validation report is committed listing every task, both check
  outcomes, and disposition. SPEC-017 selects only from tasks passing here.
- **AC-8.** Reference solutions are committed and run in CI, so a later change to
  the generator or scorer that breaks solvability fails the build.

## Validation report

> _Filled Day 18. SPEC-017 does not start until this is complete._
>
> | Task | Ref. solution | Strong model | Disposition |
> |---|---|---|---|
> | | | | |
