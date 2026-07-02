import enum


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"


class EventType(str, enum.Enum):
    ALERT_RECEIVED = "alert_received"
    STATUS_CHANGED = "status_changed"
    EVIDENCE_ADDED = "evidence_added"
    AI_SUMMARY = "ai_summary"
    SLACK_POSTED = "slack_posted"
    GITHUB_CONTEXT = "github_context"
    RUNBOOK_MATCH = "runbook_match"
    POSTMORTEM_DRAFT = "postmortem_draft"
    APPROVAL = "approval"


class EvidenceSource(str, enum.Enum):
    ALERT = "alert"
    GITHUB = "github"
    RUNBOOK = "runbook"
    MANUAL = "manual"
    AI = "ai"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
