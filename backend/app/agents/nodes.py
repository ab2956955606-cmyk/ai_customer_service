from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.agents.llm import MockLLMClient, get_llm_client
from app.agents.policy import (
    ACCOUNT_DELETION_TERMS,
    ADDRESS_CHANGE_TERMS,
    APPROVAL_TERMS,
    CANCEL_ORDER_TERMS,
    DOWNGRADE_TERMS,
    PROMPT_INJECTION_TERMS,
    REFUND_TERMS,
    SEVERE_PROMPT_INJECTION_TERMS,
    URGENT_TERMS,
    contains_any,
    matching_terms,
)
from app.agents.state import AgentState
from app.models import Ticket
from app.rag.retriever import retrieve
from app.serializers import action_to_dict, ticket_to_dict
from app.tools.action_tools import create_internal_task, create_pending_action, handoff_to_human
from app.tools.customer_tools import get_customer_by_email
from app.tools.order_tools import extract_order_number, get_order_by_number, search_orders_by_customer


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
    flags = matching_terms(lowered, PROMPT_INJECTION_TERMS)
    state["guardrail_flags"] = flags
    sanitized = state.get("description", "")
    for flag in flags:
        sanitized = re.sub(re.escape(flag), "[blocked instruction]", sanitized, flags=re.IGNORECASE)
    state["sanitized_description"] = sanitized
    if flags:
        state.setdefault("errors", []).append("prompt injection detected")
    if any(flag in SEVERE_PROMPT_INJECTION_TERMS for flag in flags):
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
    call_failed = False
    try:
        result = llm.classify_ticket(state["subject"], state.get("sanitized_description") or state["description"])
    except Exception as exc:
        result = MockLLMClient().classify_ticket(
            state["subject"],
            state.get("sanitized_description") or state["description"],
        )
        llm.record_fallback()
        call_failed = True
        state.setdefault("errors", []).append(f"llm triage failed: {exc}")

    state["category"] = result.get("category", "unknown")
    state["priority"] = result.get("priority", "normal")
    state["risk_level"] = result.get("risk_level", state.get("risk_level") or "low")
    state["requires_human"] = bool(state.get("requires_human") or result.get("requires_human"))
    state["requires_approval"] = bool(state.get("requires_approval") or result.get("requires_approval"))
    state["low_confidence"] = float(result.get("confidence", 0.5)) < 0.45 or state["category"] == "unknown"
    suggestion = llm.last_classification_suggestion
    if suggestion:
        output = (
            "LLM suggested "
            f"category={suggestion.get('category')}, priority={suggestion.get('priority')}, "
            f"risk={suggestion.get('risk_level')}; Python policy enforced "
            f"category={state['category']}, priority={state['priority']}, risk={state['risk_level']}."
        )
    elif call_failed:
        output = (
            "LLM triage failed; deterministic fallback enforced "
            f"category={state['category']}, priority={state['priority']}, risk={state['risk_level']}."
        )
    else:
        output = f"Classified as category={state['category']}, priority={state['priority']}, risk={state['risk_level']}."
    _set_event(
        state,
        output,
        tool_name=llm.__class__.__name__,
        status="failed" if call_failed else "completed",
    )
    return state


def risk_policy_node(state: AgentState, db: Session) -> AgentState:
    del db
    text = _text(state)
    urgent_hits = matching_terms(text, URGENT_TERMS)
    if urgent_hits:
        state["priority"] = "urgent"
        state["risk_level"] = "high"
        state["requires_human"] = True
        state["requires_approval"] = False
    if contains_any(text, APPROVAL_TERMS):
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
    if state.get("low_confidence"):
        state["draft_response"] = MockLLMClient().draft_response(state)
        _set_event(
            state,
            "Low-confidence route produced a deterministic clarification question.",
            tool_name="deterministic_clarification",
            citations=state.get("citations", []),
        )
        return state

    llm = get_llm_client()
    call_failed = False
    try:
        state["draft_response"] = llm.draft_response(state)
    except Exception as exc:
        llm.record_fallback()
        call_failed = True
        state.setdefault("errors", []).append(f"llm draft failed: {exc}")
        state["draft_response"] = MockLLMClient().draft_response(state)
    _set_event(
        state,
        "LLM draft failed; deterministic fallback response created." if call_failed else "Draft response created.",
        tool_name=llm.__class__.__name__,
        citations=state.get("citations", []),
        status="failed" if call_failed else "completed",
    )
    return state


def _primary_order(state: AgentState) -> dict[str, Any] | None:
    tool_results = state.get("tool_results", {})
    if tool_results.get("order"):
        return tool_results["order"]
    orders = tool_results.get("orders") or []
    return orders[0] if orders else None


def _extract_address(text: str) -> str:
    patterns = [
        r"(?:to|address is|new address is)\s+(.+)",
        r"(?:收货地址(?:改为|修改为|更改为|是|为)|改为|修改为|更改为|新地址(?:是|为)?)[:：]?\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(".。")
    return "Address supplied in customer ticket"


def action_planner_node(state: AgentState, db: Session) -> AgentState:
    del db
    text = _text(state)
    planned: list[dict[str, Any]] = []
    order = _primary_order(state)

    if contains_any(text, REFUND_TERMS):
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
    if contains_any(text, CANCEL_ORDER_TERMS):
        planned.append(
            {
                "action_type": "cancel_order",
                "risk_level": "medium",
                "payload": {"order_id": order["id"] if order else None, "reason": state.get("subject")},
            }
        )
    if contains_any(text, ADDRESS_CHANGE_TERMS):
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
    if contains_any(text, DOWNGRADE_TERMS):
        planned.append(
            {
                "action_type": "create_internal_task",
                "risk_level": "medium",
                "payload": {
                    "title": "审核套餐降级请求" if state.get("locale") == "zh" else "Review plan downgrade request",
                    "priority": "medium",
                },
            }
        )
    if contains_any(text, ACCOUNT_DELETION_TERMS):
        planned.append(
            {
                "action_type": "create_internal_task",
                "risk_level": "medium",
                "payload": {
                    "title": "审核账户删除请求" if state.get("locale") == "zh" else "Review account deletion request",
                    "priority": "medium",
                },
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
    locale = state.get("locale", "en")
    reason = (
        "工单包含欺诈、法律、账户安全或提示注入等高风险信号"
        if locale == "zh"
        else "high-risk fraud, legal, safety, account compromise, or prompt-injection signal"
    )
    ticket = handoff_to_human(db, int(state["ticket_id"]), reason, locale=locale)
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
            "感谢您提供信息。该工单涉及高风险情况，人工客服专员将尽快审查并与您联系。"
            if state.get("locale") == "zh"
            else "Thanks for the details. A human support specialist will review this high-risk case."
        )
    elif any(action.get("status") == "pending" for action in state.get("pending_actions", [])):
        ticket.status = "pending_approval"
        if state.get("locale") == "zh":
            state["final_response"] = (
                state.get("draft_response") or "我已找到相关政策。"
            ) + " 在执行任何账户、订单或付款变更前，系统已创建待审批操作。"
        else:
            state["final_response"] = (
                state.get("draft_response") or "I found the relevant policy."
            ) + " I created a pending approval before any account, order, or payment change is executed."
    elif state.get("low_confidence"):
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
