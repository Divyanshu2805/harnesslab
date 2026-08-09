# ADR 0010 — Every task validated solvable before any sweep

**Status:** Accepted · **Date:** 2026-08-09

## Context

**A task no model completes is indistinguishable from a broken task.**

A broken task — a wrong target derivation, an unsatisfiable generated instance, a
subtly impossible predicate — scores 0 for every model and every harness. In
aggregate it looks exactly like a hard task, and nothing in the results
distinguishes them.

The damage is not merely noise. A floor effect **suppresses all harness
differences equally**, because no scaffold can rescue an impossible task. A
handful of broken tasks in a 20-task core suite would compress the harness range,
shrink the model range, and **manufacture a null result** — the one outcome that
looks like a finding while being an artefact.

## Decision

**[SPEC-028](../../specs/SPEC-028-solvability-validation.md) is a gate on Day 18.
No task reaches a sweep until it passes**, and it runs *before* core-20 selection
so only validated tasks are eligible.

Two checks, answering different questions:

**1. Programmatic reference solution (primary).** A scripted tool-call sequence
per task that the scorer must score 1.0, at every primary seed. Deterministic,
committed, and run in CI. **Failing this means the task is broken** — fix or cut.

**2. Strong-model check (secondary).** A capable hosted model solves it at least
once.

The distinction matters: (1) asks *is this achievable in principle*, (2) asks *is
this achievable by an LLM agent*. **Passing (1) and failing (2) is a legitimately
hard task** — exactly what the hard tier wants — so it is flagged, not cut.

**Refusal-tier tasks are validated inversely**: assert no valid solution exists,
and that `refusal()` fires on a correct decline.

## Consequences

**Good.** The reference solutions are the same artifact
[SPEC-004 AC-1](../../specs/SPEC-004-scorers.md) already needed as known-good
trajectories. One piece of work proves both *the scorer is right* and *the task
is solvable*.

**Good.** Committed and run in CI, they become a **regression tripwire**: a later
change to the generator or a scorer that breaks solvability fails the build
rather than silently degrading a future sweep.

**Cost — and it must be budgeted.** The strong-model check is ~53 tasks × ~8
calls ≈ 424 calls, budgeted **2× for re-runs of initial failures ≈ 850 calls**.
Against Gemini Flash-Lite's 1,000 RPD that is tight, not free.

It is therefore booked in the ledger as a **named reservation owning the whole
day**, with Groq `llama-3.1-8b-instant` as spill target and Day 17's buffer as
overflow. Without the reservation, a nightly smoke run at 02:00 would consume the
quota and Day 18 would fail at task 40 of 53. This is the concrete failure that
motivated named reservations in [ADR 0003](0003-token-budget-first.md).

**Cost.** A full day, plus authoring a reference solution per task. Cheap against
the alternative: discovering a broken task after the sweep means either
discarding the affected cells or re-running them, and free-tier quota does not
allow a second sweep.

## Alternatives rejected

**Assume tasks are solvable because the author wrote them.** How broken tasks
reach production. Target derivations are code, and code has bugs.

**Strong-model check only.** Cheaper to author, but conflates "no model solved
it" with "it is impossible", which is the exact ambiguity being removed. It also
makes the suite's validity depend on one model's capability on one day.

**Validate after the sweep, discard failures.** Post hoc exclusion after seeing
results is indistinguishable from selecting tasks on the outcome — the bias this
project exists to avoid.

**Validate during core-20 selection.** Would work, but conflates two decisions.
Selection should choose among *known-good* tasks on discrimination and balance,
not simultaneously discover which ones are broken.
