"""
Tests for LME Price MCP Server (real market data via yfinance).
"""

import pytest

from servers.lme_price.server import get_price, get_trend, list_commodities


@pytest.mark.asyncio
async def test_get_price_lithium():
    result = await get_price(commodity="lithium_carbonate")
    assert "commodity" in result
    assert "price" in result
    assert "unit" in result
    assert "date" in result
    # Price may be 0 if yfinance fetch fails, but structure must be valid
    assert isinstance(result["price"], (int, float))


@pytest.mark.asyncio
async def test_get_price_spodumene():
    result = await get_price(commodity="spodumene")
    assert "commodity" in result
    assert "price" in result
    assert "unit" in result


@pytest.mark.asyncio
async def test_get_price_invalid():
    result = await get_price(commodity="nonexistent")
    assert "error" in result


@pytest.mark.asyncio
async def test_get_trend():
    result = await get_trend(commodity="lithium_carbonate", days=7)
    assert "commodity" in result
    assert "current" in result
    assert "change_7d" in result
    assert "change_pct" in result
    assert "volatility" in result
    assert result["trend"] in ("upward", "downward", "stable", "unknown")
    assert result["period_days"] == 7


@pytest.mark.asyncio
async def test_get_trend_max_days():
    result = await get_trend(commodity="spodumene", days=30)
    # Yahoo Finance 1mo range returns ~22 trading days
    assert 15 <= result["period_days"] <= 30


@pytest.mark.asyncio
async def test_get_trend_invalid():
    result = await get_trend(commodity="unknown", days=7)
    assert "error" in result


@pytest.mark.asyncio
async def test_list_commodities():
    result = await list_commodities()
    assert isinstance(result, list)
    assert len(result) >= 3
    for item in result:
        assert "id" in item
        assert "name" in item
        assert "ticker" in item
