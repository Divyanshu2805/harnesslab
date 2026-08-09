# ADR 0005 — Two first-class lanes, not one lane and a compromise

**Status:** Accepted · **Date:** 2026-08-09

## Context

Free-tier API quotas cannot support the statistical replication the headline
claim needs. An earlier framing concluded: *"we had to use local models because
quotas"* — treating local inference as a fallback forced by budget.

That framing is both weaker and less accurate than it needs to be.

*Which agent setups actually work on hardware a student owns?* is a **first-class
research question**. It is the question r/LocalLLaMA asks daily, nobody has
answered it with a controlled ablation, and it makes an RTX 4060 a **feature of
the design** rather than a limitation of the budget.

## Decision

Two lanes, each owning a question, neither subordinate:

| | **Lane A — consumer hardware** | **Lane B — free-tier APIs** |
|---|---|---|
| Question | *What works on a GPU you own?* | *What works on a free API key?* |
| Constraint | GPU throughput | Daily quota |
| Carries | Headline ablation, full harness axis, compaction ablation | Cost/Pareto claim across diverse hosted models |

They share a 20-task core suite and a 3-harness common subset, so the **pooled
primary grid is 8 models × 3 harnesses × 20 tasks**.

## Consequences

**Good — and this is the main point.** The lanes **contend for nothing**: one is
GPU-bound, the other is API-quota-bound in CI. An earlier revision scheduled them
sequentially out of habit. Running them concurrently puts the headline finding on
Day 32 rather than the last day, which is the single largest schedule
improvement in the plan.

**Good.** The leaderboard presents both side by side — *"here is what runs on
your 8 GB card, here is what runs on a free key"*. That pairing is what travels,
and it is not a consolation prize for either lane.

**Good.** Lane A's unlimited quota buys 5 seeds and the full 5-harness axis,
which Lane B could never afford.

**Cost.** Every claim must name its lane, and some claims are single-lane only
(the compaction ablation is Lane A only, because Lane B is *forced* to compact).
`METHODOLOGY.md §5` tabulates the attribution.

**Cost.** Lane A tops out near 12B at 4-bit on 8 GB, so nothing here speaks to
scaffold effects at frontier scale. Stated in `LIMITATIONS.md`.

## Alternatives rejected

**API-only, grid shrunk to fit.** ~24 tasks, 3 harnesses, N=1. No error bars, so
the headline becomes suggestive rather than evidence.

**API-only, 3–4 week rolling sweep.** Keeps the full grid, but produces one
complete sweep at the very end with no room to iterate — and every schedule risk
lands on the same day.

**Local-only.** Loses the cost/Pareto claim entirely, since local inference has
no published price, and loses model diversity.

**Local as a "control".** The original framing. Rejected: it wastes the more
legible of the two questions, and it invites the reading that the local numbers
are a fallback rather than a result.
