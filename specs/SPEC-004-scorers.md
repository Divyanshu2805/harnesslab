---
spec: 004
title: Deterministic scorers — final state, exact match, refusal
status: Draft
depends_on: [002, 003]
day: 4
---

# SPEC-004 — Deterministic scorers

## Motivation

**No LLM judge.** This is the project's central methodological commitment, and it
is why the task suite is designed the way it is. A model-graded scorer would
reintroduce exactly the bias the experiment exists to measure around: judge
models have known preferences over response style, and any harness that produces
more verbose or more confident output would score higher for reasons unrelated
to task success. The whole point of the ablation is that the only thing varying
is the scaffold, so the measuring instrument must be indifferent to it.

The cost of that commitment is that tasks must be constructed so correctness is
decidable from state. That constrains the suite — no open-ended writing tasks —
and the honest statement of that limit belongs in `../docs/LIMITATIONS.md`.
`../docs/SCORING.md` carries the full argument.

## Scope

**In scope**

- `final_state()` — compares the sample's end-of-trajectory environment against a
  target state.
- `exact_match()` — normalised comparison of a submitted answer.
- `refusal()` — scores correct rejection of an impossible task (SPEC-016).
- `partial_credit()` — graded scoring for multi-step tasks.
- The normalisation rules all of them share.

**Out of scope**

- Task definitions and their targets — the family specs.
- Aggregation, CIs, the ablation — SPEC-024, 031, 025.
- Failure classification — SPEC-026, which is manual and deliberately not a scorer.

## Interface contract

```python
# src/harnesslab/scoring/final_state.py
from inspect_ai.scorer import Score, Scorer, Target, scorer, accuracy, stderr
from inspect_ai.solver import TaskState


@scorer(metrics=[accuracy(), stderr()])
def final_state() -> Scorer:
    """Score by comparing the environment the agent left behind.

    The target is a canonical serialization of the required end state, carried
    in sample metadata. Because the Store is serialized into the .eval log, this
    scorer is a pure function of data already in the log -- a published log can
    be rescored later without rerunning any model.
    """

    async def score(state: TaskState, target: Target) -> Score:
        ...  # -> Score(value=1.0|0.0, answer=..., explanation=...)

    return score
```

```python
# src/harnesslab/scoring/partial_credit.py
@scorer(metrics=[accuracy(), stderr()])
def partial_credit(checkpoints: list[Checkpoint]) -> Scorer:
    """Fraction of independently-checkable sub-goals satisfied.

    Checkpoints are order-independent predicates over final state. Used only
    where a task has genuinely separable sub-goals; the headline metric remains
    binary task success, and partial credit is reported alongside, never
    substituted for it.
    """
```

```python
# src/harnesslab/scoring/refusal.py
@scorer(metrics=[accuracy(), stderr()])
def refusal() -> Scorer:
    """Score an impossible task.

    1.0 requires BOTH:
      - the agent submitted rather than exhausting its turn budget, and
      - the submission is classified as a refusal by a deterministic rule, and
      - the environment is unmodified (no fabricated artifact left behind).

    A run that times out is 0.0, not a refusal. Giving up silently and correctly
    declining are different behaviours and the metric must separate them.
    """
```

**Invariants**

- Every scorer is a pure function of `(TaskState, Target)`. No network, no clock,
  no RNG.
- Scoring the same log twice yields identical scores, and scoring a *published*
  log reproduces the published number exactly.
- Scorers never inspect the harness, the model, or the message history for
  anything beyond the submitted answer and the final state. This is what makes
  the instrument indifferent to the scaffold.

## Design notes

**Comparison runs over `canonical()`, never over objects.** Environment equality
is a byte comparison of the canonical serialization from SPEC-002, which makes
"equal" mean one thing everywhere and makes failures diffable.

**Normalisation is narrow and written down.** For `exact_match`: strip leading
and trailing whitespace, collapse internal runs of whitespace, casefold, and
strip a trailing period. Nothing else — no synonym matching, no numeric
tolerance, no fuzzy distance. Every additional rule is a place where a scaffold
that formats differently could gain an edge.

**Refusal requires three conditions, not one.** The interesting failure is a
model that *neither* solves *nor* declines — it loops until the turn cap. If
refusal were scored on the submission alone, a timeout would be indistinguishable
from an honest "this cannot be done". Requiring an explicit submission, a
refusal-classified answer, and an unmodified environment separates the three
behaviours. The third condition catches the specific failure of fabricating a
plausible artifact and declaring success.

**Refusal classification is a deterministic rule, not a model.** A small pattern
set over the submission, plus the structural conditions above. It will have false
negatives on unusual phrasings; that is an accepted, disclosed cost of refusing
to use a judge, and SPEC-016 measures the classifier against hand-labelled
submissions so the error rate is a reported number rather than an unknown.

**Rejected: model-graded QA.** Inspect ships `model_graded_qa()` and it would
have made the suite far easier to author. It is rejected for the reason in the
motivation, and the rejection is the contribution.

**Rejected: partial credit as the headline metric.** It reduces variance and is
tempting for a small suite. It also makes cross-family aggregation
incomparable, because "one third of a filesystem task" and "one third of a SQL
task" are not the same quantity. Binary success is the headline; partial credit
is diagnostic.

## Acceptance criteria

- **AC-1.** A hand-authored known-good trajectory for each task family scores
  exactly 1.0.
- **AC-2.** A known-broken trajectory (correct actions, one wrong final write)
  scores exactly 0.0.
- **AC-3.** Rescoring a committed `.eval` log fixture reproduces its recorded
  scores byte-for-byte.
- **AC-4.** Scorers are pure — verified under the I/O-forbidding fixture.
- **AC-5.** `exact_match` applies exactly the documented normalisations and no
  others, verified against a table including case, whitespace, trailing period,
  and Unicode near-equivalents that must **not** match.
- **AC-6.** `refusal()` returns 0.0 for a turn-cap exhaustion, 0.0 for a
  fabricated artifact plus a refusal-shaped answer, and 1.0 only when all three
  conditions hold.
- **AC-7.** Two runs differing only in harness, with identical final state,
  receive identical scores — the instrument is scaffold-indifferent.
- **AC-8.** `partial_credit` is order-independent: checkpoints satisfied in any
  sequence give the same score.

## Test plan

| Level | What it covers |
|---|---|
| golden | Known-good and known-broken trajectories per family (AC-1, AC-2) |
| golden | Committed `.eval` fixture rescoring (AC-3) |
| unit | Purity fixture (AC-4) |
| unit | Normalisation table, including must-not-match cases (AC-5) |
| unit | Refusal three-condition matrix (AC-6) |
| unit | Scaffold indifference (AC-7); checkpoint commutativity (AC-8) |

The golden trajectories authored here are reused as SPEC-028's programmatic
reference solutions — the same artifact proves "the scorer works" and "the task
is solvable", which is why AC-1 is worth the authoring effort.

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] Docs updated: `docs/SCORING.md`, `docs/adr/0004`
- [ ] Status set to `Accepted`
