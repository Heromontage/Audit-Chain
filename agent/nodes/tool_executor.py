"""
AuditChain — Tool Executor Node

Executes the current ``tool_call`` step by connecting to the Web3 MCP
Tools server via ``langchain-mcp-adapters`` ``MultiServerMCPClient``.

The node:
1. Reads the current step from ``planned_steps[current_step_index]``
2. Spins up a stdio connection to ``mcp_applets/web3_tools_server.py``
3. Finds the matching tool by name and invokes it
4. Stores the result (or error) in ``state["tool_results"]``
5. Never raises — errors are captured and stored gracefully
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.state import AgentState

logger = logging.getLogger(__name__)

# ── MCP Server Configuration ─────────────────────────────────────────────

MCP_SERVER_CONFIG: dict[str, dict[str, Any]] = {
    "web3_tools": {
        "transport": "stdio",
        "command": "python",
        "args": ["mcp_applets/web3_tools_server.py"],
    },
}


async def tool_executor_node(state: AgentState) -> AgentState:
    """Execute the current planned step's MCP tool call.

    If the current step is ``llm_reasoning`` rather than ``tool_call``,
    the node records a no-op result and returns immediately.

    Parameters
    ----------
    state:
        Current agent state.  Must have ``planned_steps`` and
        ``current_step_index`` already set by the planner.

    Returns
    -------
    AgentState
        Updated state with a new entry appended to ``tool_results``.
    """
    step_index: int = state["current_step_index"]
    planned_steps: list[dict] = state["planned_steps"]

    # Guard: index out of range
    if step_index >= len(planned_steps):
        logger.warning("Step index %d out of range — skipping execution.", step_index)
        return state

    step: dict[str, Any] = planned_steps[step_index]
    step_type: str = step.get("step_type", "")
    tool_name: str | None = step.get("tool_name")
    tool_args: dict[str, Any] = step.get("tool_args", {})
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── Skip non-tool steps ───────────────────────────────────────────────

    if step_type != "tool_call" or not tool_name:
        logger.info(
            "Step %d is '%s' — no tool execution needed.", step_index, step_type
        )
        state["tool_results"].append(
            {
                "step_index": step_index,
                "tool_name": None,
                "args": {},
                "result": {"note": "LLM reasoning step — no tool invoked."},
                "error": None,
                "timestamp": timestamp,
            }
        )
        return state

    # ── Execute the MCP tool ──────────────────────────────────────────────

    result: Any = None
    error: str | None = None

    try:
        async with MultiServerMCPClient(MCP_SERVER_CONFIG) as mcp:
            tools = await mcp.get_tools()

            # Find the matching tool by name
            target_tool = None
            for tool in tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break

            if target_tool is None:
                error = f"Tool '{tool_name}' not found in MCP server."
                logger.error(error)
            else:
                logger.info(
                    "Invoking MCP tool  ▸ step=%d  tool=%s  args=%s",
                    step_index,
                    tool_name,
                    tool_args,
                )
                result = await target_tool.ainvoke(input=tool_args)

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.error(
            "Tool execution failed  ▸ step=%d  tool=%s  error=%s",
            step_index,
            tool_name,
            error,
        )

    # ── Store the result ──────────────────────────────────────────────────

    state["tool_results"].append(
        {
            "step_index": step_index,
            "tool_name": tool_name,
            "args": tool_args,
            "result": result,
            "error": error,
            "timestamp": timestamp,
        }
    )

    return state