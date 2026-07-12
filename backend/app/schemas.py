from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    subject: str = Field(min_length=2, max_length=240)
    description: str = Field(min_length=2)
    customer_email: str | None = None


class RagAskRequest(BaseModel):
    question: str = Field(min_length=2)


class Citation(BaseModel):
    title: str
    snippet: str
    score: float


class RagAskResponse(BaseModel):
    answer: str
    citations: list[Citation]


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    customer_email: str | None
    category: str | None
    priority: str | None
    risk_level: str | None
    status: str
    assigned_agent: str | None
    final_response: str | None
    created_at: datetime
    updated_at: datetime


class AgentRunOut(BaseModel):
    id: int
    ticket_id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    agents_run: list[str]
    total_latency_ms: int


class AgentEventOut(BaseModel):
    id: int
    run_id: int
    ticket_id: int
    step_index: int
    node_name: str
    event_type: str
    status: str
    input_summary: str | None
    output_summary: str | None
    tool_name: str | None
    citations: list[dict[str, Any]]
    latency_ms: int
    created_at: datetime


class PendingActionOut(BaseModel):
    id: int
    ticket_id: int
    action_type: str
    payload_json: dict[str, Any]
    risk_level: str
    status: str
    created_at: datetime
    decided_at: datetime | None


class TicketWorkflowResponse(BaseModel):
    ticket: dict[str, Any]
    agent_run: dict[str, Any]
    agents_run: list[str]
    events: list[dict[str, Any]]
    pending_actions: list[dict[str, Any]]
    final_response: str | None
    citations: list[dict[str, Any]]


class ApprovalDecisionResponse(BaseModel):
    action: dict[str, Any]
    ticket: dict[str, Any]


class EvalRunResponse(BaseModel):
    locale: str
    run_id: str | None
    started_at: str | None
    completed_at: str | None
    metrics: dict[str, float]
    results: list[dict[str, Any]]
    failed_cases: list[dict[str, Any]]
    llm_execution: dict[str, str | int]
