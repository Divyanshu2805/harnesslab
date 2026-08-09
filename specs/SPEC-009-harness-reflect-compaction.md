---
spec: 009
title: Harness react_reflect and the context-compaction policies
status: Draft
depends_on: [007]
day: 10
---

# SPEC-009 — `react_reflect` and context-compaction policies

> **Stub.** Interface contract deferred until SPEC-007 lands.

## Scope

**In scope**

- `react_reflect`: ReAct with a periodic self-critique turn that reviews progress
  before continuing.
- The three context policies as a first-class harness parameter:
  `none`, `truncate_oldest`, `compact_summary`, each with a token ceiling.
- Enforcement that a capped run never exceeds its ceiling on any call.

**Out of scope**

- Choosing which policy the experiment uses where — `docs/EXPERIMENT_DESIGN.md`
  fixes that: every pooled-grid cell runs capped at 8K, and the uncapped
  comparison is the A3 block.

## Why this spec carries unusual weight

The 8K cap exists to remove a confound: Cerebras' free tier caps context at 8,192
tokens, so if Lane B ran capped and Lane A did not, the model axis would be
confounded with context policy. But the cap creates its own risk, and it is the
sharpest one in the project — **the mechanism by which `react_reflect` and
`plan_execute` are supposed to help is carrying more context.** Cap everything and
the control may erase the very advantage being measured, producing "harness
barely matters" as an artefact of the experimenter's own design.

That is why the A3 block runs the compaction ablation crossed on the **full**
harness axis, and why a suppressed effect is pre-declared as a directional lower
bound rather than discovered afterward. See `docs/adr/0008` and
`docs/PREREGISTRATION.md`.

## Acceptance criteria

- **AC-1.** `react_reflect` satisfies the SPEC-007 protocol and is drop-in.
- **AC-2.** Every harness accepts a context policy; the policy is recorded on
  every result row.
- **AC-3.** Under an 8,192-token ceiling, no model call exceeds the ceiling for
  any harness on any task — verified by asserting over recorded per-call context
  sizes across a full smoke sweep.
- **AC-4.** `truncate_oldest` preserves the system prompt, the task statement,
  and the most recent turns; it never drops the submission instruction.
- **AC-5.** `compact_summary` is deterministic given the same history — no
  sampling in the summariser, or the compaction step itself injects variance
  into the measurement.
- **AC-6.** Context exhaustion is recorded as a distinct outcome
  (`context_exhausted`), separable from `turn_cap_exhausted` and from task
  failure. This is a first-class category in the SPEC-026 taxonomy.
- **AC-7.** The same task under `none` and under the 8K cap produces paired,
  comparable records — same task, same seed, same harness, differing only in
  policy. The A3 analysis depends on this pairing being exact.
- **AC-8.** Estimator parameters calibrated per policy; uncapped trajectories are
  forecast at their higher cost (~1.5× wall time is the planning assumption).
