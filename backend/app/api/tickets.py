from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.runtime_factory import get_support_runner
from app.db import get_db
from app.models import AgentEvent, AgentRun, PendingAction, Ticket
from app.schemas import TicketCreate, TicketWorkflowResponse
from app.serializers import action_to_dict, event_to_dict, run_to_dict, ticket_to_dict

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", response_model=TicketWorkflowResponse)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> dict:
    result = get_support_runner().run_ticket_data(
        db,
        subject=payload.subject,
        description=payload.description,
        customer_email=payload.customer_email,
    )
    result.pop("state", None)
    return result


@router.get("")
def list_tickets(db: Session = Depends(get_db)) -> list[dict]:
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return [ticket_to_dict(ticket) for ticket in tickets]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> dict:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    run = db.query(AgentRun).filter(AgentRun.ticket_id == ticket_id).order_by(AgentRun.started_at.desc()).first()
    events = db.query(AgentEvent).filter(AgentEvent.ticket_id == ticket_id).order_by(AgentEvent.step_index.asc()).all()
    actions = db.query(PendingAction).filter(PendingAction.ticket_id == ticket_id).all()
    return {
        "ticket": ticket_to_dict(ticket),
        "agent_run": run_to_dict(run) if run else None,
        "events": [event_to_dict(event) for event in events],
        "pending_actions": [action_to_dict(action) for action in actions],
    }


@router.get("/{ticket_id}/events")
def get_ticket_events(ticket_id: int, db: Session = Depends(get_db)) -> list[dict]:
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    events = db.query(AgentEvent).filter(AgentEvent.ticket_id == ticket_id).order_by(AgentEvent.step_index.asc()).all()
    return [event_to_dict(event) for event in events]
