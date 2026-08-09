"""SPEC-001: the pricing loader.

The behaviour under test is mostly *refusal*. An invented rate is
indistinguishable from a real one once it is plotted on the Pareto chart, so the
loader raises rather than guessing.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from harnesslab.providers import pricing
from harnesslab.providers.pricing import ModelPrice, PricingTable, load_pricing


def _table(**prices: ModelPrice) -> PricingTable:
    return PricingTable(fetched=dt.date(2026, 8, 9), prices=prices)


class TestCostRefusesToGuess:
    def test_unverified_price_raises(self) -> None:
        table = _table(m=ModelPrice(model_key="m", usd_per_1m_input=1, usd_per_1m_output=2))
        with pytest.raises(ValueError, match="unverified"):
            table.cost_usd("m", 1000, 100)

    def test_missing_model_raises(self) -> None:
        with pytest.raises(KeyError, match="no price"):
            _table().cost_usd("absent", 1000, 100)

    def test_verified_price_computes(self) -> None:
        table = _table(
            m=ModelPrice(
                model_key="m",
                usd_per_1m_input=1.0,
                usd_per_1m_output=3.0,
                source_url="https://example.com",
                verified=True,
            )
        )
        # 2M input at $1/M + 1M output at $3/M
        assert table.cost_usd("m", 2_000_000, 1_000_000) == pytest.approx(5.0)


class TestHistoricalPricing:
    """A run is costed with the prices in force on its own date. Otherwise
    re-ingesting old logs silently rewrites history."""

    @pytest.fixture
    def tables(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        for day, rate in ((dt.date(2026, 1, 1), 10.0), (dt.date(2026, 6, 1), 2.0)):
            (tmp_path / f"pricing-{day.isoformat()}.json").write_text(
                json.dumps(
                    {
                        "currency": "USD",
                        "prices": {
                            "m": {
                                "usd_per_1m_input": rate,
                                "usd_per_1m_output": rate,
                                "source_url": "https://example.com",
                                "verified": True,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
        monkeypatch.setattr(pricing, "PRICING_DIR", tmp_path)
        load_pricing.cache_clear()
        yield tmp_path
        load_pricing.cache_clear()

    def test_uses_the_table_in_force_on_that_date(self, tables: Path) -> None:
        march = load_pricing(dt.date(2026, 3, 15))
        assert march.fetched == dt.date(2026, 1, 1)
        assert march.cost_usd("m", 1_000_000, 0) == pytest.approx(10.0)

    def test_later_run_uses_later_table(self, tables: Path) -> None:
        assert load_pricing(dt.date(2026, 7, 1)).fetched == dt.date(2026, 6, 1)

    def test_run_predating_every_table_raises(self, tables: Path) -> None:
        with pytest.raises(ValueError, match="did not yet exist"):
            load_pricing(dt.date(2025, 12, 1))


class TestShippedTable:
    def test_every_registry_model_has_an_entry(self) -> None:
        """A model that can be run but not costed would silently drop out of the
        Pareto chart."""
        from harnesslab.providers import Lane, registry

        table = load_pricing()
        for spec in registry().values():
            if spec.lane is Lane.API:
                assert spec.key in table.prices, f"{spec.key} has no price entry"

    def test_prices_are_unverified_until_confirmed(self) -> None:
        """Day 1 ships the structure, not the numbers. `make pricing` fills them
        in against each vendor's page."""
        assert pricing.unverified(), "prices are marked verified but were never confirmed"
