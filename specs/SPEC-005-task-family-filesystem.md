---
spec: 005
title: Task family 1 — filesystem, 10 tasks across 3 difficulty tiers
status: Draft
depends_on: [003, 004]
day: 5
---

# SPEC-005 — Task family 1: filesystem

## Motivation

This is the first end-to-end slice: generator → tools → task → scorer → a real
accuracy number. It is scheduled on Day 5 specifically so that the first number
arrives before two more weeks of infrastructure gets built on assumptions.

Filesystem tasks lead because they are the cleanest fit for final-state scoring.
Correctness is "the workspace looks like this afterwards", which is decidable by
byte comparison and needs no judgement call. Later families relax that in
controlled ways; this one establishes the pattern.

The family also fixes the **task authoring template** every later family follows.
Getting that template right here is most of the value of the spec.

## Scope

**In scope**

- 10 filesystem tasks: 4 easy, 3 medium, 3 hard.
- The `Task` construction pattern: dataset from seeds, solver injected by the
  harness under test, scorer from SPEC-004.
- Task metadata carrying the target state and the core-suite flag.
- `harnesslab run --task <id> --model <m>` producing a scored log.

**Out of scope**

- Harnesses. Day 5 runs against a bare `generate()` baseline; SPEC-007 brings the
  real ones.
- Other families — SPEC-012 through 016.
- Core-20 selection — SPEC-017 decides which tasks make the pooled grid.

## Interface contract

```python
# src/harnesslab/tasks/filesystem.py
from inspect_ai import Task, task
from inspect_ai.dataset import Sample


@task
def fs_reorganise(difficulty: Difficulty = Difficulty.MEDIUM, seeds: list[int] | None = None) -> Task:
    """Move files into a directory layout implied by their contents.

    Dataset: one Sample per seed. The environment is generated at solve time
    from the seed carried in metadata, so the task definition holds no fixed
    content -- that is what makes the suite contamination-resistant.
    """
    return Task(
        dataset=[_sample(seed, difficulty) for seed in (seeds or DEFAULT_SEEDS)],
        solver=None,            # injected by the harness under test
        scorer=final_state(),
    )
```

```python
# src/harnesslab/tasks/registry.py
class TaskMeta(BaseModel, frozen=True):
    task_id: str                  # stable, e.g. "fs.reorganise"
    family: str                   # "filesystem"
    difficulty: Difficulty
    toolset: ToolSet
    in_core_20: bool = False      # set by SPEC-017
    solvable: bool = True         # False only for the refusal tier
    max_turns: int                # per-task ceiling; bounds worst-case tokens


def all_tasks() -> dict[str, TaskMeta]: ...
def core_suite() -> list[TaskMeta]: ...
```

**Invariants**

- `task_id` is stable forever — it is a column in every result row.
- A task definition contains **no generated content**. Everything comes from
  `generate_env(seed, spec)`, so the same task at a different seed is a genuinely
  fresh instance.
- Every task declares `max_turns`. Unbounded loops are the single largest
  uncontrolled token cost, and the estimator in SPEC-006 needs a ceiling to
  forecast against.
- The target state is derived from the seed by the same pure function the
  reference solution uses — targets are never hand-transcribed.

## Design notes

**The ten tasks.** Difficulty is *structural*, not a vibe — it is the number of
dependent steps and the amount of discrimination required:

| # | Task | Tier | Shape |
|---|---|---|---|
| 1 | `fs.read_answer` | easy | Read one file, answer a question about it |
| 2 | `fs.count_matches` | easy | `grep` for a pattern, report the count |
| 3 | `fs.copy_one` | easy | Create one file with specified content |
| 4 | `fs.find_largest` | easy | List a directory, identify by metadata |
| 5 | `fs.reorganise` | medium | Move N files into directories implied by content |
| 6 | `fs.dedupe` | medium | Find duplicate contents, keep one, delete the rest |
| 7 | `fs.extract_collate` | medium | Read several files, write a combined summary file |
| 8 | `fs.conditional_move` | hard | Move only files satisfying a content predicate, amid distractors |
| 9 | `fs.multi_stage` | hard | Build an index, then act on what the index says |
| 10 | `fs.repair` | hard | Detect and fix an inconsistency between a manifest and the tree |

Tasks 8–10 are where a harness should matter: they need several dependent
observations, and a single-shot solver cannot see enough to succeed. If
`single_shot` scores near `react` on 8–10, that is early evidence about the
headline hypothesis and is worth noticing on Day 5 rather than Day 32.

**Targets are computed, not written.** Each task ships a `target_for(seed)` that
derives required end state from the same generator input. Hand-written targets
drift from generated environments; a computed target cannot.

**`max_turns` per task, not global.** `fs.read_answer` needs 3; `fs.multi_stage`
needs 12. A single global cap would either starve the hard tasks or hand the easy
ones a budget they only use to loop. Per-task ceilings also make the token
forecast tight enough to be useful.

**Rejected: scoring hard tasks on partial credit by default.** Tempting, since
binary scoring on a 10-task family is noisy. Rejected because it makes families
non-comparable in aggregate; partial credit is reported as a diagnostic
alongside, per SPEC-004.

## Acceptance criteria

- **AC-1.** All 10 tasks are registered, each with a stable `task_id`, a
  difficulty tier, a toolset, and a `max_turns`.
- **AC-2.** For every task and every seed in the fixed set, `target_for(seed)`
  is derivable and internally consistent with the generated environment.
- **AC-3.** Each task has a programmatic reference solution scoring exactly 1.0
  — the artifact SPEC-028 reuses for solvability validation.
- **AC-4.** A deliberately wrong reference solution scores exactly 0.0 for each
  task.
- **AC-5.** Difficulty tiers are structurally ordered: median reference-solution
  tool-call count is strictly increasing easy → medium → hard.
- **AC-6.** `uv run harnesslab run --task fs.reorganise --model ollama/<m>`
  produces a scored `.eval` log that opens in `inspect view`. Marked `gpu`.
- **AC-7.** **First real accuracy number**: all 10 tasks × 5 seeds against one
  model with a bare `generate()` solver, recorded in the spec's closing note with
  the model digest and date.
- **AC-8.** No task definition contains generated content — verified by a test
  asserting two different seeds yield different environment digests for every task.

## Test plan

| Level | What it covers |
|---|---|
| unit | Registry completeness and stable IDs (AC-1) |
| unit | Target derivation consistency (AC-2) |
| unit | Difficulty ordering by reference tool-call count (AC-5) |
| unit | No baked content (AC-8) |
| golden | Reference solution scores 1.0 per task (AC-3) |
| golden | Mutated reference scores 0.0 per task (AC-4) |
| integration | CLI end-to-end against local Ollama, marked `gpu` (AC-6) |

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] The AC-7 baseline number recorded here, with model digest and date
- [ ] Docs updated: `docs/TASK_FAMILIES.md` filesystem section
- [ ] Status set to `Accepted`

## Result log

> _AC-7 baseline, filled on completion. Do not fill before the run._
>
> | Model (digest) | Solver | Tasks × seeds | Accuracy | Date |
> |---|---|---|---|---|
> | | `generate()` | 10 × 5 | | |
