from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.agents.llm import URGENT_TERMS, get_llm_client
from app.agents.state import AgentState
from app.models import Ticket
from app.rag.retriever import retrieve
from app.serializers import action_to_dict, ticket_to_dict
from app.tools.action_tools import create_internal_task, create_pending_action, handoff_to_human
from app.tools.customer_tools import get_customer_by_email
from app.tools.order_tools import extract_order_number, get_order_by_number, search_orders_by_customer


PROMPT_INJECTION_TERMS = [
    "ignore previous instructions",
    "reveal system prompt",
    "bypass approval",
    "execute refund without approval",
    "delete all data",
]

ACTION_KEYWORDS = {
    "refund": "create_refund_request",
    "money back": "create_refund_request",
    "cancel order": "cancel_order",
    "change address": "update_shipping_address",
    "update address": "update_shipping_address",
    "shipping address": "update_shipping_address",
    "account deletion": "handoff_to_human",
    "delete my account": "handoff_to_human",
    "downgrade": "create_internal_task",
}


def _text(state: AgentState) -> str:
    return f"{state.get('subject', '')} {state.get('sanitized_description') or state.get('description', '')}".lower()


def _set_event(
    state: AgentState,
    output: str,
    tool_name: str | None = None,
    citations: list[dict] | None = None,
    event_type: str = "node",
    status: str = "completed",
) -> None:
    state["_event"] = {
        "output_summary": output[:1000],
        "tool_name": tool_name,
        "citations": citations or [],
        "event_type": event_type,
        "status": status,
    }


def intake_node(state: AgentState, db: Session) -> AgentState:
    ticket = db.get(Ticket, int(state["ticket_id"])) if state.get("ticket_id") else None
    if ticket is None:
        ticket = Ticket(
            subject=state["subject"],
            description=state["description"],
            customer_email=state.get("customer_email"),
            category="unknown",
            priority="normal",
            risk_level="low",
            status="processing",
            assigned_agent="supportops-agent",
        )
        db.add(ticket)
    else:
        ticket.status = "processing"
        ticket.assigned_agent = ticket.assigned_agent or "supportops-agent"
    db.commit()
    db.refresh(ticket)
    state["ticket_id"] = ticket.id
    state.setdefault("tool_results", {})["ticket"] = ticket_to_dict(ticket)
    _set_event(state, f"Ticket {ticket.id} accepted and moved to processing.")
    return state


def injection_guard_node(state: AgentState, db: Session) -> AgentState:
    del db
    original = f"{state.get('subject', '')} {state.get('description', '')}"
    lowered = original.lower()
    flags = [term for term in PROMPT_INJECTION_TERMS if term in lowered]
    state["guardrail_flags"] = flags
    sanitized = state.get("description", "")
    for flag in flags:
        sanitized = re.sub(re.escape(flag), "[blocked instruction]", sanitized, flags=re.IGNORECASE)
    state["sanitized_description"] = sanitized
    if flags:
        state.setdefault("errors", []).append("prompt injection detected")
    if any(flag in {"delete all data", "bypass approval", "execute refund without approval", "reveal system prompt"} for flag in flags):
        state["requires_human"] = True
        state["risk_level"] = "high"
        state["priority"] = "urgent"
    _set_event(
        state,
        "Prompt injection scan completed; "
        + (f"blocked terms: {', '.join(flags)}." if flags else "no injection terms detected."),
        event_type="guardrail",
    )
    return state


def triage_agent_node(state: AgentState, db: Session) -> AgentState:
    del db
    llm = get_llm_client()
    try:
        result = llm.classify_ticket(state["subject"], state.get("sanitized_description") or state["description"])
    except Exception as exc:
        result = {"category": "unknown", "priority": "normal", "risk_level": "low", "confidence": 0.0}
        state.setdefault("errors", []).append(f"llm triage failed: {exc}")

    state["category"] = result.get("category", "unknown")
    state["priority"] = result.get("priority", "normal")
    state["risk_level"] = result.get("risk_level", state.get("risk_level") or "low")
    state["requires_human"] = bool(state.get("requires_human") or result.get("requires_human"))
    state["requires_approval"] = bool(state.get("requires_approval") or result.get("requires_approval"))
    state["low_confidence"] = float(result.get("confidence", 0.5)) < 0.45 or state["category"] == "unknown"
    _set_event(
        state,
        f"Classified as category={state['category']}, priority={state['priority']}, risk={state['risk_level']}.",
        tool_name="MockLLMClient" if llm.__class__.__name__ == "MockLLMClient" else llm.__class__.__name__,
    )
    return state


