---
spec: 012
title: Task family 2 — SQL over SQLite
status: Draft
depends_on: [003, 004]
day: 12
---

# SPEC-012 — Task family 2: SQL

> **Stub.**

## Scope

**In scope**

- ~8 tasks over a generated relational schema, across three difficulty tiers:
  single-table filters → joins → aggregation with a grouping subtlety.
- Difficulty measured structurally by required join depth and predicate count.
- Scoring by `exact_match` on the answer, since the tool is read-only and there
  is no final state to compare.

**Out of scope**

- Write queries. `run_query` is read-only by design (SPEC-003) — allowing writes
  would let a task be "solved" by mutating the grading substrate.

## Acceptance criteria

- **AC-1.** All tasks registered with stable IDs, tiers, toolset, and `max_turns`.
- **AC-2.** Schemas and rows generate deterministically from the seed.
- **AC-3.** Each task has a programmatic reference solution scoring 1.0, and a
  mutated variant scoring 0.0.
- **AC-4.** Answers are normalised by exactly the SPEC-004 rules — no numeric
  tolerance, no column-order leniency beyond what is documented.
- **AC-5.** Join depth is strictly increasing across tiers.
- **AC-6.** A task whose answer is ambiguous under the documented normalisation
  is rejected in review — ambiguity here shows up later as unexplained variance.
