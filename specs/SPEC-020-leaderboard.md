---
spec: 020
title: Static leaderboard generator and Pages deploy
status: Draft
depends_on: [019]
day: 23
---

# SPEC-020 — Leaderboard generator and Pages deploy

> **Stub. PROTECTED SCOPE** — see below.

## Why this is protected

The leaderboard is the artifact that carries the work to readers. A paper alone
does not produce traction, and traction is a real signal. Under schedule
pressure the instinct is to cut presentation in favour of analysis; that instinct
is wrong here and is structurally prevented rather than merely discouraged:

- It ships **Day 23, on smoke data**, before any sweep starts.
- It depends **only on the ingest layer**, so nothing upstream can block it.
- The release valve under pressure is **task count**, never this spec. Falling
  back from 53 tasks to the core 20 costs per-family breakdown detail and costs
  the headline finding nothing.

## Scope

**In scope**

- A build step turning result rows into static JSON.
- A static site — no backend, no server-side rendering, no request-path model
  calls. The expensive path is structurally unreachable from the internet.
- Two-lane presentation: "what runs on your 8GB card" beside "what runs on a free
  API key", which is the pairing that actually travels.
- Deploy to GitHub Pages.

**Out of scope**

- Charts — SPEC-021.
- Any dynamic query. A visitor triggering computation is the architecture this
  project exists to avoid.

## Acceptance criteria

- **AC-1.** The build produces static JSON from the results store with no
  network dependency at serve time.
- **AC-2.** The published site makes **zero LLM calls** on any code path —
  asserted by a test scanning built output for provider endpoints and keys.
- **AC-3.** The site renders correctly with smoke-only data, including empty
  states — it must be presentable before the sweeps exist.
- **AC-4.** Both lanes are presented side by side with their distinct questions
  named, not merged into one ranking.
- **AC-5.** Every number displayed carries its N and its lane attribution.
- **AC-6.** Deploys to Pages from CI; the URL is live and reachable.
- **AC-7.** The site is readable on mobile and does not scroll horizontally.
- **AC-8.** No secret, key, or connection string appears in built output.
