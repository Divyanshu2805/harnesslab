---
spec: 026
title: Failure taxonomy — manual coding protocol
status: Draft
depends_on: [019]
day: 34
---

# SPEC-026 — Failure taxonomy

> **Stub.** Owns a **dedicated day**. Coding 150 trajectories is realistically
> 6–10 hours; scheduling it as spare capacity beside a running sweep is how it
> gets done badly.

## Scope

**In scope**

- `analysis/failures.py` — stratified sampling of failed trajectories and
  generation of pre-populated coding sheets.
- The coding protocol below, and the reliability second pass.
- The category table, tabulated by model and by harness — the qualitative
  section of the paper.

**Out of scope**

- Any automated or model-assisted classification. See below; this is the point.
- Scoring. A failure category is diagnostic and never feeds a score.

## The protocol is a methodological commitment

**Classification is manual. Never by an LLM.** Using a model to classify failures
would reintroduce precisely the judge bias this project was built to avoid — and
it would do so at the exact point where the qualitative story is told. The whole
argument for deterministic scoring collapses if the failure analysis is
model-graded.

- **Sample:** 150 failed trajectories, stratified by model × harness.
- **Instrument:** `analysis/failures.py` pre-populates a coding sheet with
  trajectory metadata, so the human makes only the category judgment. This is
  what makes 150 feasible in a day.
- **Reliability:** a second pass over 50 after a **≥48 h gap**, reporting Cohen's
  κ. With a single coder this is **intra-rater** agreement, which is the honest
  ceiling — inter-rater κ requires a second person and is strictly better if one
  is available. Stated as a limitation either way.
- **Pre-declared reduction:** N = 100 if the day overruns. Decided now, not when
  tired at hour nine.

## Categories

`tool_misuse` · `premature_answer` · `loop` · `hallucinated_tool` ·
`early_give_up` · `context_exhausted` · `turn_cap_exhausted` · `fabrication`

`context_exhausted` is first-class because the 8K cap makes it a real and
expected outcome, and confusing it with a reasoning failure would misattribute
the cap's effect to the model.

## Acceptance criteria

- **AC-1.** The sample is drawn stratified by model × harness, reproducibly from
  a recorded seed.
- **AC-2.** Coding sheets are pre-populated with trajectory metadata and contain
  no suggested category.
- **AC-3.** 150 trajectories coded (or 100 under the declared reduction, with the
  reduction recorded).
- **AC-4.** Second pass over 50 completed after ≥48 h; κ computed and reported.
- **AC-5.** The report names the agreement as **intra-rater** and states the
  limitation explicitly in `docs/LIMITATIONS.md`.
- **AC-6.** **No LLM is used at any point** in classification — asserted by a test
  that the module imports no provider client.
- **AC-7.** Category counts are tabulated by model and by harness, and the
  resulting table is the qualitative section of the paper.
- **AC-8.** Coding decisions are committed as data, so the taxonomy can be
  re-derived or re-analysed by a reader.
