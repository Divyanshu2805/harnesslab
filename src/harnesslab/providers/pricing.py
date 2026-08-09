"""Notional cost: what free execution *would* cost at published rates.

Execution here is $0 -- every call is on a free tier or local hardware. Notional
cost multiplies the tokens actually consumed by the vendor's own published *paid*
rate, giving a number with real economic meaning from a run that cost nothing.
That is what makes free-tier benchmarking meaningful rather than a curiosity.

Two rules this module enforces rather than documents:

* **Prices are versioned with a fetch date**, and cost is computed from the table
  in force on the *run's* date -- not whatever is current at ingest. Otherwise
  re-ingesting old logs silently rewrites history.
* **An unverified price cannot produce a cost.** Loading a table entry that has
  not been confirmed against the vendor's page raises. Inventing a plausible
  number would be indistinguishable from a real one in the published chart.

See docs/COST_MODEL.md, which also explains why Lane A uses an entirely
different basis (GPU-hour rental) and why the two are not equivalent.
"""

from __future__ import annotations

import datetime as dt
import functools
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from harnesslab.config import REPO_ROOT

PRICING_DIR = REPO_ROOT / "data" / "pricing"


class ModelPrice(BaseModel):
    model_config = ConfigDict(frozen=True, protected_namespaces=())

    model_key: str
    usd_per_1m_input: float | None = None
    usd_per_1m_output: float | None = None
    source_url: str | None = None
    verified: bool = False
    note: str | None = None

    @property
    def usable(self) -> bool:
        return (
            self.verified
            and self.usd_per_1m_input is not None
            and self.usd_per_1m_output is not None
        )


class PricingTable(BaseModel):
    model_config = ConfigDict(frozen=True)

    fetched: dt.date
    currency: str = "USD"
    prices: dict[str, ModelPrice]

    def cost_usd(self, model_key: str, input_tokens: int, output_tokens: int) -> float:
        """Notional cost of one trajectory.

        Raises rather than guessing. A silently-zero or silently-estimated cost
        would propagate into the Pareto chart, which is a published claim.
        """
        price = self.prices.get(model_key)
        if price is None:
            raise KeyError(
                f"no price for {model_key!r} in the {self.fetched} table. "
                "Run `make pricing` to refresh it."
            )
        if not price.usable:
            raise ValueError(
                f"price for {model_key!r} is unverified in the {self.fetched} table. "
                "Confirm it against the vendor's pricing page and set verified=true; "
                "an invented rate is indistinguishable from a real one once plotted."
            )
        assert price.usd_per_1m_input is not None
        assert price.usd_per_1m_output is not None
        return (
            input_tokens * price.usd_per_1m_input + output_tokens * price.usd_per_1m_output
        ) / 1_000_000


def available_tables() -> list[dt.date]:
    dates: list[dt.date] = []
    for path in PRICING_DIR.glob("pricing-*.json"):
        try:
            dates.append(dt.date.fromisoformat(path.stem.removeprefix("pricing-")))
        except ValueError:
            continue
    return sorted(dates)


@functools.lru_cache(maxsize=8)
def load_pricing(on: dt.date | None = None) -> PricingTable:
    """The pricing table in force on a given date.

    Picks the most recent table at or before `on`, so a result from June is
    costed with June's prices even if the repository now holds September's.
    """
    tables = available_tables()
    if not tables:
        raise FileNotFoundError(f"no pricing tables in {PRICING_DIR}")
    if on is None:
        chosen = tables[-1]
    else:
        earlier = [d for d in tables if d <= on]
        if not earlier:
            raise ValueError(
                f"no pricing table at or before {on}; earliest is {tables[0]}. "
                "A run cannot be costed with prices that did not yet exist."
            )
        chosen = earlier[-1]
    path = PRICING_DIR / f"pricing-{chosen.isoformat()}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return PricingTable(
        fetched=chosen,
        currency=raw.get("currency", "USD"),
        prices={k: ModelPrice(model_key=k, **v) for k, v in raw["prices"].items()},
    )


def unverified(table: PricingTable | None = None) -> list[str]:
    """Model keys whose price still needs confirming. Reported by `make pricing`."""
    table = table or load_pricing()
    return sorted(k for k, p in table.prices.items() if not p.usable)


def _write_path(fetched: dt.date) -> Path:
    return PRICING_DIR / f"pricing-{fetched.isoformat()}.json"
