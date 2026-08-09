"""The model catalogue.

Two properties matter more than completeness.

**Stable keys.** `ModelSpec.key` is written into every result row. Changing one
orphans historical data, so keys are permanent even if a model is retired.

**Precise identity.** For hosted models the provider's model string is enough.
For Ollama it is not: tags move, and `ollama/qwen2.5:7b` six months from now
will not be the weights that produced a number. Lane A models are pinned by
`sha256:` digest (docs/adr/0011).
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from harnesslab.providers.limits import QuotaLimits

_GROQ = "https://console.groq.com/docs/rate-limits"
_GEMINI = "https://ai.google.dev/gemini-api/docs/rate-limits"
_CEREBRAS = "https://inference-docs.cerebras.ai/support/rate-limits"
_OPENROUTER = "https://openrouter.ai/docs/api-reference/limits"
_MISTRAL = "https://docs.mistral.ai/deployment/laplateforme/tier/"

FETCHED = dt.date(2026, 8, 9)


class Lane(StrEnum):
    """The two populations the project measures. Both are first class."""

    LOCAL = "A"  # consumer hardware -- Ollama on an RTX 4060, 8GB
    API = "B"  # free-tier hosted APIs


class GateStatus(StrEnum):
    """Whether a model has cleared the Lane A capability gate (SPEC-010).

    Hosted models are `PASSED` on arrival -- there is nothing to gate. Local
    models start `PENDING`: on Day 1 nobody knows whether a 3B model can
    tool-call well enough to score above zero, or whether a 12B model fits in
    8GB of VRAM. Day 8 answers both and fills in the digests.
    """

    PENDING = "pending"
    PASSED = "passed"
    REJECTED = "rejected"


class ModelSpec(BaseModel):
    """One model on the board."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    key: str
    """Stable short id, written into every result row. Permanent."""

    inspect_model: str
    """What Inspect is handed, e.g. `groq/llama-3.1-8b-instant`."""

    lane: Lane
    display_name: str
    param_count_b: float | None = None
    limits: QuotaLimits

    # Lane A reproducibility. Empty for hosted models.
    ollama_digest: str | None = None
    quantization: str | None = None

    gate: GateStatus = GateStatus.PASSED
    supports_tools: bool = True
    in_pooled_grid: bool = False
    notes: str | None = None

    @field_validator("key")
    @classmethod
    def _key_is_stable_shaped(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-." for c in v):
            raise ValueError(f"key {v!r} must be alphanumeric with - or . only")
        return v

    @model_validator(mode="after")
    def _pinned_once_gated(self) -> Self:
        """A Lane A model that has passed its gate must be pinned by digest.

        Deliberately keyed on gate status rather than on grid membership. The
        registry declares *intent* to include a local model before SPEC-010 has
        run, and no digest exists until it does. What must never happen is a
        model being declared sweep-ready while still identified only by a
        mutable tag.
        """
        if self.lane is Lane.LOCAL and self.gate is GateStatus.PASSED:
            if not self.ollama_digest:
                raise ValueError(
                    f"{self.key}: Lane A model passed its gate without a digest. "
                    "Tags move; pin sha256: (docs/adr/0011)."
                )
            if not self.ollama_digest.startswith("sha256:"):
                raise ValueError(f"{self.key}: digest must start with 'sha256:'")
            if not self.quantization:
                raise ValueError(
                    f"{self.key}: quantisation must be recorded. If the top model "
                    "runs Q3 while others run Q4, the model axis confounds "
                    "parameter count with quantisation and that must be visible."
                )
        return self

    @property
    def sweep_ready(self) -> bool:
        return self.gate is GateStatus.PASSED


_MODELS: tuple[ModelSpec, ...] = (
    # ---------------- Lane B: free-tier hosted APIs ----------------
    ModelSpec(
        key="gemini-flash-lite",
        inspect_model="google/gemini-2.5-flash-lite",
        lane=Lane.API,
        display_name="Gemini 2.5 Flash-Lite",
        in_pooled_grid=True,
        notes="Lane B workhorse: ~125 trajectories/day, the most of any free tier here.",
        limits=QuotaLimits(
            requests_per_minute=15,
            requests_per_day=1_000,
            tokens_per_minute=250_000,
            context_ceiling=1_000_000,
            source_url=_GEMINI,
            fetched=FETCHED,
            probe_supported=False,  # Google publishes limits only in AI Studio
        ),
    ),
    ModelSpec(
        key="gemini-flash",
        inspect_model="google/gemini-2.5-flash",
        lane=Lane.API,
        display_name="Gemini 2.5 Flash",
        in_pooled_grid=True,
        limits=QuotaLimits(
            requests_per_minute=10,
            requests_per_day=250,
            tokens_per_minute=250_000,
            context_ceiling=1_000_000,
            source_url=_GEMINI,
            fetched=FETCHED,
            probe_supported=False,
        ),
    ),
    ModelSpec(
        key="groq-llama-8b",
        inspect_model="groq/llama-3.1-8b-instant",
        lane=Lane.API,
        display_name="Llama 3.1 8B Instant",
        param_count_b=8,
        in_pooled_grid=True,
        notes="Also the declared fallback substrate if the Lane A gate fails (SPEC-010).",
        limits=QuotaLimits(
            requests_per_minute=30,
            requests_per_day=14_400,
            tokens_per_minute=6_000,
            tokens_per_day=500_000,
            source_url=_GROQ,
            fetched=FETCHED,
        ),
    ),
    ModelSpec(
        key="groq-llama-70b",
        inspect_model="groq/llama-3.3-70b-versatile",
        lane=Lane.API,
        display_name="Llama 3.3 70B Versatile",
        param_count_b=70,
        in_pooled_grid=True,
        notes=(
            "~6 trajectories/day. On the board for the model-size axis at "
            "disclosed low N, never as a workhorse."
        ),
        limits=QuotaLimits(
            requests_per_minute=30,
            requests_per_day=1_000,
            tokens_per_minute=12_000,
            tokens_per_day=100_000,
            source_url=_GROQ,
            fetched=FETCHED,
        ),
    ),
    # WITHDRAWN from the pooled grid on day 1. The documented free tier is not
    # available on this account: /models lists the catalogue, but inference
    # returns HTTP 402 "Payment required to access this resource".
    #
    # This matters well beyond one missing model. Cerebras' 8,192-token free
    # context ceiling was the stated justification for capping every cell in the
    # pooled grid (adr/0008). That premise is gone, and the binding constraint is
    # now Groq's 6,000 TPM -- a rate limit rather than a context cap, and one
    # that is tighter in practice. adr/0008 needs amending before any sweep.
    ModelSpec(
        key="cerebras-gpt-oss-120b",
        inspect_model="openai-api/cerebras/gpt-oss-120b",
        lane=Lane.API,
        display_name="gpt-oss-120B (Cerebras)",
        param_count_b=120,
        in_pooled_grid=False,
        gate=GateStatus.REJECTED,
        notes=(
            "Free tier unavailable as of 2026-08-09: HTTP 402 on inference. "
            "Restore to the grid only if a free tier reappears."
        ),
        limits=QuotaLimits(
            requests_per_minute=5,
            requests_per_day=14_400,
            tokens_per_minute=30_000,
            tokens_per_day=1_000_000,
            context_ceiling=8_192,
            source_url=_CEREBRAS,
            fetched=FETCHED,
        ),
    ),
    # Breadth garnish, not in the pooled grid: 50 requests/day without
    # purchased credits, and the :free roster shifts continuously, which makes
    # it unusable as a stable axis.
    ModelSpec(
        key="openrouter-free",
        inspect_model="openrouter/qwen/qwen3-8b:free",
        lane=Lane.API,
        display_name="Qwen3 8B (OpenRouter free)",
        param_count_b=8,
        limits=QuotaLimits(
            requests_per_minute=20,
            requests_per_day=50,
            source_url=_OPENROUTER,
            fetched=FETCHED,
        ),
    ),
    # Promoted into the pooled grid on day 1, replacing Cerebras. Limits below
    # were read from live response headers, not from documentation -- the
    # provisional figures carried into day 1 (1 RPM / 500 RPD) were wrong by a
    # wide margin in the generous direction.
    ModelSpec(
        key="mistral-small",
        inspect_model="mistral/mistral-small-latest",
        lane=Lane.API,
        display_name="Mistral Small",
        in_pooled_grid=True,
        limits=QuotaLimits(
            requests_per_minute=50,
            tokens_per_minute=50_000,
            source_url=_MISTRAL,
            fetched=dt.date(2026, 8, 9),
        ),
        notes="Live-verified 50 RPM / 50K TPM. No published daily cap observed.",
    ),
    # ---------------- Lane A: consumer hardware ----------------
    # All PENDING until SPEC-010 on Day 8 measures VRAM fit, throughput and a
    # tool-calling floor, then pins digests. A 3B model may simply be unable to
    # tool-call well enough to score above zero, and a 12B at Q4 is ~7.3GB
    # against 8GB of VRAM -- tight enough that it has to be measured, not assumed.
    ModelSpec(
        key="qwen25-3b",
        inspect_model="ollama/qwen2.5:3b",
        lane=Lane.LOCAL,
        display_name="Qwen2.5 3B",
        param_count_b=3,
        gate=GateStatus.PENDING,
        in_pooled_grid=True,
        limits=QuotaLimits(
            context_ceiling=32_768,
            source_url="https://ollama.com/library/qwen2.5",
            fetched=FETCHED,
            probe_supported=False,
        ),
    ),
    ModelSpec(
        key="qwen25-7b",
        inspect_model="ollama/qwen2.5:7b",
        lane=Lane.LOCAL,
        display_name="Qwen2.5 7B",
        param_count_b=7,
        gate=GateStatus.PENDING,
        in_pooled_grid=True,
        limits=QuotaLimits(
            context_ceiling=32_768,
            source_url="https://ollama.com/library/qwen2.5",
            fetched=FETCHED,
            probe_supported=False,
        ),
    ),
    ModelSpec(
        key="gemma3-12b",
        inspect_model="ollama/gemma3:12b",
        lane=Lane.LOCAL,
        display_name="Gemma 3 12B",
        param_count_b=12,
        gate=GateStatus.PENDING,
        in_pooled_grid=True,
        notes="~7.3GB at Q4 against 8GB VRAM. Tight; SPEC-010 measures whether it resides.",
        limits=QuotaLimits(
            context_ceiling=32_768,
            source_url="https://ollama.com/library/gemma3",
            fetched=FETCHED,
            probe_supported=False,
        ),
    ),
)

POOLED_GRID_SIZE = 8


def registry() -> dict[str, ModelSpec]:
    """Every known model, keyed by `ModelSpec.key`."""
    return {m.key: m for m in _MODELS}


def get(key: str) -> ModelSpec:
    try:
        return registry()[key]
    except KeyError:
        raise KeyError(f"unknown model key {key!r}; see providers/registry.py") from None


def pooled_grid() -> list[ModelSpec]:
    """The models of the primary grid, in a stable order.

    Order is Lane then key so that results, charts and tables agree without
    anyone having to sort them consistently.
    """
    return sorted(
        (m for m in _MODELS if m.in_pooled_grid),
        key=lambda m: (m.lane, m.key),
    )


def by_lane(lane: Lane) -> list[ModelSpec]:
    return sorted((m for m in _MODELS if m.lane is lane), key=lambda m: m.key)


def assert_sweep_ready() -> None:
    """Refuse to sweep a grid that is not fully identified.

    Called before any scored run. Lane A models that have not passed SPEC-010
    have no digest, so a result from them could not be reproduced -- and an
    unreproducible number is not a result.
    """
    blocked = [m.key for m in pooled_grid() if not m.sweep_ready]
    if blocked:
        raise RuntimeError(
            "pooled grid is not sweep-ready; these models have not passed the "
            f"Lane A gate (SPEC-010): {', '.join(blocked)}"
        )
