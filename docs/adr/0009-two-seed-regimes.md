# ADR 0009 — Two seed regimes: fixed primary, rotating public

**Status:** Accepted · **Date:** 2026-08-09

## Context

The original plan specified rotating seeds every run so that task instances are
freshly generated and memorisation cannot help.

That is correct for a **live leaderboard** and wrong for the **primary
experiment**, because seeds are also the **replication unit for the bootstrap**.
If seeds rotate between runs, results cannot be pooled cleanly across runs and a
published interval cannot be reproduced.

One mechanism, two incompatible requirements.

## Decision

**Two regimes, recorded on every result row, never pooled.**

| Regime | Behaviour | Purpose |
|---|---|---|
| `primary` | Fixed set of 5 in `data/seeds/primary-v1.json`; committed; **immutable once the sweep starts** | Replication unit; produces the paper |
| `rotating` | Fresh per scheduled run, derived deterministically from the run date | Contamination defence for the public leaderboard |

The public leaderboard shows only `rotating`; the paper uses only `primary`.
Neither borrows from the other, and the analysis **raises rather than silently
averaging** if asked to pool across regimes
([SPEC-024 AC-5](../../specs/SPEC-024-bootstrap-core.md)).

## The distinction that goes in the paper

**The primary experiment's contamination resistance comes from the generator
being procedural — not from rotation.**

Tasks are synthesised from templates at run time and never scraped, so **no
instance existed to be memorised**. Rotation defends the *ongoing leaderboard*
against *future* contamination — a different threat on a different timescale.

A reviewer will probe this, and conflating the two would lose the exchange. The
separation makes the correct answer available.

## Consequences

**Good.** Both jobs are done properly. The paper is reproducible; the live board
stays contamination-resistant as it ages.

**Good.** Rotating seeds are **deterministic given the run date**, so a published
leaderboard entry can still be regenerated exactly — rotation does not cost
reproducibility.

**Cost.** Immutability must be enforced, not trusted:
[SPEC-023 AC-2](../../specs/SPEC-023-seed-regimes.md) fails the build if the
primary seed file changes while any `seed_regime='primary'` row exists.

**Cost.** Every row carries a regime column, and every analysis path checks it.

## Alternatives rejected

**Rotate everything** (the original plan). Breaks pooling and reproducibility of
the primary experiment.

**Fix everything.** The published leaderboard would become a fixed target that a
future model could be trained against, and the board's value decays over time.

**Rotate, but archive each run's seeds and pool afterwards.** Superficially
appealing. Each run becomes its own stratum with a different task-instance draw,
so the cluster bootstrap's resampling unit stops being well defined — and the
number of clusters, already only 20, is what limits precision.
