# Token budget

**Fetched 2026-08-09. Re-verify on Day 1 — free tiers change monthly.**

This document exists because the project's original run economics were wrong by
roughly an order of magnitude, in a way that is easy to repeat. The arithmetic
here is what sizes the entire experiment, and [SPEC-006](../specs/SPEC-006-token-budget.md)
turns it into an admission controller that refuses work it cannot finish.

---

## 1. The two errors

### Error 1 — counting requests instead of tokens

The binding free-tier limit is usually **tokens per day**, not requests per day.

Groq's `llama-3.3-70b-versatile` allows **1,000 requests/day** — which sounds
generous — and **100,000 tokens/day**, which is not. Sizing by requests suggests
~125 trajectories; sizing by tokens gives **about six**.

### Error 2 — a trajectory is not one call's worth of tokens

A ReAct-style harness **resends its accumulated history on every turn**. Eight
turns is not eight calls' worth of tokens; input grows with the *square* of turn
count.

With an ~800-token system-plus-tools preamble and ~300 tokens added per turn:

```
input  = calls × preamble  +  tokens_per_turn × calls × (calls − 1) / 2
       = 8 × 800           +  300 × 8 × 7 / 2
       = 6,400             +  8,400
       ≈ 14,800 tokens

output ≈ 8 × 180 ≈ 1,400 tokens
```

**≈ 15,000 tokens per 8-turn trajectory** — not the ~2,000 a linear model
suggests.

### The consequence

The originally planned sweep (5 models × 4 harnesses × 53 tasks ≈ 1,060
trajectories) is **~16 million tokens**. Against 100K TPD, a single model's slice
takes **~32 days**.

This is why the estimator models the quadratic explicitly, and why it is a Week-1
component rather than a scheduling detail.

---

## 2. Verified free-tier capacity

| Provider / model | RPM | RPD | TPD | Ctx cap | Est. traj/day | Binds on |
|---|---|---|---|---|---|---|
| Gemini 2.5 Flash-Lite | 15 | 1,000 | — | 1M | **~125** | RPD |
| Cerebras gpt-oss-120b / GLM-4.7 | 5 | 14,400 | 1M | **8,192** | ~40 | TPD + ctx |
| Groq llama-3.1-8b-instant | 30 | 14,400 | 500K | — | ~33 | TPD |
| Gemini 2.5 Flash | 10 | 250 | — | 1M | ~31 | RPD |
| Groq llama-3.3-70b-versatile | 30 | 1,000 | **100K** | — | **~6** | TPD |
| OpenRouter `:free` | 20 | **50** | — | varies | **~6** | RPD |
| Ollama (local, RTX 4060) | ∞ | ∞ | ∞ | — | ~7.5 GPU-h/night | throughput |

Sources and fetch dates in [PROVIDERS.md](PROVIDERS.md).

**Aggregate Lane B capacity ≈ 240 trajectories/day** with providers running in
parallel. Lane B's 600 trajectories are therefore a **3–4 day sharded sweep**,
not a nightly job.

Two providers earn a caveat rather than exclusion:

- **Groq 70B** at ~6 trajectories/day and **OpenRouter** at ~6 are included for
  the model axis at low N. That N is disclosed wherever they are reported.
- **Cerebras** binds on two dimensions at once: 1M TPD is generous, but the
  **8,192-token context ceiling** is what forces the shared context policy across
  the whole pooled grid. See [EXPERIMENT_DESIGN.md §4](EXPERIMENT_DESIGN.md).

---

## 3. Lane A: GPU-hours, per model

Lane A is unlimited in quota and limited in **throughput**, so it is budgeted in
GPU-hours rather than tokens. Timing is computed per model because the three
differ by roughly 4×; an average would hide that the 12B model dominates.

| Model | VRAM @ Q4 | Fits 8 GB? | Capped traj. | Uncapped traj. |
|---|---|---|---|---|
| Qwen2.5 3B | ~2.0 GB | yes | ~0.5 min | ~0.8 min |
| Qwen2.5 7B | ~4.7 GB | yes | ~1 min | ~1.5 min |
| Gemma 3 12B | ~7.3 GB | tight | ~2 min | ~3 min |
| Qwen2.5 14B | ~9.0 GB | **no — spills** | ~8 min | — |

Uncapped trajectories cost ~1.5× the wall time of capped ones: more retained
context means more prefill on every turn.

### Block totals

| Block | Trajectories | Split | GPU-h |
|---|---|---|---|
| A1 + A2 (capped) | 1,500 | 500 per model | 4.2 + 8.3 + 16.7 = **29.2** |
| A3 (uncapped) | 600 | 300 each on 7B, 12B | 7.5 + 15.0 = **22.5** |
| | | | **≈ 51.7 GPU-h** |

At ~7.5 h/night, **≈ 7 nights**. The 12B model is ~61% of that total, which is
what the cut ladder targets.

These figures are planning estimates validated only by a Day 8 smoke test
([SPEC-010](../specs/SPEC-010-lane-a-model-gate.md)). If the 12B runs at 3 min
rather than 2, its block goes from 23 h to 34 h and the sweep from 7 nights to 9
— which is why the Day 30 checkpoint and the pre-declared cut ladder exist.

---

## 4. Named reservations

**Every model call in the project is booked**, including one-off validation.
An unrecorded call is both a quota leak and a reproducibility gap.

| Reservation | Day | Model | Calls | Why it needs booking |
|---|---|---|---|---|
| `solvability-check` | 18 | Gemini Flash-Lite | ~850 | 53 tasks × ~8 calls ≈ 424, budgeted 2× for re-runs of initial failures. Against 1,000 RPD this owns the whole day. |

Without the reservation, a nightly smoke run starting at 02:00 would consume the
quota and Day 18 would fail at task 40 of 53. Spill target: Groq
`llama-3.1-8b-instant`. Overflow: Day 17's buffer.

---

## 5. Admission control

The estimator forecasts; the ledger records; `admit()` decides.

| Verdict | Meaning |
|---|---|
| `ADMIT` | The whole plan fits in today's remaining quota. |
| `ADMIT_PARTIAL` | A cell-aligned prefix fits; the rest defers to tomorrow. |
| `REJECT` | Not enough remaining quota. **Nothing is started.** |

Two properties matter:

**Refusing beats failing halfway.** A shard that dies mid-cell has spent
irreplaceable quota and left an unbalanced cell — which is worse for the analysis
than not having started. `admit()` is conservative: on any uncertainty, `REJECT`.

**`ADMIT_PARTIAL` aligns on cell boundaries.** A partially completed cell is the
one shape of damage the analysis cannot repair, so shard boundaries never land
mid-cell.

**Rejected alternative — catching 429s.** The standard approach is reactive: you
learn the budget is gone by having already spent it, burned the wall-clock, and
produced a partial cell. Forecasting first is what makes an unattended overnight
sweep trustworthy.

---

## 6. Calibration

A forecast nobody has checked is worse than no forecast, because it invites
trust. [SPEC-006 AC-2](../specs/SPEC-006-token-budget.md) requires the estimator
to land within **±25%** of tokens actually consumed for at least three
harness/model pairs, measured against real `.eval` logs.

> _Filled on Day 7 when the first harnesses produce real logs._
>
> | Harness | Model | Forecast tokens | Actual | Error |
> |---|---|---|---|---|
> | | | | | |
