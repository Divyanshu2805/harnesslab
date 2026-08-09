---
spec: 022
title: CI workflows — smoke, sharded sweep, secrets, artifacts
status: Draft
depends_on: [011, 019]
day: 25
---

# SPEC-022 — CI workflows

> **Stub.**

## Scope

**In scope**

- `smoke.yml` — nightly: one harness × all models × 10 tasks. Small enough to
  fit any day's quota.
- `sweep.yml` — the sharded rolling sweep, provider matrix, resumable, with
  admission control consulted before each shard.
- `publish.yml` — rebuild site JSON and deploy Pages.
- Secret handling; artifact upload of `.eval` logs; failure notification.

**Out of scope**

- `ci.yml` (lint/types/tests) — SPEC-000.

## Design constraint

**Logs are uploaded as artifacts before the database write.** The DB write is the
step most likely to fail unattended (free-tier idle-suspend, network), and a
sweep whose results exist only in a database that rejected the write has burned
irreplaceable quota for nothing. Artifact first, ingest second, replayable.

## Acceptance criteria

- **AC-1.** Smoke runs nightly unattended and completes within its quota,
  verified over three consecutive nights.
- **AC-2.** The sweep shards by (block, model) and consults `admit()` before each
  shard; a shard that cannot finish is deferred, not started.
- **AC-3.** `.eval` logs are uploaded as artifacts **before** ingestion, and a
  simulated DB failure leaves the logs recoverable.
- **AC-4.** Secrets are available only to workflows that need them; `ci.yml`
  passes on fork PRs with none present.
- **AC-5.** No secret appears in any log line, including on failure paths.
- **AC-6.** A failed nightly notifies rather than failing silently.
- **AC-7.** Re-running a workflow resumes rather than duplicating (SPEC-011 AC-5).
- **AC-8.** Public-repo runners only — the project's $0 claim depends on it.
- **AC-9.** A sweep run records which cut-ladder step, if any, was active.
