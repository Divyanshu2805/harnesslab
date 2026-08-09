---
spec: 007
title: Harnesses — single_shot and react
status: Draft
depends_on: [003, 006]
day: 7
---

# SPEC-007 — Harnesses: `single_shot` and `react`

> **Stub.** Scope and acceptance criteria only. The interface contract is written
> when this spec is picked up, against the real behaviour of Inspect's
> `Agent`/`AgentState` rather than against a guess. See `specs/README.md`.

## Scope

**In scope**

- `harnesses/base.py`: the shared contract every harness implements — turn cap,
  context policy, per-turn telemetry, submission handling.
- `single_shot`: one generation with tools available but no observation loop.
  The floor of the harness axis.
- `react`: the reason-act-observe loop, built on Inspect's `react()` agent.
- Calibration of the SPEC-006 estimator parameters from the first real logs.

**Out of scope**

- `plan_execute`, `react_retry` (SPEC-008); `react_reflect` and the compaction
  policies (SPEC-009).
- Any model selection — a harness is a solver and must be model-agnostic.

## Acceptance criteria

- **AC-1.** Both harnesses satisfy a common `Harness` protocol and are
  interchangeable in a `Task` without touching the task definition.
- **AC-2.** Every harness receives an identical toolset for a given task —
  verified by comparing rendered tool schemas across harnesses.
- **AC-3.** `max_turns` is enforced; exceeding it terminates the trajectory and
  records a distinct `turn_cap_exhausted` outcome, not a generic failure.
- **AC-4.** Per-turn telemetry (call index, input/output tokens, tool calls,
  context size) is written into the sample Store and survives into the `.eval` log.
- **AC-5.** On the same task and seed, `single_shot` and `react` produce
  **measurably different** accuracy on the hard tier — the axis moves at all.
- **AC-6.** Estimator parameters for both harnesses are calibrated to within the
  ±25% required by SPEC-006 AC-2, and the measured values are committed.
- **AC-7.** Neither harness inspects the model identity or branches on it.

## Notes for the author

The Day 5 baseline used a bare `generate()`. AC-5 is the first evidence about the
headline hypothesis; if the hard tier does not separate, say so in the spec's
result log rather than adjusting tasks until it does.
