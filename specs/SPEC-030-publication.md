---
spec: 030
title: Paper and blog publication pipeline
status: Draft
depends_on: [021, 025]
day: 36
---

# SPEC-030 — Publication pipeline

> **Stub.** The workstream starts **Day 15**, not Day 36 — see below.

## Two documents, not one

Same work, different readers, and neither substitutes for the other:

- **arXiv paper**, 5–6 pages, LaTeX, in `paper/`. The citable artifact.
- **Blog post**, ~1,500 words, on the Pages site. This is what gets linked on
  r/LocalLLaMA and Hacker News, and traction is a real signal that a paper alone
  does not produce.

## Day 15: arXiv endorsement

First-time arXiv submitters to `cs.LG` need an endorsement, and a
post-graduation institutional address may no longer auto-endorse. Endorsement
requests sit in inboxes for weeks, so the request goes out on **Day 15** — three
weeks of slack before submission. The MITACS supervisor at Calgary is the
natural ask.

If it does not arrive: the blog post and HuggingFace release still ship on
schedule and carry the traction, and the paper goes to **TMLR**, which requires no
endorsement.

## Scope

**In scope**

- LaTeX source and build; figures consumed as vector PDF from SPEC-021's export
  path — figures are **not** rebuilt here.
- The blog post, published to the Pages site.
- Citation plumbing: `CITATION.cff`, the prereg commit hash, the dataset DOI.

**Out of scope**

- Producing figures. SPEC-021 built both render targets on Day 24 precisely so
  this spec has none of that work.

## Acceptance criteria

- **AC-1.** `make paper` builds the PDF from committed source with no manual step.
- **AC-2.** Every figure is vector, sourced from SPEC-021's export — no
  screenshots, no rasterised charts.
- **AC-3.** Every number in the paper traces to a result row or an analysis
  output; **no number is typed by hand**. A test scans for numerals in the
  results section against the generated macro file.
- **AC-4.** The paper cites the prereg commit hash and states which pre-declared
  outcome obtained.
- **AC-5.** The paper reports the D8 suppression estimate alongside the headline,
  in the abstract, not a footnote.
- **AC-6.** Related work names HAL, AstaBench, τ-bench, AgentBench, GAIA,
  WebArena and the ReAct / Reflexion / plan-and-solve papers, and states the
  specific gap this work addresses. **No claim of novelty that overlaps HAL
  without acknowledging it.**
- **AC-7.** Limitations are stated: small local models, low N on quota-starved
  providers, single-coder intra-rater κ, deterministic-scoring task constraints,
  and any quantisation confound from SPEC-010.
- **AC-8.** The blog post is standalone — comprehensible without the paper — and
  links the leaderboard, dataset, and repo.
- **AC-9.** Neither document contains an unfilled bracket placeholder.
