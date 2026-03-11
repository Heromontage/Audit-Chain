"""
AuditChain — LangGraph State Graph

Compiles the full agent execution graph:

    START → planner → tool_executor → audit_logger → reasoner
                ▲                                        │
                │         ┌──── is_complete=False ───────┘
                │         ▼
                └── tool_executor
                                    is_complete=True ──▶ reporter → END

The compiled ``app`` is a runnable LangGraph application.  Use the
``run_audit()`` helper for a single async call that returns the
completed ``AgentState`` including the final report and all WeilChain
transaction hashes.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    audit_logger_node,
    planner_node,
    reasoner_node,
    reporter_node,
    tool_executor_node,
)
from agent.state import AgentState

logger = logging.getLogger(__name__)

# ── Build the StateGraph ──────────────────────────────────────────────────

graph = StateGraph(AgentState)

# ── Add nodes ─────────────────────────────────────────────────────────────

graph.add_node("planner", planner_node)
graph.add_node("tool_executor", tool_executor_node)
graph.add_node("audit_logger", audit_logger_node)
graph.add_node("reasoner", reasoner_node)
graph.add_node("reporter", reporter_node)

# ── Add edges ─────────────────────────────────────────────────────────────

graph.add_edge(START, "planner")
graph.add_edge("planner", "tool_executor")
graph.add_edge("tool_executor", "audit_logger")
graph.add_edge("audit_logger", "reasoner")

# Conditional: loop back to tool_executor or proceed to reporter
graph.add_conditional_edges(
    "reasoner",
    lambda s: "reporter" if s["is_complete"] else "tool_executor",
    {
        "reporter": "reporter",
        "tool_executor": "tool_executor",
    },
)

graph.add_edge("reporter", END)

# ── Compile ───────────────────────────────────────────────────────────────

app = graph.compile()

# ── Public helper ─────────────────────────────────────────────────────────


async def run_audit(query: str, session_id: str) -> AgentState:
    """Execute a full AuditChain due-diligence session.

    Initialises a blank ``AgentState``, invokes the compiled LangGraph
    application, and returns the completed state — including the final
    report and every WeilChain ``tx_hash``.

    Parameters
    ----------
    query:
        The natural-language Web3 audit query
        (e.g. *"Audit wallet 0xABC… for rug-pull risk"*).
    session_id:
        A unique session identifier (typically ``str(uuid4())``).

    Returns
    -------
    AgentState
        The fully-populated agent state after the graph reaches ``END``.
    """
    initial_state = AgentState(
        session_id=session_id,
        query=query,
        planned_steps=[],
        current_step_index=0,
        tool_results=[],
        audit_logs=[],
        weilchain_tx_hashes=[],
        llm_reasoning_history=[],
        final_report=None,
        is_complete=False,
        error=None,
    )

    logger.info("Starting audit  ▸ session=%s  query=%s", session_id, query[:120])

    result: AgentState = await app.ainvoke(initial_state)  # type: ignore[assignment]

    logger.info(
        "Audit complete  ▸ session=%s  steps=%d  risk=%s",
        session_id,
        len(result.get("weilchain_tx_hashes", [])),
        (result.get("final_report") or {}).get("risk_level", "N/A"),
    )

    return result