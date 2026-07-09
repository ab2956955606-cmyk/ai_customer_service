from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(80), default="unknown")
    priority: Mapped[str | None] = mapped_column(String(40), default="normal")
    risk_level: Mapped[str | None] = mapped_column(String(40), default="low")
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    assigned_agent: Mapped[str | None] = mapped_column(String(120), default="supportops-agent")
    final_response: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    runs: Mapped[list["AgentRun"]] = relationship(back_populates="ticket")
    events: Mapped[list["AgentEvent"]] = relationship(back_populates="ticket")
    pending_actions: Mapped[list["PendingAction"]] = relationship(back_populates="ticket")


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), default="active", nullable=False)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    order_number: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_address: Mapped[str] = mapped_column(String(500), nullable=False)


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    agents_run: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="runs")
    events: Mapped[list["AgentEvent"]] = relationship(back_populates="run")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"), index=True, nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True, nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), default="node", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(160))
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    run: Mapped[AgentRun] = relationship(back_populates="events")
    ticket: Mapped[Ticket] = relationship(back_populates="events")


class PendingAction(TimestampMixin, Base):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)

    ticket: Mapped[Ticket] = relationship(back_populates="pending_actions")
