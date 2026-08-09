---
spec: 008
title: Harnesses — plan_execute and react_retry
status: Draft
depends_on: [007]
day: 9
---

# SPEC-008 — Harnesses: `plan_execute` and `react_retry`

> **Stub.** Interface contract deferred until SPEC-007 lands.

## Scope

**In scope**

- `plan_execute`: an explicit planning turn producing a step list, then execution
  against it, with a bounded replan on step failure.
- `react_retry`: ReAct plus structured retry on tool error — the error text is
  fed back with an explicit retry instruction rather than as a bare observation.
- Both registered in the harness registry and usable by the runner.

**Out of scope**

- `react_reflect` and context compaction — SPEC-009.
- Any claim about which harness is better; that is the experiment's output.

## Acceptance criteria

- **AC-1.** Both satisfy the SPEC-007 `Harness` protocol and are drop-in.
- **AC-2.** `plan_execute` emits a machine-readable plan into the Store before
  any tool call, so plan quality is analysable separately from execution.
- **AC-3.** `plan_execute` replans at most the documented number of times; the
  bound is enforced and recorded.
- **AC-4.** `react_retry` retries only on **tool errors**, never on an
  unsatisfying-but-valid tool result — verified against a fixture where the tool
  succeeds with unhelpful output.
- **AC-5.** Retry count is bounded, recorded per sample, and counts against
  `max_turns`.
- **AC-6.** On the error-recovery family (SPEC-015), `react_retry` outperforms
  plain `react` — the harness does the thing it was built to do.
- **AC-7.** Estimator parameters calibrated for both to within ±25%.
- **AC-8.** Four harnesses now run over the same task without task-side changes.
