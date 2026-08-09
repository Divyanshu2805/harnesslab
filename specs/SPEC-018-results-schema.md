---
spec: 018
title: Results schema, Postgres store, migrations
status: Draft
depends_on: [000]
day: 21
---

# SPEC-018 — Results schema and Postgres store

> **Stub.**

## Scope

**In scope**

- The normalized result row and its Pydantic model.
- Postgres (Neon/Supabase) as source of truth; SQLite behind the same repository
  interface for local dev and fork-PR CI, which cannot read secrets.
- Versioned SQL migrations — plain files, no ORM migration framework.
- Connect-retry handling for free-tier idle-suspend.

**Out of scope**

- Reading `.eval` logs — SPEC-019.
- Analysis queries — SPEC-024, 031.

## The row

Every row must answer "what exactly produced this number?":

| Column | Why it is here |
|---|---|
| `task_id`, `seed`, `model_key`, `harness_id` | the cell |
| `context_policy` | the D8 control; without it capped and uncapped runs are indistinguishable |
| `block_id` | A1 / A2 / A3 / laneB — which analysis a row belongs to |
| `seed_regime` | `primary` (fixed) or `rotating` (public leaderboard) |
| `model_digest`, `quantization` | Lane A reproducibility; tags move, digests do not |
| `score`, `outcome` | success plus the distinct failure kind |
| `input_tokens`, `output_tokens`, `calls` | the cost basis |
| `wall_seconds` | throughput, and the GPU-hour cost model |
| `git_sha` | the code that produced it |
| `started_at` | provenance |

## Acceptance criteria

- **AC-1.** Schema created by a migration; the migration is idempotent.
- **AC-2.** Both backends satisfy the same repository interface and pass the same
  contract test suite.
- **AC-3.** Every row carries a non-null `git_sha`, `seed`, `model_digest` (Lane
  A), `context_policy`, `block_id`, and `seed_regime`. Enforced by constraints,
  not convention.
- **AC-4.** Idle-suspend is survived: a connection to a suspended instance
  retries with backoff and succeeds, verified against a simulated cold start.
- **AC-5.** `(task_id, seed, model_key, harness_id, context_policy, seed_regime)`
  is unique — re-ingesting the same log is idempotent, not duplicating.
- **AC-6.** CI on a fork PR runs the full contract suite against SQLite with no
  secrets present.
- **AC-7.** A row can be traced back to the exact `.eval` log that produced it.
