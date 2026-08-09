"""Free-tier quota descriptors.

Quotas are *claims about the world* and they expire. Every one carries a source
URL and a fetch date, and `scripts/verify_providers.py` re-probes them against
the live APIs and fails loudly on drift. A number in here without provenance is
a bug, not an oversight.
"""

from __future__ import annotations

import datetime as dt
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class QuotaLimits(BaseModel):
    """One model's free-tier ceiling.

    `None` means "not published" or "not binding" -- which is NOT the same as
    unlimited. The estimator treats None as unconstrained for planning while the
    ledger still records real consumption, so an undocumented ceiling surfaces
    as an anomaly rather than as a crash mid-sweep.
    """

    model_config = ConfigDict(frozen=True)

    requests_per_minute: int | None = None
    requests_per_day: int | None = None
    tokens_per_minute: int | None = None
    tokens_per_day: int | None = None

    context_ceiling: int | None = None
    """The free tier's context cap, which may be far below the model's
    architectural window. Cerebras publishes 8,192 on models whose real window
    is much larger, and that single number is what forces the shared context
    policy across the whole pooled grid (docs/adr/0008)."""

    source_url: str
    fetched: dt.date

    probe_supported: bool = True
    """Whether limits are readable from response headers. Google publishes them
    only in AI Studio, so a probe cannot confirm them and drift there has to be
    caught by hand."""

    @field_validator("source_url")
    @classmethod
    def _real_source(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("source_url must be a URL -- quotas need provenance")
        return v

    @model_validator(mode="after")
    def _at_least_one_limit(self) -> Self:
        if not any(
            (
                self.requests_per_minute,
                self.requests_per_day,
                self.tokens_per_minute,
                self.tokens_per_day,
                self.context_ceiling,
            )
        ):
            raise ValueError("QuotaLimits declares no limit at all")
        return self

    def trajectories_per_day(self, tokens_each: int = 15_000, calls_each: int = 8) -> int | None:
        """Rough daily trajectory capacity -- the number that actually matters.

        Raw quota figures mislead for agentic work because a trajectory is many
        calls that each resend accumulated history. Groq's 70B reads as generous
        at 1,000 requests/day and is really about six trajectories, because
        100K tokens/day binds first.

        Returns None when nothing binds. See docs/TOKEN_BUDGET.md.
        """
        caps: list[int] = []
        if self.tokens_per_day is not None:
            caps.append(self.tokens_per_day // tokens_each)
        if self.requests_per_day is not None:
            caps.append(self.requests_per_day // calls_each)
        return min(caps) if caps else None

    def binds_on(self) -> str:
        """Which dimension runs out first, for the capacity table."""
        by_tokens = self.tokens_per_day // 15_000 if self.tokens_per_day else None
        by_reqs = self.requests_per_day // 8 if self.requests_per_day else None
        if by_tokens is None and by_reqs is None:
            return "unconstrained"
        if by_tokens is None:
            return "RPD"
        if by_reqs is None:
            return "TPD"
        return "TPD" if by_tokens <= by_reqs else "RPD"


class ProbeResult(BaseModel):
    """What a live probe of one model observed."""

    model_config = ConfigDict(frozen=True)

    model_key: str
    reachable: bool
    observed: QuotaLimits | None = None
    error: str | None = None
    note: str | None = None

    def drift_against(self, declared: QuotaLimits) -> list[str]:
        """Fields where the live API disagrees with the registry.

        Only compares fields the probe actually observed; a header the provider
        does not send is silence, not a contradiction.
        """
        if self.observed is None:
            return []
        diffs: list[str] = []
        for field in (
            "requests_per_minute",
            "requests_per_day",
            "tokens_per_minute",
            "tokens_per_day",
        ):
            seen = getattr(self.observed, field)
            said = getattr(declared, field)
            if seen is not None and said is not None and seen != said:
                diffs.append(f"{field}: registry {said:,} vs live {seen:,}")
        return diffs
