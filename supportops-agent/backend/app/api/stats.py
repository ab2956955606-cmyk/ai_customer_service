from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AgentEvent, AgentRun, PendingAction, Ticket
from app.serializers import event_to_dict, run_to_dict

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _breakdown(values: list[str | None]) -> list[dict]:
    counter = Counter(value or "unknown" for value in values)
    return [{"name": key, "value": value} for key, value in sorted(counter.items())]


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    tickets = db.query(Ticket).all()
    total = len(tickets)
    resolved = sum(1 for ticket in tickets if ticket.status == "resolved")
    escalated = sum(1 for ticket in tickets if ticket.status == "escalated")
    pending = db.query(PendingAction).filter(PendingAction.status == "pending").count()
    runs = db.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(8).all()
    average_latency = round(sum(run.total_latency_ms for run in runs) / len(runs), 2) if runs else 0
    approvals_total = db.query(PendingAction).count()
    approvals_done = db.query(PendingAction).filter(PendingAction.status.in_(["approved", "executed"])).count()
    latest_trace = (
        db.query(AgentEvent)
        .order_by(AgentEvent.created_at.desc(), AgentEvent.step_index.desc())
        .limit(8)
        .all()
    )
    return {
        "total_tickets": total,
        "resolved_tickets": resolved,
        "escalated_tickets": escalated,
        "pending_approval_count": pending,
        "average_latency": average_latency,
        "category_breakdown": _breakdown([ticket.category for ticket in tickets]),
        "priority_breakdown": _breakdown([ticket.priority for ticket in tickets]),
        "escalation_rate": round(escalated / total, 3) if total else 0,
        "approval_rate": round(approvals_done / approvals_total, 3) if approvals_total else 0,
        "recent_runs": [run_to_dict(run) for run in runs],
        "latest_trace_preview": [event_to_dict(event) for event in latest_trace],
    }
