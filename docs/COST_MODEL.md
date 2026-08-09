# Cost model

The headline chart is accuracy versus cost. That chart cannot be drawn without a
defensible cost figure for **both** lanes — and Lane A models have no published
per-token price, because nothing is being sold.

This document fixes how cost is computed, and is explicit about the one thing
that matters most: **the two lanes use different cost bases, and they are not
equivalent.**

---

## 1. Notional cost, and why it is the right idea

The project spends $0. Every model call is on a free tier or on local hardware.
So no real money is measured — and measuring real money was never the point.

**Notional cost** is what the same work *would* cost at published rates. Log the
input and output tokens actually consumed, multiply by the model's published paid
per-token price, and you get a number with real economic meaning produced by an
execution that cost nothing.

This is what makes free-tier benchmarking meaningful rather than a curiosity: the
accuracy is real, the token counts are real, and the price is the vendor's own.

Prices move, so the pricing table is **versioned in git with a fetch date**, and
[SPEC-019 AC-4](../specs/SPEC-019-ingest.md) requires cost to be computed from
the table **in force on the run's date** — not whatever is current at ingest.
Otherwise re-ingesting old logs silently rewrites history.

---

## 2. Lane B — published per-token pricing

```
notional_cost = input_tokens  × price_per_input_token
              + output_tokens × price_per_output_token
```

Source: each provider's public pricing page for the **paid** tier of the same
model. Stored in `data/pricing/pricing-<date>.json` with source URL and fetch
date per model.

---

## 3. Lane A — GPU-hour rental equivalent

Local inference has no per-token price, so cost is derived from **time on
hardware**.

### Primary basis

```
cost_per_trajectory = spot_rate_per_hour ÷ measured_trajectories_per_hour
```

- `spot_rate_per_hour` — a market rate for comparable-class consumer GPU
  capacity, recorded with source and date in
  `data/pricing/gpu-rental-<date>.json`.
- `measured_trajectories_per_hour` — **measured, not estimated**, per model, from
  [SPEC-010](../specs/SPEC-010-lane-a-model-gate.md) and confirmed against real
  sweep wall-times.

Per-model measurement matters: the three Lane A models differ by ~4× in
throughput, so a single blended rate would misprice two of them.

### Secondary basis — electricity

```
cost_per_trajectory = (system_watts ÷ 1000) × hours_per_trajectory × tariff
```

System draw under sustained load is measured on Day 8 (~200 W estimated for this
machine). This is a **lower bound** and is reported as its own series — **never
blended** with the rental figure, because they answer different questions.

---

## 4. The two bases are not equivalent

**This is stated on the chart itself, not in a footnote.** It is a correctness
requirement — see [SPEC-021 AC-3](../specs/SPEC-021-charts.md).

| | API per-token price | GPU-hour rental |
|---|---|---|
| Includes provider margin | yes | partly (rental margin) |
| Includes serving infrastructure | yes | yes |
| Includes model training amortisation | yes | **no** |
| Includes hardware amortisation | indirectly | yes |
| Includes the operator's time | no | no |

An API price is a *retail* price for a service that includes the cost of having
trained the model. A GPU-hour rate is a *wholesale* price for compute, on weights
someone else paid to train and released.

So cross-lane cost comparison is **indicative, not equivalent**. It supports
statements like *"this configuration reaches X% of that one's accuracy at roughly
an order of magnitude less cost"*. It does not support precise ratios, and the
paper will not make any.

---

## 5. Cost per solved task

Both bases are also reported normalised by success:

```
cost_per_solved_task = total_notional_cost ÷ tasks_solved
```

This is the number a practitioner actually decides on. It is also the one that
punishes an expensive harness that fails often — a configuration can look cheap
per trajectory and be ruinous per result, and cost-per-trajectory alone hides
that completely.

A configuration solving nothing has undefined cost per solved task; it is
reported as such rather than as infinity or omitted.

---

## 6. What is deliberately not counted

- **Failed and retried calls are counted.** A retry spends real tokens. Excluding
  them would flatter harnesses that retry a lot — which is exactly the design
  dimension under study.
- **The operator's time is not counted**, in either lane. It would dominate and
  is not comparable across lanes.
- **Free-tier prices are never used as the price.** The price is always the
  vendor's paid rate for the same model; using $0 would make the entire chart
  degenerate.

---

## 7. Pricing tables

| File | Contents | Refreshed by |
|---|---|---|
| `data/pricing/pricing-<date>.json` | Per-model input/output token prices, source URL, fetch date | `make pricing` |
| `data/pricing/gpu-rental-<date>.json` | Spot rate for comparable GPU class, source, date; electricity tariff and measured system watts | `make pricing`, plus SPEC-010 measurements |

Both are committed. Reproducing a published number six months from now means
reproducing the prices that produced it.

> _Filled on Day 1 (API pricing) and Day 8 (GPU rental + watts)._
>
> | Basis | Value | Source | Fetched |
> |---|---|---|---|
> | GPU spot rate | | | |
> | Electricity tariff | | | |
> | Measured system watts | | (SPEC-010) | |
