---
spec: 013
title: Task family 3 — multi-hop tool composition
status: Draft
depends_on: [003, 004]
day: 13
---

# SPEC-013 — Task family 3: multi-hop tool composition

> **Stub.**

## Scope

**In scope**

- ~7 tasks requiring output from one tool to become input to another, across two
  or more toolsets (filesystem → SQL, SQL → filesystem).
- Explicit hop-count metadata per task, since hop count is this family's
  difficulty axis and a natural covariate in the analysis.

**Out of scope**

- Tasks solvable by a single lucky call — those belong in family 1 or 2.

## Why this family matters to the headline

This is where a harness should matter most: a `single_shot` solver cannot see a
tool result before deciding its next action, so multi-hop tasks are close to the
cleanest test of whether the scaffold does anything. If harness effects are
invisible here, they are unlikely to be real anywhere.

## Acceptance criteria

- **AC-1.** All tasks registered with stable IDs, hop count, toolset, `max_turns`.
- **AC-2.** Every task has a minimum hop count of ≥2, verified by asserting the
  reference solution's tool-call dependency chain.
- **AC-3.** No task is solvable without observing an intermediate result —
  verified by a control run where tool outputs are replaced with placeholders,
  which must score 0.
- **AC-4.** Reference solution 1.0, mutated variant 0.0, per task.
- **AC-5.** Environments across the two toolsets are generated from the **same**
  seed and are mutually consistent — a filesystem manifest that disagrees with
  the SQL rows would make the task unsolvable in a way that looks like model
  failure.
