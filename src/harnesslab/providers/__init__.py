"""Provider catalogue: what models exist, what their free tiers allow, what
they would cost at published rates.

This package *describes* limits. It does not enforce them -- SPEC-006 owns the
ledger and admission control, and SPEC-011 owns backoff.
"""

from harnesslab.providers.limits import ProbeResult, QuotaLimits
from harnesslab.providers.registry import (
    GateStatus,
    Lane,
    ModelSpec,
    by_lane,
    pooled_grid,
    registry,
)

__all__ = [
    "GateStatus",
    "Lane",
    "ModelSpec",
    "ProbeResult",
    "QuotaLimits",
    "by_lane",
    "pooled_grid",
    "registry",
]
