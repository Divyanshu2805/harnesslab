---
spec: 027
title: HuggingFace dataset release and card
status: Draft
depends_on: [019, 023]
day: 35
---

# SPEC-027 — HuggingFace dataset release

> **Stub.**

## Scope

**In scope**

- Publishing the task suite (templates + generated instances at the primary
  seeds), the result rows, and the released trajectories.
- A dataset card: provenance, generation procedure, schema, limitations, license.
- **CC-BY-4.0** for the data, separate from the code's Apache-2.0. See
  `LICENSE-DATA`.

**Out of scope**

- The leaderboard — SPEC-020.

## Acceptance criteria

- **AC-1.** Dataset published with a complete card: what it is, how it was
  generated, what each column means, known limitations.
- **AC-2.** The data license is CC-BY-4.0 and is stated in both the card and the
  repository, distinct from the code license.
- **AC-3.** The card states that rights in model-generated text are governed by
  the generating provider's terms, not by CC-BY.
- **AC-4.** Released instances regenerate exactly from the committed generator
  plus the primary seeds — a consumer can verify the data was not hand-edited.
- **AC-5.** Every result row carries its full provenance (git SHA, digest,
  policy, regime, block).
- **AC-6.** No API key, connection string, or personal data appears anywhere in
  the release — checked by an automated scan before upload.
- **AC-7.** The card links the paper, the leaderboard, and the prereg commit.
- **AC-8.** The release is versioned, so a citation resolves to exact content.
