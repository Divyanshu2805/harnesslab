# ADR 0004 — Deterministic scoring; no LLM judge anywhere

**Status:** Accepted · **Date:** 2026-08-09

## Context

Inspect ships `model_graded_qa()`, and using it would make authoring the task
suite dramatically easier — open-ended tasks become scorable, and the suite could
cover far more ground.

But the experiment varies the **scaffold** while holding everything else fixed.
Judge models have documented preferences over response style: length, confidence,
structure, explicitness. A harness that produces more verbose or more assertive
output would score higher **for reasons unrelated to task success**.

That is not a small bias. It is a bias *aligned with the independent variable*.
`react_reflect` produces more deliberative text than `single_shot` almost by
construction, so a judge would systematically favour it — and "harness matters"
would be partly an artefact of the instrument.

## Decision

**No LLM judge anywhere in this project.** Not in scoring, and not in the failure
taxonomy.

- Scoring: `final_state`, `exact_match`, `refusal`, `partial_credit` — all pure
  functions of `(final state, target)`.
- Failure classification: **manual coding**
  ([SPEC-026](../../specs/SPEC-026-failure-taxonomy.md)), with intra-rater κ
  reported.
- Enforced: [SPEC-004 AC-7](../../specs/SPEC-004-scorers.md) requires two runs
  differing only in harness, with identical final state, to receive identical
  scores. [SPEC-026 AC-6](../../specs/SPEC-026-failure-taxonomy.md) asserts the
  classification module imports no provider client.

## Consequences

**Good.** The measuring instrument is indifferent to the thing being varied,
which is the precondition for the headline claim meaning anything. Scoring is
also free, instant, and reproducible — a published log can be re-scored years
later with no quota.

**Cost, and it is real.** Tasks must be constructed so correctness is decidable
from state. **No open-ended generation, no summarisation, no writing tasks.** This
excludes a large and interesting part of what agents are used for, and it is
stated in `LIMITATIONS.md` rather than elided. The benchmark is narrower than it
could be, deliberately.

**Cost.** The refusal classifier is a deterministic rule set and will have false
negatives on unusual phrasings. Accepted — and its error rate is **measured
against hand-labelled submissions and reported as a number**
([SPEC-016 AC-6](../../specs/SPEC-016-family-refusal.md)) rather than left
unknown.

## Alternatives rejected

**`model_graded_qa()` with a strong judge.** Easier and broader. Rejected because
the bias is aligned with the independent variable — see Context.

**Judge with a fixed, cheap model to reduce cost.** Does nothing about the bias;
a weaker judge has *more* style sensitivity, not less.

**Hybrid — deterministic where possible, judge for open-ended tasks.** Tempting.
Rejected because aggregate numbers would then mix two instruments with different
biases, and any harness effect could be attributed to the judge-scored subset.
Reviewers would be right to ask, and there would be no clean answer.

**LLM-assisted failure classification with human review.** Rejected: the LLM's
suggestion anchors the human coder, so the bias returns wearing a lab coat. The
coding sheets are pre-populated with metadata and **no suggested category**
([SPEC-026 AC-2](../../specs/SPEC-026-failure-taxonomy.md)).
