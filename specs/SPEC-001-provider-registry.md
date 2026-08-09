---
spec: 001
title: Provider registry, quota limits, and capability probe
status: Accepted
depends_on: [000]
day: 1
---

# SPEC-001 — Provider registry, quota limits, and capability probe

## Motivation

Two facts drive this spec.

First, **free tiers are the experiment's binding constraint**, and they move. A
quota table written from memory is wrong within a month. The registry therefore
holds quotas as *data with fetch dates*, and a script re-verifies them against
the live APIs and fails loudly on drift. That table is also a genuine standalone
contribution — nobody maintains a current, sourced comparison of free-tier agent
quotas, and `docs/PROVIDERS.md` is generated from this registry.

Second, **model identity must be precise enough to reproduce**. For hosted models
that means the provider's model string. For Ollama it means the **digest**, not
the tag: tags move, and `qwen2.5:7b` in six months will not be the weights that
produced these numbers. See `../docs/adr/0011`.

## Scope

**In scope**

- `ModelSpec` — the canonical description of a model on the board.
- `QuotaLimits` — declarative RPM / RPD / TPM / TPD / context ceiling.
- The registry itself: the eight models of the pooled grid plus candidates.
- `scripts/verify_providers.py` — probes live limits, regenerates
  `docs/PROVIDERS.md`, exits non-zero on drift.
- Ollama digest resolution.

**Out of scope**

- Consuming quota or enforcing it — SPEC-006 owns the ledger and admission
  control. This spec only *describes* limits.
- Retry and backoff behaviour — SPEC-011.
- Notional pricing values — the loader lives here, the methodology in
  `../docs/COST_MODEL.md`, and the numbers in `data/pricing/`.

## Interface contract

```python
# src/harnesslab/providers/limits.py
from pydantic import BaseModel, Field


class QuotaLimits(BaseModel, frozen=True):
    """A provider's free-tier ceiling for one model.

    None means "not published" or "not binding", which is not the same as
    unlimited -- the estimator treats None as unconstrained and every other
    field as hard.
    """

    requests_per_minute: int | None = None
    requests_per_day: int | None = None
    tokens_per_minute: int | None = None
    tokens_per_day: int | None = None

    # The free tier's context ceiling, which may be far below the model's
    # architectural limit. Cerebras publishes 8,192 on a model whose real
    # window is much larger; this is what forces the shared context policy.
    context_ceiling: int | None = None

    source_url: str
    fetched: str  # ISO date, e.g. "2026-08-09"
```

```python
# src/harnesslab/providers/registry.py
from enum import StrEnum
from pydantic import BaseModel


class Lane(StrEnum):
    LOCAL = "A"   # consumer hardware, Ollama on the RTX 4060
    API = "B"     # free-tier hosted APIs


class ModelSpec(BaseModel, frozen=True):
    key: str                 # stable short id used in results, e.g. "gemini-flash-lite"
    inspect_model: str       # what Inspect is handed, e.g. "google/gemini-2.5-flash-lite"
    lane: Lane
    display_name: str
    param_count_b: float | None      # billions; None for undisclosed hosted models
    limits: QuotaLimits

    # Lane A reproducibility. Empty for hosted models.
    ollama_digest: str | None = None      # sha256:... -- pinned, never a tag
    quantization: str | None = None       # e.g. "Q4_K_M"

    supports_tools: bool = True
    in_pooled_grid: bool = False          # part of the 8-model primary grid


def registry() -> dict[str, ModelSpec]:
    """All known models, keyed by ModelSpec.key."""

def pooled_grid() -> list[ModelSpec]:
    """The eight models of the primary grid, in a stable order."""

def by_lane(lane: Lane) -> list[ModelSpec]: ...
```

**Invariants**

- `key` is stable forever. It is written into every result row; changing one
  orphans historical data.
- Every Lane A model in the pooled grid has a non-null `ollama_digest` and
  `quantization`. Enforced by a validator, not by convention.
- `QuotaLimits.fetched` is never hand-edited. It is written by
  `verify_providers.py`.

## Design notes

**Cerebras rides `openai-api/`.** Inspect has no native Cerebras provider, but
Cerebras exposes an OpenAI-compatible endpoint, so `inspect_model` is
`openai-api/cerebras/<model>` with `CEREBRAS_API_KEY` and `CEREBRAS_BASE_URL`.
This is why the project has no LiteLLM dependency — see `../docs/adr/0001`.

**Quotas are data, not constants in code.** They carry a source URL and a fetch
date because they are *claims about the world* that expire. The same discipline
applies to pricing.

**`None` is not "unlimited".** A provider that does not publish a TPD is not
promising one does not exist. The estimator treats `None` as unconstrained for
planning while the ledger still records actual consumption, so a silent ceiling
shows up as an anomaly rather than as a crash.

