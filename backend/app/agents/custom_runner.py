from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.graph import run_ticket_workflow
from app.models import Ticket


class CustomSupportRunner:
    runtime_name = "custom"

    def run_ticket_data(
        self,
        db: Session,
        subject: str,
        description: str,
        customer_email: str | None = None,
    ) -> dict:
        return run_ticket_workflow(
            db,
            subject=subject,
            description=description,
            customer_email=customer_email,
        )

    def run_ticket(self, db: Session, ticket_id: int) -> dict:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} not found")
        return run_ticket_workflow(
            db,
            subject=ticket.subject,
            description=ticket.description,
            customer_email=ticket.customer_email,
            ticket_id=ticket.id,
        )
