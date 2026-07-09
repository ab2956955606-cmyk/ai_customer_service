from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import PendingAction, Ticket, utc_now
from app.tools.order_tools import cancel_order, update_shipping_address


APPROVAL_REQUIRED_ACTIONS = {
    "update_shipping_address",
    "create_refund_request",
    "cancel_order",
    "account_deletion",
    "plan_downgrade",
}


def create_pending_action(
    db: Session,
    ticket_id: int,
    action_type: str,
    payload: dict,
    risk_level: str = "medium",
    status: str = "pending",
) -> PendingAction:
    action = PendingAction(
        ticket_id=ticket_id,
        action_type=action_type,
        payload_json=payload,
        risk_level=risk_level,
        status=status,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def handoff_to_human(db: Session, ticket_id: int, reason: str) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise ValueError("Ticket not found")
    ticket.status = "escalated"
    ticket.risk_level = "high"
    ticket.final_response = (
        "Thanks for flagging this. A human support specialist will review your case "
        f"because it requires careful handling: {reason}."
    )
    db.commit()
    db.refresh(ticket)
    return ticket


def create_internal_task(db: Session, ticket_id: int, title: str, priority: str) -> PendingAction:
    return create_pending_action(
        db,
        ticket_id=ticket_id,
        action_type="create_internal_task",
        payload={"title": title, "priority": priority},
        risk_level=priority if priority in {"high", "urgent"} else "low",
        status="executed",
    )


def execute_approved_action(db: Session, action: PendingAction) -> PendingAction:
    if action.status not in {"approved", "pending"}:
        return action

    payload = action.payload_json or {}
    if action.action_type == "update_shipping_address":
        update_shipping_address(db, int(payload["order_id"]), str(payload["new_address"]))
    elif action.action_type == "cancel_order":
        cancel_order(db, int(payload["order_id"]))
    elif action.action_type == "create_refund_request":
        payload["refund_status"] = "requested"
        action.payload_json = payload
    elif action.action_type == "create_internal_task":
        payload["task_status"] = "created"
        action.payload_json = payload
    else:
        payload["note"] = "Simulated execution recorded."
        action.payload_json = payload

    action.status = "executed"
    action.decided_at = utc_now()
    ticket = db.get(Ticket, action.ticket_id)
    if ticket:
        ticket.status = "resolved"
        ticket.final_response = (
            ticket.final_response
            or "Your request has been reviewed and the approved action has been completed."
        )
    db.commit()
    db.refresh(action)
    return action


def reject_action(db: Session, action: PendingAction) -> PendingAction:
    action.status = "rejected"
    action.decided_at = utc_now()
    ticket = db.get(Ticket, action.ticket_id)
    if ticket and ticket.status == "pending_approval":
        ticket.status = "resolved"
        ticket.final_response = (
            "The requested action was reviewed and not approved. No account, order, or "
            "payment changes were executed."
        )
    db.commit()
    db.refresh(action)
    return action
