"""
Intent Parser & Planner

Parses user intent and creates tool execution plans.
"""

import json
import os
from typing import Any

import yaml


def load_llm_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "configs", "llm.yaml"
    )
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm():
    """Get an LLM instance based on configuration."""
    config = load_llm_config()
    provider = config.get("default_provider", "openai")
    provider_config = config["providers"].get(provider, {})

    model = provider_config.get("model", "gpt-4o")
    api_key = os.getenv(provider_config.get("api_key_env", "OPENAI_API_KEY"))

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=provider_config.get("temperature", 0.3),
            max_tokens=provider_config.get("max_tokens", 4096),
        )
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=provider_config.get("base_url", "https://api.deepseek.com/v1"),
            temperature=provider_config.get("temperature", 0.3),
            max_tokens=provider_config.get("max_tokens", 4096),
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=provider_config.get("temperature", 0.3),
            max_tokens=provider_config.get("max_tokens", 4096),
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


INTENT_PROMPT = """You are a mining industry analyst assistant. Parse the user's query (in Chinese or English) and extract:
- target: the geographic region or mine name (e.g. "Pilbara", "Greenbushes", "西澳")
- commodity: the mineral/commodity in English (e.g. "Lithium", "Iron Ore", "Gold", "Copper")
- scope: time scope in English (e.g. "today", "this week", "last 3 days")

Return ONLY valid JSON with these three keys. No other text.

User query: {query}

JSON:"""


def parse_intent(query: str) -> dict[str, str]:
    """Parse user intent from natural language query.

    Uses LLM when available, otherwise falls back to rule-based parsing.
    """
    try:
        llm = get_llm()
        result = llm.invoke(INTENT_PROMPT.format(query=query))
        content = result.content if hasattr(result, "content") else str(result)
        return json.loads(content)
    except Exception:
        return _rule_based_intent(query)


def _rule_based_intent(query: str) -> dict[str, str]:
    """Simple rule-based intent parser as fallback. Handles Chinese and English."""
    query_lower = query.lower()

    # Detect commodity
    commodity = "Lithium"
    if "lithium" in query_lower or "锂" in query_lower:
        commodity = "Lithium"
    elif "iron" in query_lower or "铁" in query_lower:
        commodity = "Iron Ore"
    elif "gold" in query_lower or "金" in query_lower:
        commodity = "Gold"
    elif "copper" in query_lower or "铜" in query_lower:
        commodity = "Copper"

    # Detect target
    target = "Pilbara"
    if "pilbara" in query_lower or "皮尔巴拉" in query_lower:
        target = "Pilbara"
    elif "greenbushes" in query_lower or "格林布什" in query_lower:
        target = "Greenbushes"
    elif "wodgina" in query_lower:
        target = "Wodgina"
    elif "wa" in query_lower or "western australia" in query_lower or "西澳" in query_lower:
        target = "Western Australia"

    # Detect scope
    scope = "today"
    if "today" in query_lower or "今日" in query_lower or "今天" in query_lower or "简报" in query_lower:
        scope = "today"
    elif "week" in query_lower or "周" in query_lower or "本周" in query_lower:
        scope = "this week"
    elif "month" in query_lower or "月" in query_lower:
        scope = "this month"

    return {"target": target, "commodity": commodity, "scope": scope}


def build_plan(intent: dict[str, str]) -> list[dict]:
    """Build an execution plan based on parsed intent.

    Returns a list of tool calls with parameters and dependencies.
    """
    target = intent.get("target", "")
    commodity = intent.get("commodity", "")
    scope = intent.get("scope", "today")

    days = 1 if scope == "today" else (7 if "week" in scope else 3)

    commodity_map = {
        "Lithium": "lithium_carbonate",
        "Gold": "gold",
        "Copper": "copper",
        "Iron Ore": "iron_ore",
    }
    commodity_id = commodity_map.get(commodity, "lithium_carbonate")

    # Real resource report URLs
    resource_urls = {
        "Pilbara": "https://www.pls.com.au/site/content/reports/PLS_Annual_Resource_and_Reserve_Statement_2024.pdf",
        "Greenbushes": "https://www.igolimited.com.au/investors-centre/asx-announcements/",
        "Wodgina": "https://www.mineralresources.com.au/investors/asx-announcements/",
    }
    pdf_url = resource_urls.get(target, f"https://www.sedar.com/search/{target.lower()}_resources.pdf")

    plan = [
        {
            "phase": 1,
            "tool": "search_news",
            "params": {"query": f"{target} {commodity}", "days": days},
            "server": "mining-news",
            "depends_on": [],
        },
        {
            "phase": 1,
            "tool": "get_price",
            "params": {"commodity": commodity_id},
            "server": "lme-price",
            "depends_on": [],
        },
        {
            "phase": 1,
            "tool": "get_trend",
            "params": {"commodity": commodity_id, "days": min(days + 6, 30)},
            "server": "lme-price",
            "depends_on": [],
        },
    ]

    # Phase 2: Fetch article contents (optional, may fail due to paywalls/geoblocking)
    plan.append({
        "phase": 2,
        "tool": "fetch_article",
        "params": {"url": "{{news[0].url}}"},
        "server": "mining-news",
        "depends_on": ["search_news"],
        "conditional": True,
        "optional": True,
    })

    # Phase 3: Real PDF resource report + reference data fallback
    plan.append({
        "phase": 3,
        "tool": "extract_resources",
        "params": {"pdf_url": pdf_url, "mine_name": target},
        "server": "mineral-pdf",
        "depends_on": [],
        "optional": True,
    })

    return plan
