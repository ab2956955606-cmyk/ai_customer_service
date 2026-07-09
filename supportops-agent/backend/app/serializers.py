from __future__ import annotations

from datetime import datetime
from typing import Any


def _value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def model_to_dict(model: Any, fields: list[str]) -> dict[str, Any]:
    return {field: _value(getattr(model, field)) for field in fields}


TICKET_FIELDS = [
    "id",
    "subject",
    "description",
    "customer_email",
    "category",
    "priority",
    "risk_level",
    "status",
    "assigned_agent",
    "final_response",
    "created_at",
    "updated_at",
]

AGENT_RUN_FIELDS = [
    "id",
    "ticket_id",
    "status",
    "started_at",
    "completed_at",
    "agents_run",
    "total_latency_ms",
]

AGENT_EVENT_FIELDS = [
    "id",
    "run_id",
    "ticket_id",
    "step_index",
    "node_name",
    "event_type",
    "status",
    "input_summary",
    "output_summary",
    "tool_name",
    "citations",
    "latency_ms",
    "created_at",
]

PENDING_ACTION_FIELDS = [
    "id",
    "ticket_id",
    "action_type",
    "payload_json",
    "risk_level",
    "status",
    "created_at",
    "decided_at",
]

KNOWLEDGE_FIELDS = ["id", "title", "content", "source", "created_at"]


def ticket_to_dict(model: Any) -> dict[str, Any]:
    return model_to_dict(model, TICKET_FIELDS)


def run_to_dict(model: Any) -> dict[str, Any]:
    return model_to_dict(model, AGENT_RUN_FIELDS)


def event_to_dict(model: Any) -> dict[str, Any]:
    return model_to_dict(model, AGENT_EVENT_FIELDS)


def action_to_dict(model: Any) -> dict[str, Any]:
    return model_to_dict(model, PENDING_ACTION_FIELDS)


def document_to_dict(model: Any) -> dict[str, Any]:
    return model_to_dict(model, KNOWLEDGE_FIELDS)
