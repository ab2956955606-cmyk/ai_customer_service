from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PendingAction, Ticket
from app.serializers import action_to_dict, ticket_to_dict
from app.tools.action_tools import execute_approved_action, reject_action

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


def _approval_payload(action: PendingAction, db: Session) -> dict:
    ticket = db.get(Ticket, action.ticket_id)
    payload = action_to_dict(action)
    payload["ticket_subject"] = ticket.subject if ticket else None
    payload["ticket_status"] = ticket.status if ticket else None
    return payload


@router.get("")
def list_approvals(db: Session = Depends(get_db)) -> list[dict]:
    actions = db.query(PendingAction).order_by(PendingAction.created_at.desc()).all()
    return [_approval_payload(action, db) for action in actions]


@router.post("/{action_id}/approve")
def approve(action_id: int, db: Session = Depends(get_db)) -> dict:
    action = db.get(PendingAction, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    action.status = "approved"
    db.commit()
    db.refresh(action)
    action = execute_approved_action(db, action)
    ticket = db.get(Ticket, action.ticket_id)
    return {"action": action_to_dict(action), "ticket": ticket_to_dict(ticket)}


@router.post("/{action_id}/reject")
def reject(action_id: int, db: Session = Depends(get_db)) -> dict:
    action = db.get(PendingAction, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    action = reject_action(db, action)
    ticket = db.get(Ticket, action.ticket_id)
    return {"action": action_to_dict(action), "ticket": ticket_to_dict(ticket)}
