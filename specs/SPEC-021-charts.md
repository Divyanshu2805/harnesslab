---
spec: 021
title: Charts and the vector-PDF export pipeline
status: Draft
depends_on: [020]
day: 24
---

# SPEC-021 — Charts and dual-target figure export

> **Stub. PROTECTED SCOPE** — see SPEC-020.

## Scope

**In scope**

- Four chart families:
  1. **Accuracy vs notional cost** — the Pareto frontier, both lanes, with the
     two cost bases distinguished.
  2. **Harness delta** — per model, accuracy by harness, the headline visual.
  3. **Per-family breakdown**.
  4. **Compaction effect** — capped vs uncapped, from block A3.
- **One chart definition, two render targets**: JSON for the client-side web
  charts, vector PDF for the paper.
- Client-side filtering by lane, family, difficulty.

**Out of scope**

- The statistics behind the numbers — SPEC-024, 031.

## Why the dual target is in this spec and not the endgame

Rebuilding figures for the paper at the end is the classic way a deadline slips,
and figures redone under pressure diverge from the web version they were supposed
to match. Building both outputs from one definition on Day 24 costs a little more
now and removes an entire endgame task.

## Acceptance criteria

- **AC-1.** Every chart renders from JSON with no external network requests —
  no CDN, no remote fonts.
- **AC-2.** The same definition exports a vector PDF whose data matches the web
  chart exactly, verified by comparing the underlying series.
- **AC-3.** The Pareto chart **states on the chart itself** that Lane A and Lane
  B costs use different bases and are indicative, not equivalent. This is a
  correctness requirement, not styling — see `docs/COST_MODEL.md`.
- **AC-4.** Error bars appear on every accuracy figure once CIs exist; before
  then the chart shows N and marks intervals as pending rather than implying
  precision it does not have.
- **AC-5.** Charts are legible in greyscale and do not encode meaning by colour
  alone.
- **AC-6.** Charts render correctly with partial data — a lane still sweeping
  must not break the page.
- **AC-7.** PDF output is true vector, not a rasterised image.
- **AC-8.** Wide charts scroll within their own container; the page body never
  scrolls horizontally.
