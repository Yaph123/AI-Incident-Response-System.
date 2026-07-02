from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.slack import slack_client
from app.models import Approval, Incident, Runbook, SlackMessage
from app.models.enums import ApprovalStatus, EventType, IncidentStatus
from app.services.ai import draft_postmortem, generate_incident_summary
from app.services.common import log_event
from app.services.context import fetch_github_context


async def run_incident_pipeline(db: Session, incident_id) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).one()
    incident.status = IncidentStatus.INVESTIGATING
    log_event(db, incident.id, EventType.STATUS_CHANGED, "Status -> investigating")
    db.commit()

    await fetch_github_context(db, incident)
    db.refresh(incident)

    generate_incident_summary(db, incident)
    db.refresh(incident)

    await notify_slack(db, incident)
    draft_postmortem(db, incident)
    db.refresh(incident)
    return incident


async def notify_slack(db: Session, incident: Incident) -> SlackMessage:
    channel = (
        incident.service.slack_channel
        if incident.service and incident.service.slack_channel
        else settings.slack_default_channel
    )
    text = (
        f"*Incident:* {incident.title}\n"
        f"*Severity:* {incident.severity}\n"
        f"*Status:* {incident.status.value}\n"
        f"*Summary:* {(incident.ai_summary or 'Pending')[:500]}"
    )

    msg = SlackMessage(incident_id=incident.id, channel=channel, message=text, posted=False)
    db.add(msg)
    db.flush()

    if settings.require_approval_for_slack:
        approval = Approval(
            incident_id=incident.id,
            action="post_slack_message",
            status=ApprovalStatus.PENDING,
        )
        db.add(approval)
        log_event(db, incident.id, EventType.APPROVAL, "Slack post pending approval")
        db.commit()
        db.refresh(msg)
        return msg

    ts = await slack_client.post_message(channel, text)
    msg.posted = ts is not None
    msg.slack_ts = ts
    log_event(db, incident.id, EventType.SLACK_POSTED, f"Slack message {'sent' if ts else 'logged locally'}")
    db.commit()
    db.refresh(msg)
    return msg


def index_runbook_embedding(db: Session, runbook: Runbook) -> Runbook:
    from app.integrations.openai_client import openai_client

    runbook.embedding = openai_client.embed(f"{runbook.title}\n{runbook.content}")
    db.commit()
    db.refresh(runbook)
    return runbook