def risk_policy_node(state: AgentState, db: Session) -> AgentState:
    del db
    text = _text(state)
    urgent_hits = sorted(term for term in URGENT_TERMS if term in text)
    if urgent_hits:
        state["priority"] = "urgent"
        state["risk_level"] = "high"
        state["requires_human"] = True
        state["requires_approval"] = False
    if any(term in text for term in ["refund", "cancel order", "change address", "update address", "shipping address", "account deletion", "delete my account", "downgrade"]):
        if not state.get("requires_human"):
            state["requires_approval"] = True
            state["risk_level"] = "medium"
    _set_event(
        state,
        "Python policy enforced. "
        + (f"Urgent terms: {', '.join(urgent_hits)}." if urgent_hits else "No urgent fraud/legal terms found."),
    )
    return state


def customer_lookup_node(state: AgentState, db: Session) -> AgentState:
    customer = get_customer_by_email(db, state.get("customer_email"))
    state.setdefault("tool_results", {})["customer"] = customer
    _set_event(
        state,
        "Customer lookup completed." if customer else "No matching customer found.",
        tool_name="get_customer_by_email",
    )
    return state


def order_lookup_node(state: AgentState, db: Session) -> AgentState:
    text = _text(state)
    order_number = extract_order_number(text)
    order = get_order_by_number(db, order_number)
    orders = [] if order else search_orders_by_customer(db, state.get("customer_email"))
    state.setdefault("tool_results", {})["order"] = order
    state.setdefault("tool_results", {})["orders"] = orders
    summary = f"Found order {order['order_number']}." if order else f"Found {len(orders)} recent order(s)."
    _set_event(state, summary, tool_name="get_order_by_number" if order_number else "search_orders_by_customer")
    return state


def rag_retrieval_node(state: AgentState, db: Session) -> AgentState:
    query = f"{state.get('subject')} {state.get('sanitized_description') or state.get('description')}"
    citations = retrieve(db, query, limit=3)
    state["retrieved_context"] = citations
    state["citations"] = citations
    if not citations:
        state["low_confidence"] = True
    _set_event(state, f"Retrieved {len(citations)} knowledge citation(s).", tool_name="keyword_retriever", citations=citations)
    return state


def response_drafter_node(state: AgentState, db: Session) -> AgentState:
    del db
    llm = get_llm_client()
    try:
        state["draft_response"] = llm.draft_response(state)
    except Exception as exc:
        state.setdefault("errors", []).append(f"llm draft failed: {exc}")
        state["draft_response"] = "Thanks for contacting support. A teammate will review this request."
    _set_event(state, "Draft response created.", tool_name=llm.__class__.__name__, citations=state.get("citations", []))
    return state


def _primary_order(state: AgentState) -> dict[str, Any] | None:
    tool_results = state.get("tool_results", {})
    if tool_results.get("order"):
        return tool_results["order"]
    orders = tool_results.get("orders") or []
    return orders[0] if orders else None


