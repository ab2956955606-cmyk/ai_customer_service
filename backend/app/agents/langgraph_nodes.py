from __future__ import annotations

import time
from contextvars import ContextVar
from typing import Callable

from sqlalchemy.orm import Session

from app.agents.nodes import (
    action_planner_node as custom_action_planner_node,
    approval_gate_node as custom_approval_gate_node,
    customer_lookup_node as custom_customer_lookup_node,
    finalize_node as custom_finalize_node,
    human_escalation_node as custom_human_escalation_node,
    injection_guard_node as custom_injection_guard_node,
    intake_node as custom_intake_node,
    order_lookup_node as custom_order_lookup_node,
    rag_retrieval_node as custom_rag_retrieval_node,
    response_drafter_node as custom_response_drafter_node,
    risk_policy_node as custom_risk_policy_node,
    triage_agent_node as custom_triage_agent_node,
)
from app.agents.state import AgentState
from app.agents.langgraph_state import SupportAgentState
from app.models import Ticket


_current_db: ContextVar[Session] = ContextVar("langgraph_support_db")


CustomNode = Callable[[AgentState, Session], AgentState]


def bind_db(db: Session):
    return _current_db.set(db)


def reset_db(token) -> None:
    _current_db.reset(token)


def _db() -> Session:
    return _current_db.get()


def _input_summary(state: SupportAgentState) -> str:
    return (
        f"ticket_id={state.get('ticket_id')}, category={state.get('category')}, "
        f"priority={state.get('priority')}, risk={state.get('risk_level')}, "
        f"approval={state.get('requires_approval')}, human={state.get('requires_human')}"
    )


def _sync_aliases(state: AgentState) -> None:
    tool_results = state.setdefault("tool_results", {})
    state["detected_injection"] = bool(state.get("guardrail_flags"))
    state["customer"] = tool_results.get("customer")
    state["order"] = tool_results.get("order")
    state["retrieved_docs"] = state.get("retrieved_context") or state.get("citations", [])
    if state.get("errors"):
        state["error"] = "; ".join(state["errors"])
    ticket_id = state.get("ticket_id")
    if ticket_id:
        ticket = _db().get(Ticket, int(ticket_id))
        if ticket:
            state["status"] = ticket.status


def _changed(before: SupportAgentState, after: AgentState) -> dict:
    ignored = {"_event"}
    updates = {}
    for key, value in after.items():
        if key in ignored:
            continue
        if before.get(key) != value:
            updates[key] = value
    return updates


def _run(name: str, node: CustomNode, state: SupportAgentState) -> dict:
    started = time.perf_counter()
    input_summary = _input_summary(state)
    working: AgentState = AgentState(**dict(state))
    working.pop("_event", None)
    status = "completed"
    try:
        working = node(working, _db())
    except Exception as exc:
        status = "failed"
        working.setdefault("errors", []).append(f"{name}: {exc}")
        working["error"] = str(exc)
        working["requires_human"] = True
        working["_event"] = {
            "output_summary": f"Node failed: {exc}",
            "status": "failed",
            "event_type": "error",
            "tool_name": None,
            "citations": [],
        }

    latency = round((time.perf_counter() - started) * 1000)
    event = working.get("_event", {})
    trace_event = {
        "step_index": len(state.get("events", [])) + 1,
        "node_name": name,
        "event_type": event.get("event_type", "node"),
        "status": event.get("status", status),
        "input_summary": input_summary,
        "output_summary": event.get("output_summary", "Node completed."),
        "tool_name": event.get("tool_name"),
        "citations": event.get("citations", []),
        "latency_ms": latency,
    }
    working["events"] = [*state.get("events", []), trace_event]
    working["agents_run"] = [*state.get("agents_run", []), name]
    _sync_aliases(working)
    return _changed(state, working)


def intake(state: SupportAgentState) -> dict:
    return _run("intake", custom_intake_node, state)


def injection_guard(state: SupportAgentState) -> dict:
    return _run("injection_guard", custom_injection_guard_node, state)


def triage(state: SupportAgentState) -> dict:
    return _run("triage", custom_triage_agent_node, state)


def risk_policy(state: SupportAgentState) -> dict:
    return _run("risk_policy", custom_risk_policy_node, state)


def customer_lookup(state: SupportAgentState) -> dict:
    return _run("customer_lookup", custom_customer_lookup_node, state)


def order_lookup(state: SupportAgentState) -> dict:
    return _run("order_lookup", custom_order_lookup_node, state)


def rag_retrieval(state: SupportAgentState) -> dict:
    return _run("rag_retrieval", custom_rag_retrieval_node, state)


def response_drafter(state: SupportAgentState) -> dict:
    return _run("response_drafter", custom_response_drafter_node, state)


def action_planner(state: SupportAgentState) -> dict:
    return _run("action_planner", custom_action_planner_node, state)


def approval_gate(state: SupportAgentState) -> dict:
    return _run("approval_gate", custom_approval_gate_node, state)


def human_escalation(state: SupportAgentState) -> dict:
    return _run("human_escalation", custom_human_escalation_node, state)


def finalize(state: SupportAgentState) -> dict:
    return _run("finalize", custom_finalize_node, state)
