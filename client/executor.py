"""
Tool Executor

Handles calling MCP tools with permission validation.
Supports both direct MCP client calls and local function calls for testing.
"""

import asyncio
from typing import Any

from .permissions import PermissionManager
from .state import AgentState

# Import MCP server tool functions for direct invocation (no MCP transport needed)
# This allows the agent to call tools directly in the same process.


async def execute_plan(
    state: AgentState,
    perm_manager: PermissionManager | None = None,
) -> AgentState:
    """Execute all phases of the plan, respecting dependencies and permissions."""
    plan = state.get("plan", [])
    if not plan:
        state["errors"] = state.get("errors", []) + ["No plan to execute"]
        return state

    if perm_manager is None:
        perm_manager = PermissionManager()

    results: dict[str, Any] = {}
    errors: list[str] = list(state.get("errors", []))

    phases = sorted(set(p["phase"] for p in plan))
    for phase in phases:
        phase_tasks = [p for p in plan if p["phase"] == phase]

        # Check dependencies are satisfied
        for task in phase_tasks:
            for dep in task.get("depends_on", []):
                if dep not in results:
                    errors.append(f"Dependency '{dep}' not satisfied for '{task['tool']}'")

        # Execute phase tasks concurrently
        tasks = [_execute_tool(task, state, results, perm_manager) for task in phase_tasks]
        phase_results = await asyncio.gather(*tasks, return_exceptions=True)

        for task, result in zip(phase_tasks, phase_results):
            tool_name = task["tool"]
            if isinstance(result, Exception):
                if not task.get("optional"):
                    errors.append(f"Tool '{tool_name}' failed: {result}")
            elif isinstance(result, dict) and result.get("error"):
                if not task.get("optional"):
                    errors.append(f"Tool '{tool_name}' failed: {result['error']}")
                results[tool_name] = result
            else:
                results[tool_name] = result

        # Sync results to state after each phase so subsequent phases can reference them
        _sync_results_to_state(state, results)
    if "search_news" in results:
        state["news"] = results["search_news"] or []
    if "fetch_article" in results:
        state["fetch_contents"] = (
            results["fetch_article"] if isinstance(results["fetch_article"], list)
            else [results["fetch_article"]]
        )
    if "extract_resources" in results:
        state["resources"] = results["extract_resources"]
    if "get_price" in results:
        state["prices"] = state.get("prices", {})
        state["prices"]["current"] = results["get_price"]
    if "get_trend" in results:
        state["prices"] = state.get("prices", {})
        state["prices"]["trend"] = results["get_trend"]

    state["errors"] = errors
    return state


def _sync_results_to_state(state: AgentState, results: dict[str, Any]) -> None:
    """Map tool results to state keys so subsequent phases can resolve templates."""
    if "search_news" in results:
        state["news"] = results["search_news"] or []
    if "fetch_article" in results:
        state["fetch_contents"] = (
            results["fetch_article"] if isinstance(results["fetch_article"], list)
            else [results["fetch_article"]]
        )
    if "extract_resources" in results:
        state["resources"] = results["extract_resources"]
    if "get_price" in results:
        state["prices"] = state.get("prices", {})
        state["prices"]["current"] = results["get_price"]
    if "get_trend" in results:
        state["prices"] = state.get("prices", {})
        state["prices"]["trend"] = results["get_trend"]


async def _execute_tool(
    task: dict,
    state: AgentState,
    results: dict,
    perm_manager: PermissionManager,
) -> Any:
    """Execute a single tool call with permission validation."""
    tool_name = task["tool"]
    params = dict(task.get("params", {}))
    server_name = task.get("server", "")

    # Resolve template params from previous results
    for key, value in params.items():
        if isinstance(value, str) and "{{" in value:
            params[key] = _resolve_template(value, results, state)

    # Reject if conditional task with no data
    if task.get("conditional"):
        resolved = _resolve_condition(task, results, state)
        if not resolved:
            return None

    # Permission validation
    perm_manager.validate_tool_call(tool_name, "executor", params)
    perm_manager.validate_resource_limits(tool_name, params)

    # If URL param present, validate URL (skip unresolved templates)
    if "url" in params and "{{" not in str(params["url"]):
        perm_manager.validate_url(params["url"])
    if "pdf_url" in params and "{{" not in str(params["pdf_url"]):
        perm_manager.validate_url(params["pdf_url"])

    # Call the actual tool
    result = await _call_mcp_tool(server_name, tool_name, params)
    return result


async def _call_mcp_tool(server_name: str, tool_name: str, params: dict) -> Any:
    """Call an MCP tool directly by importing the server module."""
    try:
        if server_name == "mining-news":
            from servers.mining_news.server import fetch_article, search_news

            if tool_name == "search_news":
                return await search_news(**params)
            elif tool_name == "fetch_article":
                return await fetch_article(**params)

        elif server_name == "mineral-pdf":
            from servers.mineral_pdf.server import extract_resources

            if tool_name == "extract_resources":
                return await extract_resources(**params)

        elif server_name == "lme-price":
            from servers.lme_price.server import get_price, get_trend, list_commodities

            if tool_name == "get_price":
                return await get_price(**params)
            elif tool_name == "get_trend":
                return await get_trend(**params)
            elif tool_name == "list_commodities":
                return await list_commodities()

        return {"error": f"Unknown tool: {server_name}/{tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def _resolve_template(template: str, results: dict, state: AgentState) -> Any:
    """Resolve template strings like '{{news[0].url}}'."""
    import re

    match = re.search(r"\{\{(.+?)\}\}", template)
    if not match:
        return template

    path = match.group(1).strip()
    parts = path.split(".")
    current: Any = None

    # Handle first part (may include [index] like "news[0]")
    first = parts[0]
    first_idx = None
    if "[" in first and first.endswith("]"):
        first, idx_str = first[:-1].split("[")
        if idx_str.isdigit():
            first_idx = int(idx_str)

    # Look up the root name in results or state
    if first in results:
        current = results[first]
    elif first in state:
        current = state[first]
    else:
        return template

    # Apply index on root if present
    if first_idx is not None and isinstance(current, list):
        try:
            current = current[first_idx]
        except IndexError:
            return template

    # Handle remaining parts
    for part in parts[1:]:
        if "[" in part and part.endswith("]"):
            name, idx_str = part[:-1].split("[")
            if isinstance(current, dict):
                current = current.get(name, [])
            if isinstance(current, list) and idx_str.isdigit():
                try:
                    current = current[int(idx_str)]
                except IndexError:
                    return template
        elif isinstance(current, dict):
            current = current.get(part, current)
        else:
            return template

    return current


def _resolve_condition(task: dict, results: dict, state: AgentState) -> bool:
    """Check if a conditional task should run."""
    for dep in task.get("depends_on", []):
        data = results.get(dep) or state.get(dep)
        if not data:
            return False
        if isinstance(data, list) and len(data) == 0:
            return False
    return True
