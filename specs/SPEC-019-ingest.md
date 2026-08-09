---
spec: 019
title: Ingest — Inspect samples_df() to normalized rows
status: Draft
depends_on: [018]
day: 22
---

# SPEC-019 — Ingest

> **Stub.** Day 22 also carries the **committing of `docs/PREREGISTRATION.md`**,
> which must be timestamped before any sweep data exists.

## Scope

**In scope**

- Reading `.eval` logs via Inspect's `samples_df()` and mapping to result rows.
- Deriving notional cost from tokens via the versioned pricing tables.
- Idempotent, resumable ingestion of a log directory.
- `harnesslab ingest --logs <dir>`.

**Out of scope**

- A bespoke telemetry layer. Inspect's dataframe API already yields per-sample
  token usage, timing, scores and errors; reimplementing that would be work with
  a second source of truth as its only output.

## Acceptance criteria

- **AC-1.** A committed `.eval` fixture ingests to an expected set of rows,
  compared field by field.
- **AC-2.** Ingesting the same directory twice produces no duplicates (SPEC-018
  AC-5) and no changed values.
- **AC-3.** Token counts in rows match the log's recorded model usage exactly —
  no re-estimation at ingest.
- **AC-4.** Notional cost is computed from the pricing table matching the run's
  date, not from whatever table is current at ingest time. Prices move; a
  reproducible number must use the price that was in force.
- **AC-5.** A log missing a required field fails loudly with the sample
  identified, rather than inserting a null.
- **AC-6.** Ingest is resumable: interrupting mid-directory and rerunning
  completes without duplication.
- **AC-7.** Lane A rows carry the model digest resolved from the run, not looked
  up at ingest time — the digest that ran is the digest recorded.
