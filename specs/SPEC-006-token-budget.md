---
spec: 006
title: Token estimator, quota ledger, and admission control
status: Draft
depends_on: [001]
day: 6
---

# SPEC-006 — Token estimator, quota ledger, admission control

## Motivation

This is the spec that makes the project possible on free tiers, and it exists in
Week 1 because the original plan's run economics were wrong by an order of
magnitude. Two errors, both worth stating plainly because they are easy to repeat:

1. **The binding limit is tokens per day, not requests per day.** Groq's
   `llama-3.3-70b-versatile` free tier is 100K TPD. Counting requests suggests it
   is usable; counting tokens shows it supports roughly six trajectories.
2. **A ReAct trajectory resends its whole history every turn.** Eight turns is
   not eight calls' worth of tokens — with an ~800-token system-plus-tools
   preamble and ~300 tokens added per turn, cumulative usage is ~15K tokens, not
   ~2K.

Together those put the originally-planned sweep at ~16M tokens, which against
100K TPD is about 32 days for a single model's slice. The fix is not a smaller
sweep alone; it is knowing the cost **before** starting, and refusing to start a
shard that cannot finish. `../docs/TOKEN_BUDGET.md` carries the full arithmetic.

## Scope

**In scope**

- `estimate()` — pre-flight token forecast for a planned sweep.
- `Ledger` — durable per-provider, per-model, per-UTC-day consumption record.
- **Named reservations** — booking quota for non-sweep work, notably SPEC-028's
  strong-model solvability check.
- `admit()` — admission control that refuses shards it cannot finish.
- `harnesslab budget --plan <file>` reporting forecast against remaining quota.

**Out of scope**

- Retry, backoff, provider degradation — SPEC-011 consumes this module's verdicts.
- Shard scheduling across days — SPEC-022.
- Notional *money* cost — that is `pricing.py` and `../docs/COST_MODEL.md`. This
  spec counts tokens, which is a different quantity with a different purpose.

## Interface contract

```python
# src/harnesslab/budget/estimator.py
class TrajectoryEstimate(BaseModel, frozen=True):
    input_tokens: int
    output_tokens: int
    calls: int

    @property
    def total_tokens(self) -> int: ...


class SweepPlan(BaseModel, frozen=True):
    """A planned block of work: the unit the estimator forecasts and the
    admission controller admits."""
    block_id: str                 # "A1", "A3", "laneB", "solvability-check"
    model_keys: list[str]
    harness_ids: list[str]
    task_ids: list[str]
    seeds: list[int]
    context_policy: str

    @property
    def n_trajectories(self) -> int: ...


def estimate_trajectory(
    *, harness_id: str, max_turns: int, preamble_tokens: int, tokens_per_turn: int
) -> TrajectoryEstimate:
    """Forecast one trajectory.

    Models the quadratic: a harness that resends history pays the preamble on
    every call and accumulates observations, so input tokens grow with the
    square of turn count, not linearly.

        input  = calls * preamble + tokens_per_turn * calls * (calls - 1) / 2
        output = calls * output_per_turn

    Parameters are per-harness and calibrated from observed logs -- see AC-2.
    """


def estimate_plan(plan: SweepPlan) -> dict[str, TrajectoryEstimate]:
    """Forecast a plan, aggregated per model key."""
```

```python
# src/harnesslab/budget/ledger.py
class Ledger:
    """Durable consumption record, keyed (model_key, utc_date).

    Backed by the results store, so it survives process restarts and is visible
    to CI. Quota windows are provider-local; the ledger records UTC and the
    registry declares each provider's reset convention.
    """

    def record(self, *, model_key: str, input_tokens: int, output_tokens: int, calls: int) -> None: ...

    def consumed_today(self, model_key: str) -> Consumption: ...

    def remaining_today(self, model_key: str) -> Remaining:
        """Registry limits minus consumption minus outstanding reservations."""

    def reserve(self, *, name: str, model_key: str, tokens: int, calls: int) -> Reservation:
        """Book quota for non-sweep work so a sweep cannot silently eat it.

        SPEC-028's solvability check is ~850 calls against Gemini Flash-Lite's
        1,000 RPD. Without a reservation a concurrent sweep would consume the
        budget and the validation day would fail halfway through.
        """

    def release(self, reservation_id: str) -> None: ...
```

```python
# src/harnesslab/budget/scheduler.py
class Verdict(StrEnum):
    ADMIT = "admit"
    ADMIT_PARTIAL = "admit_partial"   # a prefix fits; the rest defers
    REJECT = "reject"


def admit(plan: SweepPlan, ledger: Ledger) -> AdmissionDecision:
    """Decide whether a plan can start today.

    Refuses rather than starting work that will die mid-shard: a half-finished
    block wastes the quota it consumed and leaves an unbalanced cell, which is
    worse for the analysis than not having started.
    """
```

