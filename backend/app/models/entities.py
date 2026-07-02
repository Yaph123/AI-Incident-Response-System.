import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ApprovalStatus, EvidenceSource, EventType, IncidentStatus


class ServiceCatalog(Base, TimestampMixin):
    __tablename__ = "service_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_team: Mapped[str | None] = mapped_column(String(255))
    github_repo: Mapped[str | None] = mapped_column(String(512))
    slack_channel: Mapped[str | None] = mapped_column(String(255))
    oncall_rotation: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    incidents: Mapped[list["Incident"]] = relationship(back_populates="service")
    runbooks: Mapped[list["Runbook"]] = relationship(back_populates="service")


class Runbook(Base, TimestampMixin):
    __tablename__ = "runbooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("service_catalog.id"))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    embedding: Mapped[list | None] = mapped_column(Vector(1536))

    service: Mapped["ServiceCatalog | None"] = relationship(back_populates="runbooks")


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(default=IncidentStatus.OPEN)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    service_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("service_catalog.id"))
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_recommendations: Mapped[dict | None] = mapped_column(JSONB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    service: Mapped["ServiceCatalog | None"] = relationship(back_populates="incidents")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="incident")
    events: Mapped[list["IncidentEvent"]] = relationship(back_populates="incident")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="incident")
    slack_messages: Mapped[list["SlackMessage"]] = relationship(back_populates="incident")
    postmortem_drafts: Mapped[list["PostmortemDraft"]] = relationship(back_populates="incident")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="incident")


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("incidents.id"))
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident | None"] = relationship(back_populates="alerts")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    event_type: Mapped[EventType] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped["Incident"] = relationship(back_populates="events")


class EvidenceItem(Base, TimestampMixin):
    __tablename__ = "evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    source: Mapped[EvidenceSource] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    incident: Mapped["Incident"] = relationship(back_populates="evidence_items")


class SlackMessage(Base, TimestampMixin):
    __tablename__ = "slack_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    slack_ts: Mapped[str | None] = mapped_column(String(64))
    posted: Mapped[bool] = mapped_column(Boolean, default=False)

    incident: Mapped["Incident"] = relationship(back_populates="slack_messages")


class PostmortemDraft(Base, TimestampMixin):
    __tablename__ = "postmortem_drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timeline: Mapped[dict | None] = mapped_column(JSONB)
    action_items: Mapped[list | None] = mapped_column(JSONB, default=list)
    published: Mapped[bool] = mapped_column(Boolean, default=False)

    incident: Mapped["Incident"] = relationship(back_populates="postmortem_drafts")


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(default=ApprovalStatus.PENDING)
    requested_by: Mapped[str] = mapped_column(String(255), default="system")
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    incident: Mapped["Incident"] = relationship(back_populates="approvals")
