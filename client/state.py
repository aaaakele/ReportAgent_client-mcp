"""
Agent State Definition

Defines the shared state schema used throughout the agent workflow.
"""

from typing import TypedDict


class NewsArticle(TypedDict, total=False):
    title: str
    url: str
    published_at: str
    summary: str
    source: str


class ResourceEstimate(TypedDict, total=False):
    measured_mt: float
    indicated_mt: float
    inferred_mt: float
    total_mt: float
    grade_li2o: str
    report_type: str
    error: str


class PriceData(TypedDict, total=False):
    commodity: str
    price: float
    unit: str
    date: str
    current: float
    change_7d: float
    change_pct: float
    volatility: float
    trend: str
    error: str


class AgentState(TypedDict, total=False):
    """Shared state for the agent workflow."""

    # Input
    user_query: str
    target: str
    commodity: str
    scope: str

    # Plans
    plan: list[dict]

    # Results
    news: list[NewsArticle]
    fetch_contents: list[dict]
    resources: ResourceEstimate
    prices: dict[str, PriceData]

    # Output
    report: str
    report_path: str
    errors: list[str]
