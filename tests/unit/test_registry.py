"""SPEC-001: the provider registry."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from harnesslab.providers import GateStatus, Lane, ModelSpec, QuotaLimits
from harnesslab.providers.registry import (
    POOLED_GRID_SIZE,
    assert_sweep_ready,
    by_lane,
    get,
    pooled_grid,
    registry,
)

_LIMITS = QuotaLimits(
    requests_per_day=100,
    source_url="https://example.com/limits",
    fetched=dt.date(2026, 8, 9),
)


class TestRegistryShape:
    """AC-1: complete registry, deterministic pooled grid."""

    def test_pooled_grid_has_exactly_eight(self) -> None:
        assert len(pooled_grid()) == POOLED_GRID_SIZE

    def test_pooled_grid_order_is_stable(self) -> None:
        assert [m.key for m in pooled_grid()] == [m.key for m in pooled_grid()]

    def test_pooled_grid_spans_both_lanes(self) -> None:
        lanes = {m.lane for m in pooled_grid()}
        assert lanes == {Lane.LOCAL, Lane.API}

    def test_lane_a_spans_a_real_capability_range(self) -> None:
        """A 3B-only local axis would make 'harness beats model' an artefact of
        picking models that were never going to differ (SPEC-010 AC-4)."""
        sizes = [m.param_count_b for m in by_lane(Lane.LOCAL) if m.param_count_b]
        assert max(sizes) / min(sizes) >= 2.0

    def test_keys_are_unique(self) -> None:
        assert len(registry()) == len({m.key for m in registry().values()})

    def test_get_rejects_unknown_key(self) -> None:
        with pytest.raises(KeyError, match="unknown model key"):
            get("no-such-model")


class TestDigestPinning:
    """AC-2: a gated Lane A model must be pinned. See docs/adr/0011."""

    def test_passed_lane_a_without_digest_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="without a digest"):
            ModelSpec(
                key="unpinned",
                inspect_model="ollama/qwen2.5:7b",
                lane=Lane.LOCAL,
                display_name="Unpinned",
                gate=GateStatus.PASSED,
                limits=_LIMITS,
            )

    def test_digest_must_be_sha256(self) -> None:
        with pytest.raises(ValidationError, match="sha256:"):
            ModelSpec(
                key="badtag",
                inspect_model="ollama/qwen2.5:7b",
                lane=Lane.LOCAL,
                display_name="Bad",
                gate=GateStatus.PASSED,
                ollama_digest="qwen2.5:7b",
                quantization="Q4_K_M",
                limits=_LIMITS,
            )

    def test_quantisation_must_be_recorded(self) -> None:
        """If the top model runs Q3 while others run Q4, the model axis
        confounds parameter count with quantisation."""
        with pytest.raises(ValidationError, match="quantisation"):
            ModelSpec(
                key="noquant",
                inspect_model="ollama/qwen2.5:7b",
                lane=Lane.LOCAL,
                display_name="No quant",
                gate=GateStatus.PASSED,
                ollama_digest="sha256:" + "ab" * 32,
                limits=_LIMITS,
            )

    def test_pending_lane_a_may_be_unpinned(self) -> None:
        """Before SPEC-010 runs, no digest exists. The registry declares intent."""
        spec = ModelSpec(
            key="pending",
            inspect_model="ollama/qwen2.5:7b",
            lane=Lane.LOCAL,
            display_name="Pending",
            gate=GateStatus.PENDING,
            limits=_LIMITS,
        )
        assert not spec.sweep_ready

    def test_sweep_is_blocked_until_the_gate_passes(self) -> None:
        with pytest.raises(RuntimeError, match="not sweep-ready"):
            assert_sweep_ready()


class TestProvenance:
    """AC-3: every quota carries a source and a fetch date."""

    def test_all_limits_have_source_and_date(self) -> None:
        for spec in registry().values():
            assert spec.limits.source_url.startswith("https://"), spec.key
            assert isinstance(spec.limits.fetched, dt.date), spec.key

    def test_source_must_be_a_url(self) -> None:
        with pytest.raises(ValidationError, match="provenance"):
            QuotaLimits(requests_per_day=1, source_url="the docs", fetched=dt.date.today())

    def test_empty_limits_are_rejected(self) -> None:
        with pytest.raises(ValidationError, match="no limit at all"):
            QuotaLimits(source_url="https://example.com", fetched=dt.date.today())


class TestCapacityArithmetic:
    """The translation from raw quota to trajectories, which is the number that
    actually matters. See docs/TOKEN_BUDGET.md."""

    def test_tokens_bind_before_requests_on_groq_70b(self) -> None:
        """1,000 requests/day reads as generous; 100K tokens/day is ~6
        trajectories. Getting this backwards is how the original plan came out
        an order of magnitude wrong."""
        limits = get("groq-llama-70b").limits
        assert limits.binds_on() == "TPD"
        assert limits.trajectories_per_day() == pytest.approx(6, abs=1)

    def test_requests_bind_on_gemini_flash_lite(self) -> None:
        limits = get("gemini-flash-lite").limits
        assert limits.binds_on() == "RPD"
        assert limits.trajectories_per_day() == 125

    def test_local_models_are_unconstrained_by_quota(self) -> None:
        for spec in by_lane(Lane.LOCAL):
            assert spec.limits.trajectories_per_day() is None

    def test_cerebras_is_withdrawn_and_out_of_the_grid(self) -> None:
        """Day-1 probe finding: the documented free tier returns HTTP 402.

        Cerebras' 8,192-token ceiling was the stated justification for capping
        every pooled cell (docs/adr/0008). Withdrawing it removes that premise,
        which is why the next test exists.
        """
        spec = get("cerebras-gpt-oss-120b")
        assert spec.gate is GateStatus.REJECTED
        assert not spec.in_pooled_grid

    def test_no_provider_now_forces_an_8k_context_cap(self) -> None:
        """Guards a live premise rather than a constant.

        With Cerebras gone, the tightest context ceiling in the pooled grid is
        32,768 (the local models), so nothing *forces* an 8K shared policy any
        more. If a future provider reintroduces a tighter ceiling this test
        fails, which is the intended signal to revisit adr/0008 rather than to
        edit the number here.
        """
        ceilings = [
            m.limits.context_ceiling for m in pooled_grid() if m.limits.context_ceiling is not None
        ]
        assert min(ceilings) > 8_192

    def test_groq_tpm_is_the_new_binding_constraint(self) -> None:
        """6,000 tokens/minute, verified live and confirmed by a 429 at ~7K.

        Tighter in practice than the 8,192 ceiling it replaces, but a rate limit
        rather than a per-request cap -- it throttles throughput rather than
        truncating history. adr/0008 has to be amended, not simply renumbered.
        """
        tpms = [
            m.limits.tokens_per_minute
            for m in pooled_grid()
            if m.limits.tokens_per_minute is not None
        ]
        assert min(tpms) == 6_000
        assert get("groq-llama-8b").limits.tokens_per_minute == 6_000
