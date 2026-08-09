---
spec: 010
title: Lane A model gate — VRAM fit, throughput, tool-call floor
status: Draft
depends_on: [007]
day: 8
---

# SPEC-010 — Lane A model gate

> **Stub.** This is a **go/no-go gate**, not a feature. It runs on Day 8 so the
> single largest risk to the project is retired in week two rather than
> discovered during the sweep.

## Why this exists

Lane A carries the headline ablation, and it rests on three assumptions that have
not been tested: that the chosen models **fit in 8GB of VRAM**, that they run at
roughly the estimated speed, and that a 3B-class model can **tool-call reliably
enough to score above zero**. Small models are notoriously weak at tool use. If
scores floor near zero the lane measures nothing, and the failure would be
invisible until the sweep produced a flat grid.

Each assumption gets a measurement here, and the fallback ladder is pre-declared
so the decision is not made under time pressure later.

## Scope

**In scope**

- Per-model VRAM residency check on the RTX 4060 — confirm no spill into system
  RAM, which collapses throughput to CPU-like speeds.
- Per-model throughput measurement, capped and uncapped, producing the real
  numbers behind the GPU-hour estimate in `docs/EXPERIMENT_DESIGN.md`.
- A tool-calling capability floor on a trivial two-step task.
- System power draw under load, feeding the electricity basis in
  `docs/COST_MODEL.md`.
- Digest pinning for whichever models pass.

**Out of scope**

- Running the sweep. This gate decides *which models the sweep may use*.

## Candidates

| Model | VRAM @ Q4 | Expected |
|---|---|---|
| Qwen2.5 3B | ~2.0 GB | fits |
| Qwen2.5 7B | ~4.7 GB | fits |
| Gemma 3 12B | ~7.3 GB | tight — primary candidate for the top of the axis |
| Qwen2.5 14B | ~9.0 GB | **expected to spill**; measured to confirm |

## Acceptance criteria

- **AC-1.** For each candidate, VRAM residency is measured under real load and
  recorded. A model that spills is marked ineligible with its measured penalty.
- **AC-2.** Measured trajectory time per model, capped and uncapped, is within
  **2×** of the planning estimate — or the plan's GPU-hour totals are revised in
  `docs/EXPERIMENT_DESIGN.md` in the same change.
- **AC-3.** **Tool-call floor**: each selected model scores **>50%** on a trivial
  two-step tool task over 20 seeds. A model below the floor is ineligible.
- **AC-4.** The final Lane A roster spans a real capability range. A roster where
  the top and bottom differ by less than ~2× in parameters is flagged in
  `docs/LIMITATIONS.md`, because a compressed model axis makes "harness beats
  model" easy to dismiss as an artefact.
- **AC-5.** Every selected model is pinned by `sha256:` digest and quantisation
  in the provider registry.
- **AC-6.** System watts under sustained load recorded, with the measurement
  method written into `docs/COST_MODEL.md`.
- **AC-7.** The fallback ladder is exercised or explicitly marked not-needed, and
  the outcome recorded here.

## Fallback ladder, pre-declared

1. Top model **Q4 → Q3** to fit. *If applied, the model axis confounds parameter
   count with quantisation — this must be stated in `docs/LIMITATIONS.md`, not
   papered over.*
2. Cap the axis at **7–8B**, accepting a narrower model range (see AC-4).
3. Move Lane A to Groq `llama-3.1-8b-instant` (500K TPD) with fewer seeds, and
   disclose the change of substrate.

## Gate outcome

> _Filled on Day 8. The sweep does not start until this table is complete._
>
> | Model | Digest | VRAM | Capped traj. | Uncapped traj. | Tool floor | Verdict |
> |---|---|---|---|---|---|---|
> | | | | | | | |
>
> **Watts under load:** ___  **Ladder step applied:** ___
