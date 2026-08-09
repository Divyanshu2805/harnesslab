---
spec: 014
title: Task family 4 — constraint satisfaction over a mock calendar
status: Draft
depends_on: [003, 004]
day: 14
---

# SPEC-014 — Task family 4: constraint satisfaction

> **Stub.**

## Scope

**In scope**

- ~8 tasks over `CalendarEnv`: find and book slots satisfying a conjunction of
  constraints (availability, duration, ordering, exclusions).
- Difficulty by constraint count and by whether constraints interact.
- Final-state scoring — the booking either satisfies every constraint or does not.

**Out of scope**

- Genuinely unsatisfiable instances. Those belong to the refusal tier (SPEC-016),
  and mixing them in here would conflate "failed to satisfy" with "correctly
  declined".

## Acceptance criteria

- **AC-1.** All tasks registered with stable IDs, constraint count, `max_turns`.
- **AC-2.** Every generated instance is **verified satisfiable at generation
  time** by a solver run inside the generator — an accidentally unsatisfiable
  instance is indistinguishable from a broken task.
- **AC-3.** The scorer checks every constraint independently and reports which
  failed, so failure analysis can tell a near-miss from a wild answer.
- **AC-4.** Reference solution 1.0, mutated variant 0.0, per task.
- **AC-5.** Where multiple valid bookings exist, **all** are accepted — the
  scorer validates against the constraints, never against one privileged
  solution.
- **AC-6.** Constraint count is strictly increasing across tiers.
