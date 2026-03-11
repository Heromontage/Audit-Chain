"""
AuditChain — LangGraph Agent State Schema

Defines the single ``AgentState`` TypedDict that flows through every
node in the LangGraph execution graph:

    planner → tool_executor → audit_logger → reasoner → (loop | reporter) → END

Every field is populated progressively as the agent loop iterates.
``weilchain_tx_hashes`` accumulates on-chain proof for every logged step.
"""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    """Typed state dictionary shared across all LangGraph nodes.

    Attributes
    ----------
    session_id:
        Unique identifier for this audit session.
    query:
        The original natural-language Web3 due-diligence query.
    planned_steps:
        Ordered list of steps the planner decomposed the query into.
        Each entry: ``{step_type, description, tool_name, tool_args}``.
    current_step_index:
        Zero-based index of the step currently being executed.
    tool_results:
        Accumulated results from each tool invocation.
    audit_logs:
        Full audit-log entries that were sent to WeilChain.
    weilchain_tx_hashes:
        On-chain transaction hashes returned by ``audit_client.log()``.
        Serves as immutable, verifiable proof of every agent action.
    llm_reasoning_history:
        Reasoning strings produced by the reasoner node at each
        iteration of the agent loop.
    final_report:
        The structured due-diligence report produced by the reporter
        node, or ``None`` if the agent hasn't finished yet.
    is_complete:
        ``True`` once the reasoner or reporter decides no more steps
        are needed.
    error:
        A human-readable error message if a fatal failure occurred,
        otherwise ``None``.
    """

    session_id: str
    query: str
    planned_steps: list[dict]
    current_step_index: int
    tool_results: list[dict]
    audit_logs: list[dict]
    weilchain_tx_hashes: list[str]
    llm_reasoning_history: list[str]
    final_report: dict | None
    is_complete: bool
    error: str | None