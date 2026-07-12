from __future__ import annotations

from typing import Any, TypedDict

from app.agents.policy import detect_locale


class SupportAgentState(TypedDict, total=False):
    ticket_id: int | None
    run_id: int | None
    subject: str
    description: str
    sanitized_description: str
    customer_email: str | None
    locale: str
    category: str | None
    priority: str | None
    risk_level: str | None
    status: str | None
    detected_injection: bool
    requires_human: bool
    requires_approval: bool
    low_confidence: bool
    customer: dict[str, Any] | None
    order: dict[str, Any] | None
    retrieved_docs: list[dict[str, Any]]
    retrieved_context: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    tool_results: dict[str, Any]
    planned_actions: list[dict[str, Any]]
    pending_actions: list[dict[str, Any]]
    draft_response: str | None
    final_response: str | None
    error: str | None
    errors: list[str]
    guardrail_flags: list[str]
    agents_run: list[str]
    events: list[dict[str, Any]]


def initial_langgraph_state(
    *,
    ticket_id: int,
    run_id: int,
    subject: str,
    description: str,
    customer_email: str | None,
) -> SupportAgentState:
    return SupportAgentState(
        ticket_id=ticket_id,
        run_id=run_id,
        subject=subject,
        description=description,
        sanitized_description=description,
        customer_email=customer_email.lower() if customer_email else None,
        locale=detect_locale(subject, description),
        category=None,
        priority="normal",
        risk_level="low",
        status="open",
        detected_injection=False,
        requires_human=False,
        requires_approval=False,
        low_confidence=False,
        customer=None,
        order=None,
        retrieved_docs=[],
        retrieved_context=[],
        citations=[],
        tool_results={},
        planned_actions=[],
        pending_actions=[],
        draft_response=None,
        final_response=None,
        error=None,
        errors=[],
        guardrail_flags=[],
        agents_run=[],
        events=[],
    )