**Rejected: deriving model identity from the Inspect model string alone.** Two
runs of `ollama/qwen2.5:7b` three months apart can be different weights. The
digest is the identity; the string is an address.

## Acceptance criteria

- **AC-1.** `registry()` returns every model referenced by the experimental
  design, and `pooled_grid()` returns exactly eight in a deterministic order.
- **AC-2.** *(Amended day 1 — see below.)* Constructing a Lane A `ModelSpec` with
  `gate=PASSED` and a null `ollama_digest` raises a validation error.
- **AC-3.** Every `QuotaLimits` in the registry carries a non-empty `source_url`
  and an ISO-8601 `fetched` date.
- **AC-4.** `verify_providers.py --check` probes each provider, compares observed
  limits against the registry, and exits non-zero when any differ. Marked
  `network`.
- **AC-5.** `verify_providers.py --write-docs` regenerates `docs/PROVIDERS.md`
  with a table matching the registry, each row carrying its fetch date and source.
- **AC-6.** Ollama digest resolution turns a tag into a `sha256:` digest against a
  running local server. Marked `gpu`.
- **AC-7.** Every model string in the registry is accepted by Inspect's model
  parser without a network call.

## Test plan

| Level | What it covers |
|---|---|
| unit | Registry completeness and stable ordering (AC-1) |
| unit | Digest validator rejects an unpinned Lane A grid model (AC-2) |
| unit | Every entry has source + fetch date (AC-3) |
| unit | Inspect parses every model string offline (AC-7) |
| integration | `--write-docs` output matches a golden fixture (AC-5) |
| integration | Live probe, marked `network` (AC-4) |
| integration | Digest resolution, marked `gpu` (AC-6) |

## Definition of done

- [x] `make check` green
- [x] Every AC demonstrated by a named test
- [x] Docs updated: `docs/PROVIDERS.md` generated from live probes
- [x] Status set to `Accepted`

---

## Day 1 outcome

### Amendment to AC-2 — validation keys on gate status, not grid membership

As written, AC-2 was unsatisfiable. It required a Lane A model in the pooled
grid to carry a digest, but **no digest exists until SPEC-010 resolves one on
day 8** — so either the registry could not declare its intended local models, or
`pooled_grid()` could not return eight.

Resolved with a `GateStatus` enum (`PENDING` / `PASSED` / `REJECTED`). The
registry declares *intent*; the validator fires on `PASSED`, which is the point
at which a model becomes usable in a scored run. `assert_sweep_ready()` refuses
to start any sweep while a pooled model is still `PENDING`.

The invariant is unchanged — an unpinned model can never produce a published
number — but it is now enforced where it is actually checkable.

### Probe findings

| Model | Result |
|---|---|
| `groq-llama-8b` | Live-verified. 14,400 RPD, **6,000 TPM** — matches the registry. |
| `groq-llama-70b` | Live-verified. 1,000 RPD, 12,000 TPM — matches. |
| `mistral-small` | Live-verified **50 RPM / 50,000 TPM**. The provisional figures carried into day 1 (1 RPM / 500 RPD) were wrong by a wide margin. **Promoted into the pooled grid.** |
| `openrouter-free` | Reachable. `is_free_tier: true`, so the 50 req/day tier. Its `rate_limit` field returns `-1` and is documented as deprecated. |
| `cerebras-gpt-oss-120b` | **HTTP 402 — "Payment required to access this resource."** `/models` lists the catalogue; inference is refused. **Withdrawn from the pooled grid.** |
| Gemini | Not probeable — limits are published only in AI Studio. Figures trusted from source, not confirmed. |
| Ollama | Server up, **no models pulled**. Needed before day 8. |

The pooled grid stays at eight: Mistral Small replaces Cerebras.

### The finding that reaches beyond this spec

**Cerebras' 8,192-token free context ceiling was the stated justification for
capping every cell in the pooled grid ([adr/0008](../docs/adr/0008-shared-context-policy.md)).
That premise no longer holds.**

With Cerebras gone, the tightest context ceiling in the grid is 32,768. Nothing
now *forces* an 8K shared policy.

The new binding constraint is **Groq's 6,000 TPM**, confirmed empirically: a
request at ~7K tokens returned `429 ... on tokens per minute (TPM): Limit 6000`.
That is tighter than the ceiling it replaces, but it is a **rate limit, not a
per-request cap** — it throttles throughput rather than truncating history, so it
does not justify the same design in the same way.

`adr/0008` needs amending before any sweep runs. Two tests now guard the live
premise rather than a constant: `test_no_provider_now_forces_an_8k_context_cap`
and `test_groq_tpm_is_the_new_binding_constraint`.
