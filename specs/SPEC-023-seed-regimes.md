---
spec: 023
title: Dual seed regimes — fixed primary and rotating public
status: Draft
depends_on: [002, 022]
day: 25
---

# SPEC-023 — Dual seed regimes

> **Stub.**

## Why there are two regimes

Seeds do two unrelated jobs, and conflating them breaks one of them.

- As the **replication unit** for the bootstrap, seeds must be **fixed**. If they
  rotate between runs, results cannot be pooled cleanly across runs and the
  primary experiment cannot be reproduced.
- As a **contamination defence** for the ongoing public leaderboard, seeds must
  **rotate**, so a model trained on scraped leaderboard content gains nothing.

Hence: `primary` (fixed, versioned, immutable) and `rotating` (fresh per run).
Both regimes are recorded on every row, and analyses never mix them.

A point that goes in the paper because a reviewer will probe it: **the
contamination argument rests on the generator being procedural**, not on
rotation. Tasks are synthesised from templates and never scraped. Rotation
defends the live leaderboard against *future* contamination; it is not what makes
the primary experiment sound. See `docs/CONTAMINATION.md`.

## Scope

**In scope**

- `data/seeds/primary-v1.json` — 5 seeds, committed, immutable once the primary
  sweep starts.
- Rotation for scheduled public runs, derived deterministically from run date so
  a published leaderboard entry remains reproducible.
- `seed_regime` recorded on every result row.

## Acceptance criteria

- **AC-1.** The primary seed set is committed and version-tagged.
- **AC-2.** **Immutability is enforced**: a test fails if the file changes once
  any `seed_regime='primary'` row exists.
- **AC-3.** Rotating seeds are deterministic given the run date — a leaderboard
  entry can be regenerated exactly.
- **AC-4.** Rotating seeds never collide with the primary set.
- **AC-5.** Every row records its regime; analysis code refuses to pool across
  regimes, raising rather than silently averaging.
- **AC-6.** The public leaderboard displays only rotating-regime results, and the
  paper uses only primary — neither borrows from the other.
