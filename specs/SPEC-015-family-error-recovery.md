---
spec: 015
title: Task family 5 — error recovery
status: Draft
depends_on: [003, 004]
day: 15
---

# SPEC-015 — Task family 5: error recovery

> **Stub.** Day 15 also carries the **arXiv endorsement request** — see
> `docs/PUBLICATION.md`. It is on this day because endorsement requests sit in
> inboxes for weeks and the submission is three weeks out.

## Scope

**In scope**

- ~7 tasks built on family-1 and family-3 shapes, wrapped with `faulty()` so a
  specific tool call fails deterministically once.
- Variants: fail-first-call, fail-mid-trajectory, fail-twice.
- Metadata recording which call was made to fail, so recovery behaviour can be
  located precisely in the trajectory.

**Out of scope**

- Randomised failure. Deterministic fail-on-Nth-call only — random failure would
  inject variance into the exact quantity being measured.

## Why this family exists

It is the family `react_retry` was built for, and therefore the family that can
falsify it. If structured retry does not beat plain `react` here, the harness
does not do what it claims — and that is a reportable result, not a bug to be
tuned away.

## Acceptance criteria

- **AC-1.** All tasks registered with stable IDs, failure schedule, `max_turns`.
- **AC-2.** Failures are deterministic and identical across models and harnesses
  — same call index, same error bytes.
- **AC-3.** Every task remains solvable after the injected failure; the reference
  solution recovers and scores 1.0.
- **AC-4.** A reference solution that does *not* retry scores 0.0 — the failure
  is genuinely load-bearing.
- **AC-5.** Retry attempts count against `max_turns`, so recovery is not free.
- **AC-6.** The trajectory records whether recovery was attempted and whether it
  succeeded, as structured data rather than only in prose.
