import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApprovalStatus, EvidenceSource, EventType, IncidentStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AlertWebhook(BaseModel):
    source: str = "webhook"
    title: str
    severity: str = "medium"
    service_name: str | None = None
    description: str | None = None
    external_id: str | None = None
    payload: dict = Field(default_factory=dict)


class AlertRead(ORMModel):
    id: uuid.UUID
    source: str
    title: str
    incident_id: uuid.UUID | None
    received_at: datetime


class IncidentCreate(BaseModel):
    title: str
    description: str | None = None
    severity: str = "medium"
    service_name: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: IncidentStatus | None = None
    severity: str | None = None
    assigned_to: str | None = None


class IncidentRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: IncidentStatus
    severity: str
    ai_summary: str | None
    ai_recommendations: dict | None
    created_at: datetime
    updated_at: datetime


class IncidentDetail(IncidentRead):
    events: list["IncidentEventRead"] = Field(default_factory=list)
    evidence_items: list["EvidenceItemRead"] = Field(default_factory=list)
    slack_messages: list["SlackMessageRead"] = Field(default_factory=list)
    postmortem_drafts: list["PostmortemDraftRead"] = Field(default_factory=list)


class IncidentEventRead(ORMModel):
    id: uuid.UUID
    event_type: EventType
    message: str
    payload: dict | None
    created_at: datetime


class EvidenceItemRead(ORMModel):
    id: uuid.UUID
    source: EvidenceSource
    title: str
    content: str
    url: str | None


class SlackMessageRead(ORMModel):
    id: uuid.UUID
    channel: str
    message: str
    posted: bool


class PostmortemDraftRead(ORMModel):
    id: uuid.UUID
    title: str
    content: str
    timeline: dict | None
    action_items: list | None
    published: bool


class RunbookCreate(BaseModel):
    title: str
    content: str
    service_name: str | None = None
    tags: list[str] = Field(default_factory=list)


class RunbookRead(ORMModel):
    id: uuid.UUID
    title: str
    content: str
    tags: list | None


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    owner_team: str | None = None
    github_repo: str | None = None
    slack_channel: str | None = None


class ServiceRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_team: str | None
    github_repo: str | None
    slack_channel: str | None


class ApprovalRead(ORMModel):
    id: uuid.UUID
    action: str
    status: ApprovalStatus
    requested_by: str
    reviewed_by: str | None


IncidentDetail.model_rebuild()