def _extract_address(text: str) -> str:
    match = re.search(r"(?:to|address is|new address is)\s+(.+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(".")
    return "Address supplied in customer ticket"


def action_planner_node(state: AgentState, db: Session) -> AgentState:
    del db
    text = _text(state)
    planned: list[dict[str, Any]] = []
    order = _primary_order(state)

    if "refund" in text or "money back" in text:
        planned.append(
            {
                "action_type": "create_refund_request",
                "risk_level": "medium",
                "payload": {
                    "order_id": order["id"] if order else None,
                    "amount": order["amount"] if order else None,
                    "reason": state.get("subject"),
                },
            }
        )
    if "cancel order" in text:
        planned.append(
            {
                "action_type": "cancel_order",
                "risk_level": "medium",
                "payload": {"order_id": order["id"] if order else None, "reason": state.get("subject")},
            }
        )
    if "change address" in text or "update address" in text or "shipping address" in text:
        planned.append(
            {
                "action_type": "update_shipping_address",
                "risk_level": "medium",
                "payload": {
                    "order_id": order["id"] if order else None,
                    "new_address": _extract_address(state.get("description", "")),
                },
            }
        )
    if "downgrade" in text:
        planned.append(
            {
                "action_type": "create_internal_task",
                "risk_level": "medium",
                "payload": {"title": "Review plan downgrade request", "priority": "medium"},
            }
        )

    state["planned_actions"] = planned
    if planned:
        state["requires_approval"] = True
    _set_event(state, f"Planned {len(planned)} action(s).", tool_name="action_policy_planner")
    return state


def approval_gate_node(state: AgentState, db: Session) -> AgentState:
    pending = []
    if state.get("requires_human"):
        _set_event(state, "Human route selected; approval gate skipped.")
        return state

    for action in state.get("planned_actions", []):
        payload = action.get("payload", {})
        action_type = action["action_type"]
        if action_type == "create_internal_task":
            created = create_pending_action(
                db,
                ticket_id=int(state["ticket_id"]),
                action_type="create_internal_task",
                payload=payload,
                risk_level=action.get("risk_level", "medium"),
                status="pending" if action.get("risk_level") in {"medium", "high", "urgent"} else "executed",
            )
        else:
            created = create_pending_action(
                db,
                ticket_id=int(state["ticket_id"]),
                action_type=action_type,
                payload=payload,
                risk_level=action.get("risk_level", "medium"),
            )
        pending.append(action_to_dict(created))

    state["pending_actions"] = pending
    ticket = db.get(Ticket, int(state["ticket_id"]))
    if ticket:
        if any(action["status"] == "pending" for action in pending):
            ticket.status = "pending_approval"
        else:
            ticket.status = "resolved"
        db.commit()
    _set_event(state, f"Approval gate created {len(pending)} queued action(s).", tool_name="create_pending_action")
    return state


def human_escalation_node(state: AgentState, db: Session) -> AgentState:
    reason = "high-risk fraud, legal, safety, account compromise, or prompt-injection signal"
    ticket = handoff_to_human(db, int(state["ticket_id"]), reason)
    state["final_response"] = ticket.final_response
    state["risk_level"] = "high"
    state["priority"] = "urgent"
    _set_event(state, "Ticket escalated to a human specialist.", tool_name="handoff_to_human")
    return state


def finalize_node(state: AgentState, db: Session) -> AgentState:
    ticket = db.get(Ticket, int(state["ticket_id"]))
    if ticket is None:
        raise ValueError("Ticket not found during finalize")

    ticket.category = state.get("category") or ticket.category
    ticket.priority = state.get("priority") or ticket.priority
    ticket.risk_level = state.get("risk_level") or ticket.risk_level

    if state.get("requires_human"):
        ticket.status = "escalated"
        state["final_response"] = state.get("final_response") or (
            "Thanks for the details. A human support specialist will review this high-risk case."
        )
    elif any(action.get("status") == "pending" for action in state.get("pending_actions", [])):
        ticket.status = "pending_approval"
        state["final_response"] = (
            state.get("draft_response")
            or "I found the relevant policy."
        ) + " I created a pending approval before any account, order, or payment change is executed."
    elif state.get("low_confidence") and not state.get("citations"):
        ticket.status = "open"
        state["final_response"] = state.get("draft_response")
    else:
        ticket.status = "resolved"
        state["final_response"] = state.get("draft_response")

    ticket.final_response = state.get("final_response")
    db.commit()
    db.refresh(ticket)
    state.setdefault("tool_results", {})["ticket"] = ticket_to_dict(ticket)
    _set_event(state, f"Ticket finalized with status={ticket.status}.", citations=state.get("citations", []))
    return state
