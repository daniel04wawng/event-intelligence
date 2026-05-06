"""SQLAlchemy ORM models matching infra/scripts/init_db.sql.

These mirror the file-based schema in `packages/shared/event_state.py`. The
loose, fast-iterating fields (intelligence, state, raw) are JSONB columns so
the pipeline can add new keys without a migration.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Integer, Date, DateTime, ForeignKey, ARRAY, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(Text)
    event_date: Mapped[Optional[date]] = mapped_column(Date)
    target_size: Mapped[Optional[int]] = mapped_column(Integer)
    format: Mapped[Optional[str]] = mapped_column(Text)
    brief_text: Mapped[Optional[str]] = mapped_column(Text)
    success_metrics: Mapped[list] = mapped_column(JSONB, default=list)
    intelligence: Mapped[dict] = mapped_column(JSONB, default=dict)
    state: Mapped[dict] = mapped_column(JSONB, default=dict)
    visibility: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    people: Mapped[list["Person"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[Optional[str]] = mapped_column(Text)
    linkedin_url: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    persona: Mapped[Optional[str]] = mapped_column(Text)
    fit_score: Mapped[Optional[int]] = mapped_column(Integer)
    priority: Mapped[Optional[str]] = mapped_column(Text)
    why_relevant: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    status: Mapped[str] = mapped_column(Text, default="not_contacted")
    source: Mapped[Optional[str]] = mapped_column(Text)
    outreach_angle: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped["Event"] = relationship(back_populates="people")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[str] = mapped_column(Text, nullable=False)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE")
    )
    branch_context: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    input_summary: Mapped[Optional[str]] = mapped_column(Text)
    output_summary: Mapped[Optional[str]] = mapped_column(Text)
    decisions_made: Mapped[list] = mapped_column(JSONB, default=list)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[str]] = mapped_column(Text)
    files_read: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    files_written: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    blockers: Mapped[list] = mapped_column(JSONB, default=list)
    next_actions: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped[Optional["Event"]] = relationship(back_populates="agent_runs")
