from __future__ import annotations

import time
from app.models import AgentEvent, AgentRun, Ticket, utc_now
from typing import Callable

from sqlalchemy.orm import Session

from app.agents.nodes import (
    action_planner_node,
    approval_gate_node,
    customer_lookup_node,
    finalize_node,
    human_escalation_node,
    injection_guard_node,
    intake_node,
    order_lookup_node,
    rag_retrieval_node,
    response_drafter_node,
    risk_policy_node,
    triage_agent_node,
)
from app.agents.state import AgentState, initial_state
from app.serializers import action_to_dict, event_to_dict, run_to_dict, ticket_to_dict


NodeFn = Callable[[AgentState, Session], AgentState]


NODE_MAP: dict[str, NodeFn] = {
    "intake_node": intake_node,
    "injection_guard_node": injection_guard_node,
    "triage_agent_node": triage_agent_node,
    "risk_policy_node": risk_policy_node,
    "customer_lookup_node": customer_lookup_node,
    "order_lookup_node": order_lookup_node,
    "rag_retrieval_node": rag_retrieval_node,
    "response_drafter_node": response_drafter_node,
    "action_planner_node": action_planner_node,
    "approval_gate_node": approval_gate_node,
    "human_escalation_node": human_escalation_node,
    "finalize_node": finalize_node,
}


def _input_summary(state: AgentState) -> str:
    return (
        f"ticket_id={state.get('ticket_id')}, category={state.get('category')}, "
        f"priority={state.get('priority')}, risk={state.get('risk_level')}, "
        f"approval={state.get('requires_approval')}, human={state.get('requires_human')}"
    )


def _run_node(name: str, state: AgentState, db: Session) -> AgentState:
    started = time.perf_counter()
    input_summary = _input_summary(state)
    state.pop("_event", None)
    status = "completed"
    try:
        state = NODE_MAP[name](state, db)
    except Exception as exc:
        status = "failed"
        state.setdefault("errors", []).append(f"{name}: {exc}")
        ticket_id = state.get("ticket_id")
        if ticket_id:
            ticket = db.get(Ticket, int(ticket_id))
            if ticket:
                ticket.status = "failed"
                ticket.final_response = "The workflow failed while processing this ticket."
                db.commit()
        state["_event"] = {
            "output_summary": f"Node failed: {exc}",
            "status": "failed",
            "event_type": "error",
            "tool_name": None,
            "citations": [],
        }
    latency = round((time.perf_counter() - started) * 1000)
    event = state.get("_event", {})
    state.setdefault("agents_run", []).append(name)
    state.setdefault("events", []).append(
        {
            "step_index": len(state["events"]) + 1,
            "node_name": name,
            "event_type": event.get("event_type", "node"),
            "status": event.get("status", status),
            "input_summary": input_summary,
            "output_summary": event.get("output_summary", "Node completed."),
            "tool_name": event.get("tool_name"),
            "citations": event.get("citations", []),
            "latency_ms": latency,
        }
    )
    return state


def _planned_sequence(state: AgentState) -> list[str]:
    if state.get("requires_human"):
        return ["human_escalation_node", "finalize_node"]
    return [
        "customer_lookup_node",
        "order_lookup_node",
        "rag_retrieval_node",
        "response_drafter_node",
        "action_planner_node",
        "approval_gate_node",
        "finalize_node",
    ]


def run_ticket_workflow(
    db: Session,
    subject: str,
    description: str,
    customer_email: str | None = None,
    ticket_id: int | None = None,
) -> dict:
    state = initial_state(subject=subject, description=description, customer_email=customer_email)
    if ticket_id is not None:
        state["ticket_id"] = ticket_id
    started_at = utc_now()
    graph_prefix = ["intake_node", "injection_guard_node", "triage_agent_node", "risk_policy_node"]

    for node_name in graph_prefix:
        state = _run_node(node_name, state, db)

    for node_name in _planned_sequence(state):
        state = _run_node(node_name, state, db)

    total_latency_ms = sum(event["latency_ms"] for event in state["events"])
    run = AgentRun(
        ticket_id=int(state["ticket_id"]),
        status="failed" if state.get("errors") and not state.get("final_response") else "completed",
        started_at=started_at,
        completed_at=utc_now(),
        agents_run=state["agents_run"],
        total_latency_ms=total_latency_ms,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    persisted_events: list[AgentEvent] = []
    for event in state["events"]:
        persisted = AgentEvent(
            run_id=run.id,
            ticket_id=int(state["ticket_id"]),
            **event,
        )
        db.add(persisted)
        persisted_events.append(persisted)
    db.commit()
    for event in persisted_events:
        db.refresh(event)

    ticket = db.get(Ticket, int(state["ticket_id"]))
    pending = ticket.pending_actions if ticket else []
    return {
        "ticket": ticket_to_dict(ticket),
        "agent_run": run_to_dict(run),
        "agents_run": state["agents_run"],
        "events": [event_to_dict(event) for event in persisted_events],
        "pending_actions": [action_to_dict(action) for action in pending],
        "final_response": state.get("final_response"),
        "citations": state.get("citations", []),
        "state": state,
    }
