from __future__ import annotations

from typing import Any, TypedDict

from app.agents.policy import detect_locale


class AgentState(TypedDict, total=False):
    ticket_id: int | None
    subject: str
    description: str
    sanitized_description: str
    customer_email: str | None
    locale: str
    category: str | None
    priority: str | None
    risk_level: str | None
    requires_human: bool
    requires_approval: bool
    low_confidence: bool
    retrieved_context: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    tool_results: dict[str, Any]
    planned_actions: list[dict[str, Any]]
    pending_actions: list[dict[str, Any]]
    draft_response: str | None
    final_response: str | None
    agents_run: list[str]
    events: list[dict[str, Any]]
    errors: list[str]
    guardrail_flags: list[str]
    _event: dict[str, Any]


def initial_state(subject: str, description: str, customer_email: str | None) -> AgentState:
    return AgentState(
        ticket_id=None,
        subject=subject,
        description=description,
        sanitized_description=description,
        customer_email=customer_email.lower() if customer_email else None,
        locale=detect_locale(subject, description),
        category=None,
        priority=None,
        risk_level="low",
        requires_human=False,
        requires_approval=False,
        low_confidence=False,
        retrieved_context=[],
        citations=[],
        tool_results={},
        planned_actions=[],
        pending_actions=[],
        draft_response=None,
        final_response=None,
        agents_run=[],
        events=[],
        errors=[],
        guardrail_flags=[],
    )
