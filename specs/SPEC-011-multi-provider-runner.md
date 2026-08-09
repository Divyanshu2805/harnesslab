---
spec: 011
title: Multi-provider runner — backoff, quota tracking, graceful degradation
status: Draft
depends_on: [001, 006]
day: 11
---

# SPEC-011 — Multi-provider runner

> **Stub.** Interface contract deferred.

## Scope

**In scope**

- Executing an admitted `SweepPlan` across providers, respecting per-provider
  concurrency derived from the registry's RPM.
- Rate-limit backoff: honour `Retry-After`, exponential backoff with jitter,
  bounded attempts.
- Ledger integration — every call recorded, including failed and retried ones.
- Graceful degradation: one provider being down does not abort the sweep; its
  shards defer and the rest proceed.
- Resume: re-running a plan skips cells already complete in the results store.

**Out of scope**

- Deciding what to run when — SPEC-022 owns scheduling and sharding.
- Admission — SPEC-006 decides; this spec obeys.

## Acceptance criteria

- **AC-1.** Concurrency per provider never exceeds the registry's RPM, verified
  against recorded call timestamps.
- **AC-2.** A 429 triggers backoff honouring `Retry-After` when present; attempts
  are bounded and the give-up is recorded, not silent.
- **AC-3.** **Retried and failed calls are recorded in the ledger.** A retry
  spends quota; not counting it is how a budget silently overruns.
- **AC-4.** A provider returning 5xx for an entire shard defers that shard and
  leaves the others unaffected — no partial-cell damage.
- **AC-5.** Re-running a partially complete plan resumes rather than duplicating,
  keyed on (task, seed, model, harness, policy).
- **AC-6.** An unattended run survives a simulated mid-sweep outage and completes
  the reachable work, exiting with a status distinguishing "complete" from
  "deferred work remains".
- **AC-7.** Cerebras is reachable through `openai-api/cerebras/*` with no LiteLLM
  in the dependency tree — verified by asserting the import is absent.
- **AC-8.** The runner never exceeds a plan's admitted scope, even if quota frees
  up mid-run; expanding scope silently would break the balanced grid.
