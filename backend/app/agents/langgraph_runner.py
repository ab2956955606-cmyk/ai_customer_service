from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents import langgraph_nodes
from app.agents.langgraph_graph import build_support_graph
from app.agents.langgraph_state import SupportAgentState, initial_langgraph_state
from app.models import AgentEvent, AgentRun, Ticket, utc_now
from app.serializers import action_to_dict, event_to_dict, run_to_dict, ticket_to_dict


class LangGraphSupportRunner:
    runtime_name = "langgraph"

    def __init__(self) -> None:
        self.graph = build_support_graph()

    def run_ticket_data(
        self,
        db: Session,
        subject: str,
        description: str,
        customer_email: str | None = None,
    ) -> dict:
        ticket = Ticket(
            subject=subject,
            description=description,
            customer_email=customer_email.lower() if customer_email else None,
            category="unknown",
            priority="normal",
            risk_level="low",
            status="open",
            assigned_agent="supportops-agent",
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return self.run_ticket(db, ticket.id)

    def run_ticket(self, db: Session, ticket_id: int) -> dict:
        ticket = db.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} not found")

        run = AgentRun(
            ticket_id=ticket.id,
            status="running",
            started_at=utc_now(),
            agents_run=[],
            total_latency_ms=0,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        state = initial_langgraph_state(
            ticket_id=ticket.id,
            run_id=run.id,
            subject=ticket.subject,
            description=ticket.description,
            customer_email=ticket.customer_email,
        )

        token = langgraph_nodes.bind_db(db)
        try:
            final_state: SupportAgentState = self.graph.invoke(
                state,
                config={"configurable": {"thread_id": f"ticket:{ticket.id}:run:{run.id}"}},
            )
        except Exception as exc:
            final_state = SupportAgentState(**state)
            final_state["error"] = str(exc)
            final_state["errors"] = [str(exc)]
            final_state["events"] = [
                {
                    "step_index": 1,
                    "node_name": "langgraph_runtime",
                    "event_type": "error",
                    "status": "failed",
                    "input_summary": f"ticket_id={ticket.id}",
                    "output_summary": f"LangGraph runtime failed: {exc}",
                    "tool_name": None,
                    "citations": [],
                    "latency_ms": 0,
                }
            ]
            ticket.status = "failed"
            ticket.final_response = "The workflow failed while processing this ticket."
            db.commit()
        finally:
            langgraph_nodes.reset_db(token)

        events = final_state.get("events", [])
        persisted_events: list[AgentEvent] = []
        for event in events:
            persisted = AgentEvent(
                run_id=run.id,
                ticket_id=ticket.id,
                **event,
            )
            db.add(persisted)
            persisted_events.append(persisted)

        run.status = "failed" if final_state.get("error") and not final_state.get("final_response") else "completed"
        run.completed_at = utc_now()
        run.agents_run = final_state.get("agents_run", [])
        run.total_latency_ms = sum(event.get("latency_ms", 0) for event in events)
        db.commit()

        for event in persisted_events:
            db.refresh(event)
        db.refresh(run)
        db.refresh(ticket)

        pending = ticket.pending_actions if ticket else []
        return {
            "ticket": ticket_to_dict(ticket),
            "agent_run": run_to_dict(run),
            "agents_run": final_state.get("agents_run", []),
            "events": [event_to_dict(event) for event in persisted_events],
            "pending_actions": [action_to_dict(action) for action in pending],
            "final_response": final_state.get("final_response"),
            "citations": final_state.get("citations", []),
            "state": final_state,
        }
