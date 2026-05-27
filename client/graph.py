"""
Agent Workflow Graph

LangGraph-based workflow that orchestrates the full pipeline:
Intent → Plan → Permission Check → Execute → Aggregate → Report
"""

import asyncio
import os
from typing import Literal

from langgraph.graph import END, StateGraph

from .executor import execute_plan
from .permissions import PermissionManager
from .planner import build_plan, parse_intent
from .report_generator import render_report
from .state import AgentState


async def parse_intent_node(state: AgentState) -> AgentState:
    """Node: parse user intent from query."""
    query = state.get("user_query", "")
    intent = parse_intent(query)
    state["target"] = intent.get("target", "")
    state["commodity"] = intent.get("commodity", "")
    state["scope"] = intent.get("scope", "today")
    return state


async def planning_node(state: AgentState) -> AgentState:
    """Node: build execution plan."""
    intent = {
        "target": state.get("target", ""),
        "commodity": state.get("commodity", ""),
        "scope": state.get("scope", "today"),
    }
    plan = build_plan(intent)
    state["plan"] = plan
    return state


async def permission_check_node(state: AgentState) -> AgentState:
    """Node: validate all planned tool calls against permissions."""
    perm_manager = PermissionManager()
    errors = list(state.get("errors", []))

    for task in state.get("plan", []):
        try:
            perm_manager.validate_tool_call(
                task["tool"], "executor", task.get("params", {})
            )
        except Exception as e:
            if not task.get("optional"):
                errors.append(f"Permission denied for '{task['tool']}': {e}")

    state["errors"] = errors
    return state


async def execution_node(state: AgentState) -> AgentState:
    """Node: execute the plan by calling MCP tools."""
    perm_manager = PermissionManager()
    state = await execute_plan(state, perm_manager)
    return state


async def aggregation_node(state: AgentState) -> AgentState:
    """Node: aggregate and summarize results."""
    # Compile all gathered data into a structured summary
    news = state.get("news", [])
    prices = state.get("prices", {})
    resources = state.get("resources", {})
    errors = state.get("errors", [])

    # Generate summary stats
    summary_parts = []
    if news:
        summary_parts.append(f"Retrieved {len(news)} news articles.")
    if prices:
        for key, data in prices.items():
            if isinstance(data, dict) and data.get("error") is None:
                summary_parts.append(
                    f"{data.get('commodity', key)}: {data.get('price', 'N/A')}"
                )

    state["_summary"] = "; ".join(summary_parts) if summary_parts else "No data collected."
    return state


async def report_node(state: AgentState) -> AgentState:
    """Node: generate the final markdown report."""
    report = render_report(state)
    state["report"] = report

    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    from datetime import datetime

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(reports_dir, filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    state["report_path"] = report_path
    return state


def should_continue(state: AgentState) -> Literal["execution", "report"]:
    """Conditional edge: proceed to execution or skip directly to report."""
    errors = state.get("errors", [])
    fatal_errors = [e for e in errors if "Permission denied" in e]
    if fatal_errors:
        return "report"
    return "execution"


def build_graph() -> StateGraph:
    """Build and compile the agent workflow graph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("permission_check", permission_check_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("aggregation", aggregation_node)
    workflow.add_node("report", report_node)

    # Set entry point
    workflow.set_entry_point("parse_intent")

    # Define edges
    workflow.add_edge("parse_intent", "planning")
    workflow.add_edge("planning", "permission_check")

    # Conditional: if permission errors, skip execution
    workflow.add_conditional_edges(
        "permission_check",
        should_continue,
        {"execution": "execution", "report": "report"},
    )

    workflow.add_edge("execution", "aggregation")
    workflow.add_edge("aggregation", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


async def run_agent(user_query: str) -> AgentState:
    """Run the full agent pipeline."""
    graph = build_graph()
    initial_state: AgentState = {
        "user_query": user_query,
        "target": "",
        "commodity": "",
        "scope": "",
        "plan": [],
        "news": [],
        "fetch_contents": [],
        "resources": {},
        "prices": {},
        "report": "",
        "report_path": "",
        "errors": [],
    }
    result = await graph.ainvoke(initial_state)
    return result