**Invariants**

- Every model call in the project is recorded — sweeps, smoke runs, one-off
  validation. An unrecorded call is a silent quota leak and a reproducibility gap.
- `remaining_today` never returns more than the registry's declared limit minus
  recorded consumption minus live reservations.
- `admit()` is conservative: on any uncertainty it returns `REJECT`. Wasting a
  shard is more expensive than deferring one.
- Reservations are durable and expire at the provider's daily reset, never on
  process exit.

## Design notes

**The quadratic is the whole point.** A linear model of trajectory cost is what
produced the original order-of-magnitude error. Input tokens grow with the square
of the call count for any harness that resends history, so `react_reflect` at 12
turns is not 1.5× `react` at 8 — it is closer to 2.2×. The estimator must model
this or admission control is theatre.

**Estimates are calibrated, not guessed.** Initial per-harness parameters come
from measurement on Day 7, and AC-2 requires the forecast to land within ±25% of
observed. A forecast nobody has checked is worse than none, because it invites
trust.

**Reservations exist because of one concrete failure.** The solvability check on
Day 18 consumes almost a full day of Gemini Flash-Lite's request quota. Without
booking, a nightly smoke run started at 02:00 would eat it, and Day 18 would fail
at task 40 of 53. Naming the reservation puts it in the budget report where it
can be seen.

**UTC days, provider reset conventions in the registry.** Providers do not all
reset at midnight UTC. The ledger records UTC consistently and the registry
carries each provider's convention, so the mapping is one place and auditable.

**`ADMIT_PARTIAL` is not a convenience.** It lets a shard boundary land on a
complete cell rather than mid-cell, which keeps the grid balanced. A partially
completed cell is the specific shape of damage the analysis cannot repair.

**Rejected: enforcing quota by catching 429s.** That is the standard approach and
it is reactive — you learn the budget is gone by having already spent it, having
burned wall-clock, and having produced a partial cell. Forecasting first is what
makes an overnight unattended sweep trustworthy.

**Rejected: a single global token budget.** Quotas are per-model and per-provider
with different reset windows and different binding dimensions (Groq binds on TPD,
Gemini on RPD, Cerebras on RPM). A single number would have to be the minimum of
all of them and would waste most of the available capacity.

## Acceptance criteria

- **AC-1.** `estimate_trajectory` reproduces the documented quadratic exactly for
  a hand-computed case.
- **AC-2.** **Calibration**: for at least three harness/model pairs, the forecast
  is within **±25%** of tokens actually consumed, measured against real `.eval`
  logs. Marked `network`/`gpu`; the fixture logs are committed so the assertion
  itself runs offline.
- **AC-3.** `Ledger.record` is durable across process restarts and correct under
  concurrent writes from two processes.
- **AC-4.** `remaining_today` correctly subtracts a live reservation, and restores
  it on `release`.
- **AC-5.** A reservation survives a process restart and expires at the
  provider's declared reset, not at exit.
- **AC-6.** `admit()` returns `REJECT` for a plan exceeding remaining TPD, `ADMIT`
  when it fits, and `ADMIT_PARTIAL` with a **cell-aligned** prefix when only part
  fits — verified by asserting no partial cell in the admitted prefix.
- **AC-7.** With `enforce_budget=True`, a rejected plan raises before any model
  call is made — verified by a mock provider that fails the test if invoked.
- **AC-8.** `harnesslab budget --plan plans/laneA.json` prints per-model forecast,
  remaining quota, reservations, and verdict, and exits non-zero on `REJECT`.
- **AC-9.** The full Lane A and Lane B plans from `docs/EXPERIMENT_DESIGN.md`
  forecast within 10% of the trajectory and GPU-hour totals published there —
  the plan's own arithmetic is a test.

## Test plan

| Level | What it covers |
|---|---|
| unit | Quadratic against hand-computed values (AC-1) |
| unit | Reservation arithmetic and release (AC-4) |
| unit | Admission verdicts, including cell alignment (AC-6) |
| unit | Published plan totals reproduce (AC-9) |
| golden | Calibration against committed `.eval` fixtures (AC-2) |
| integration | Ledger durability and concurrent writes (AC-3, AC-5) |
| integration | Mock provider proves no call on REJECT (AC-7) |
| integration | CLI output and exit codes (AC-8) |

## Definition of done

- [ ] `make check` green
- [ ] Every AC demonstrated by a named test
- [ ] Calibration figures from AC-2 recorded in `docs/TOKEN_BUDGET.md`
- [ ] Docs updated: `docs/TOKEN_BUDGET.md`, `docs/adr/0003`
- [ ] Status set to `Accepted`
