---
spec: 017
title: Core-20 suite selection and lane assignment
status: Draft
depends_on: [028]
day: 19
---

# SPEC-017 — Core-20 selection and lane assignment

> **Stub.** Depends on SPEC-028: only tasks that have passed solvability
> validation are eligible.

## Scope

**In scope**

- Selecting the 20-task core suite that both lanes share, and which therefore
  carries the pooled primary grid.
- Recording selection criteria and the resulting family/difficulty balance.
- Freezing the suite into `data/suites/core-20.json`.

**Out of scope**

- Changing tasks to fit. Selection picks from what exists; if the balance is
  poor, that is reported, not engineered away after seeing scores.

## Selection criteria, fixed before selection

1. **Family balance** — every family represented; no family more than ~30%.
2. **Difficulty balance** — roughly even across the three tiers.
3. **Discriminating** — the Day-5-to-16 baselines must show the task is neither
   at ceiling nor at floor for every model. A task nothing solves and a task
   everything solves both contribute zero information to a range contrast.
4. **Solvable** — passed SPEC-028, except the refusal tier which passes inversely.
5. **Bounded** — `max_turns` and forecast tokens fit the Lane B per-cell budget.

Criterion 3 is applied using **baseline** runs only, never using data from the
primary sweep. Selecting tasks on the outcome they will be used to measure is the
purest form of the bias this project is built to avoid.

## Acceptance criteria

- **AC-1.** Exactly 20 tasks selected; the file is committed and immutable
  thereafter, enforced by a checksum test.
- **AC-2.** Every criterion above is evaluated and the result recorded per task,
  including for tasks rejected.
- **AC-3.** Family and difficulty balance meet the stated bounds, or the
  deviation is documented in `docs/EXPERIMENT_DESIGN.md`.
- **AC-4.** Selection used only baseline data; a test asserts no primary-sweep
  result predates the suite file's commit.
- **AC-5.** Lane assignment recorded: which harnesses each lane runs, and which
  three form the common subset.
- **AC-6.** The pooled grid is confirmed **balanced in cells** — 8 models × 3
  harnesses × 20 tasks, with no empty cell.
