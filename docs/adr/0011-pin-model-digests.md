# ADR 0011 — Pin Ollama digests, never tags

**Status:** Accepted · **Date:** 2026-08-09

## Context

Ollama model tags are **mutable**. `qwen2.5:7b` points at whatever the registry
currently serves for that name: requantisations, updated base weights, changed
default context length, revised chat templates.

The paper claims every result is reproducible. If Lane A results record a tag,
then six months from now `ollama/qwen2.5:7b` may not be the weights that produced
the numbers, and **the claim is false without anything visibly having changed**.

The failure is silent. Nothing errors; the numbers simply stop being
reproducible, and a reader attempting replication gets different results with no
way to tell why.

## Decision

Every Lane A model records its **`sha256:` digest and quantisation level** in the
provider registry and on **every result row**.

Enforced structurally rather than by discipline:
[SPEC-001 AC-2](../../specs/SPEC-001-provider-registry.md) makes a Lane A model
with `in_pooled_grid=True` and a null digest a **validation error**, and
[SPEC-018 AC-3](../../specs/SPEC-018-results-schema.md) enforces non-null at the
database constraint level.

The digest recorded is the one **resolved at run time**, not looked up at ingest
([SPEC-019 AC-7](../../specs/SPEC-019-ingest.md)) — the digest that ran is the
digest recorded.

## Consequences

**Good.** Lane A results are reproducible in the same sense Lane B results are:
an exact model identity, not an address that resolves to something.

**Good.** Quantisation is captured alongside, which matters more than it might
seem. If the top model has to drop from Q4 to Q3 to fit in 8 GB
([SPEC-010](../../specs/SPEC-010-lane-a-model-gate.md) fallback ladder), the
**model axis confounds parameter count with quantisation**. Recording the level
per row is what makes that confound visible and reportable in `LIMITATIONS.md`
rather than invisible.

**Cost.** Digest resolution requires a running Ollama server, so it is a `gpu`
-marked step rather than pure configuration.

**Cost.** Reproducing a Lane A result requires obtaining that exact digest, which
may no longer be the registry default. The dataset card documents the digests so
a replicator knows precisely what to fetch.

## Alternatives rejected

**Record the tag.** The default, and silently wrong. This ADR exists because that
is the easy thing to do.

**Record tag plus a run date and hope the registry is auditable.** Depends on a
third party maintaining history they never promised.

**Vendor the model weights.** Genuinely reproducible and completely impractical —
multi-gigabyte binaries per model, in a repository.

**Hash the weights ourselves.** The digest already is that hash, computed by the
tool that fetched them.
