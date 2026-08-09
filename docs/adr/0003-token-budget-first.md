# ADR 0003 — Token budget as a Week-1 component, with admission control

**Status:** Accepted · **Date:** 2026-08-09

## Context

The original plan handled run economics on Day 17, sizing the sweep at
"5,000–15,000 LLM calls" and proposing a nightly smoke suite plus a weekly full
sweep.

Two errors in that sizing, both easy to repeat:

1. **The binding free-tier limit is tokens per day, not requests per day.** Groq's
   `llama-3.3-70b-versatile` allows 1,000 requests/day and **100K tokens/day**.
   Counting requests suggests ~125 trajectories; counting tokens gives ~6.
2. **A ReAct trajectory resends its history every turn.** Input grows with the
   *square* of turn count. Eight turns costs ~15K tokens, not ~2K.

Together: the planned sweep was **~16M tokens**, and a single model's slice would
have taken ~32 days. The plan was off by roughly an order of magnitude, and the
error would have surfaced as an unexplained sweep failure in Week 3.

## Decision

The token **estimator + ledger + admission controller** is
[SPEC-006](../../specs/SPEC-006-token-budget.md), built on **Day 6**.

- The estimator models the quadratic explicitly.
- The ledger durably records **every** model call, including retries, failures,
  and one-off validation runs.
- `admit()` refuses to start a shard that cannot finish, and partial admission
  aligns on **cell boundaries**.

## Consequences

**Good.** An unattended overnight sweep on free quota becomes trustworthy. Quota
is planned rather than discovered. Named reservations let non-sweep work (the
Day 18 solvability check, ~850 calls against a 1,000 RPD ceiling) be booked so a
nightly job cannot eat it.

**Good, unexpectedly.** The estimator became a *test of the plan*:
[SPEC-006 AC-9](../../specs/SPEC-006-token-budget.md) requires it to reproduce
the published sweep totals within 10%. The plan's own arithmetic is now
executable.

**Cost.** A day in Week 1, plus per-harness calibration whenever a harness lands.
The ±25% calibration requirement (AC-2) is real work — but a forecast nobody has
checked is worse than none, because it invites trust.

## Alternatives rejected

**Catch 429s and back off.** The standard approach, and reactive: you learn the
budget is gone by having already spent it, burned the wall-clock, and produced a
**partial cell** — the one shape of damage the analysis cannot repair.

**A single global token budget.** Quotas are per-model with different reset
windows and different binding dimensions (Groq binds on TPD, Gemini on RPD,
Cerebras on RPM and context). A single number would have to be the minimum across
all of them and would waste most available capacity.

**Estimate linearly and add a safety factor.** The error is quadratic in turn
count, so no constant factor is safe across harnesses — `react_reflect` at 12
turns is ~2.2× `react` at 8, not 1.5×.
