"""
LME Price MCP Server - 矿产品行情分析服务

Fetches real market data via Yahoo Finance chart API.
"""

from datetime import datetime
from typing import Annotated

import requests
from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("lme-price")

_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Real tickers for lithium market exposure
_COMMODITY_TICKERS: dict[str, dict] = {
    "lithium_carbonate": {
        "name": "碳酸锂期货 (广期所)",
        "ticker": "PLS.AX",  # Pilbara Minerals — proxy for lithium spot
        "unit": "AUD",
        "label": "Pilbara Minerals (PLS.AX) — 锂矿股基准",
    },
    "spodumene": {
        "name": "锂辉石精矿 (6% Li2O)",
        "ticker": "MIN.AX",  # Mineral Resources
        "unit": "AUD",
        "label": "Mineral Resources (MIN.AX)",
    },
    "lithium_etf": {
        "name": "锂矿ETF (LIT)",
        "ticker": "LIT",
        "unit": "USD",
        "label": "Global X Lithium & Battery Tech ETF",
    },
    "albemarle": {
        "name": "Albemarle (ALB)",
        "ticker": "ALB",
        "unit": "USD",
        "label": "Albemarle Corporation — 全球最大锂生产商",
    },
    "sqm": {
        "name": "SQM (SQM)",
        "ticker": "SQM",
        "unit": "USD",
        "label": "Sociedad Química y Minera — 智利锂巨头",
    },
    "iron_ore": {
        "name": "铁矿石 (62% Fe)",
        "ticker": "BHP",
        "unit": "USD",
        "label": "BHP Group — 综合矿业基准",
    },
    "copper": {
        "name": "铜 (LME)",
        "ticker": "COPX",
        "unit": "USD",
        "label": "Global X Copper Miners ETF",
    },
    "gold": {
        "name": "黄金",
        "ticker": "GLD",
        "unit": "USD",
        "label": "SPDR Gold Trust ETF",
    },
}

_APPROVED_COMMODITIES = list(_COMMODITY_TICKERS.keys())

def _fetch_ticker_data(ticker_symbol: str, days: int = 7) -> dict | None:
    """Fetch real ticker data from Yahoo Finance chart API."""

    # Map days to Yahoo range parameter — always fetch fresh
    if days <= 5:
        range_str = "5d"
    elif days <= 30:
        range_str = "1mo"
    else:
        range_str = "3mo"

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?range={range_str}&interval=1d"

    try:
        resp = requests.get(url, headers=_API_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        data = resp.json()
        result = data["chart"]["result"][0]
        meta = result["meta"]
        quotes = result["indicators"]["quote"][0]
        timestamps = result.get("timestamp", [])

        closes = [c for c in quotes["close"] if c is not None]
        if len(closes) < 2:
            return None

        current = round(float(closes[-1]), 2)
        prev = round(float(closes[0]), 2)
        change = round(current - prev, 2)
        change_pct = round((change / prev) * 100, 2) if prev else 0

        # Volatility
        mean_p = sum(closes) / len(closes)
        variance = sum((p - mean_p) ** 2 for p in closes) / len(closes)
        volatility = round((variance ** 0.5 / mean_p) * 100, 2) if mean_p else 0

        if change_pct > 1:
            trend = "upward"
        elif change_pct < -1:
            trend = "downward"
        else:
            trend = "stable"

        return {
            "current": current,
            "change_7d": change,
            "change_pct": change_pct,
            "volatility": volatility,
            "trend": trend,
            "history": [round(float(c), 2) for c in closes],
            "period_days": min(days, len(closes)),
        }
    except Exception:
        return None


@mcp.tool()
async def get_price(
    commodity: Annotated[str, Field(description=f"Commodity ID. Options: {', '.join(_APPROVED_COMMODITIES)}")],
) -> dict:
    """Get the current market price for a commodity via real stock data."""
    commodity_key = commodity.lower().replace(" ", "_")
    config = _COMMODITY_TICKERS.get(commodity_key)
    if not config:
        return {
            "error": f"Unknown commodity '{commodity}'. Options: {', '.join(_APPROVED_COMMODITIES)}",
            "commodity": commodity,
            "price": 0,
            "unit": "",
        }

    data = _fetch_ticker_data(config["ticker"], days=7)
    if data is None:
        return {
            "error": f"Failed to fetch data for {config['ticker']}",
            "commodity": config["name"],
            "price": 0,
            "unit": config["unit"],
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

    return {
        "commodity": config["name"],
        "label": config["label"],
        "price": data["current"],
        "unit": config["unit"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


@mcp.tool()
async def get_trend(
    commodity: Annotated[str, Field(description=f"Commodity ID. Options: {', '.join(_APPROVED_COMMODITIES)}")],
    days: Annotated[int, Field(description="Number of days for trend analysis (max 30)", ge=1, le=30)] = 7,
) -> dict:
    """Get real price trend analysis from market data."""
    commodity_key = commodity.lower().replace(" ", "_")
    config = _COMMODITY_TICKERS.get(commodity_key)
    if not config:
        return {
            "error": f"Unknown commodity '{commodity}'. Options: {', '.join(_APPROVED_COMMODITIES)}",
            "commodity": commodity,
            "current": 0,
            "change_7d": 0,
            "change_pct": 0,
            "volatility": 0,
            "trend": "unknown",
        }

    data = _fetch_ticker_data(config["ticker"], days=days)
    if data is None:
        return {
            "error": f"Failed to fetch trend data for {config['ticker']}",
            "commodity": config["name"],
            "current": 0,
            "change_7d": 0,
            "change_pct": 0,
            "volatility": 0,
            "trend": "unknown",
            "period_days": days,
        }

    return {
        "commodity": config["name"],
        "label": config["label"],
        "unit": config["unit"],
        "ticker": config["ticker"],
        "current": data["current"],
        "change_7d": data["change_7d"],
        "change_pct": data["change_pct"],
        "volatility": data["volatility"],
        "trend": data["trend"],
        "period_days": data["period_days"],
    }


@mcp.tool()
async def list_commodities() -> list[dict]:
    """List all available commodities with their real tickers."""
    return [
        {"id": k, "name": v["name"], "ticker": v["ticker"], "unit": v["unit"], "label": v["label"]}
        for k, v in _COMMODITY_TICKERS.items()
    ]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
