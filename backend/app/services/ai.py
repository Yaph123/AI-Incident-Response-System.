from sqlalchemy.orm import Session

from app.integrations.openai_client import openai_client
from app.models import EvidenceItem, Incident, PostmortemDraft
from app.models.enums import EventType, EvidenceSource
from app.services.common import log_event
from app.services.context import search_runbooks


def generate_incident_summary(db: Session, incident: Incident) -> Incident:
    evidence_text = "\n".join(
        f"- [{e.source.value}] {e.title}: {e.content[:300]}" for e in incident.evidence_items[:15]
    )
    runbooks = search_runbooks(db, incident.title + " " + (incident.description or ""))
    runbook_text = "\n".join(f"- {rb.title}: {rb.content[:400]}" for rb in runbooks)

    system = (
        "You are an SRE incident commander. Produce a concise incident summary, "
        "likely causes, immediate mitigation steps, and recommended owners."
    )
    user = (
        f"Incident: {incident.title}\n"
        f"Severity: {incident.severity}\n"
        f"Description: {incident.description or 'N/A'}\n\n"
        f"Evidence:\n{evidence_text or 'None yet'}\n\n"
        f"Runbooks:\n{runbook_text or 'None matched'}"
    )

    summary = openai_client.chat(system, user)
    incident.ai_summary = summary
    incident.ai_recommendations = {
        "runbook_ids": [str(rb.id) for rb in runbooks],
        "mitigation": [
            "Confirm blast radius and customer impact",
            "Rollback or feature-flag recent deploy if correlated",
            "Assign incident commander and comms owner",
        ],
    }

    for rb in runbooks:
        db.add(
            EvidenceItem(
                incident_id=incident.id,
                source=EvidenceSource.RUNBOOK,
                title=rb.title,
                content=rb.content[:2000],
            )
        )

    log_event(db, incident.id, EventType.AI_SUMMARY, "AI summary generated", {"length": len(summary)})
    log_event(
        db,
        incident.id,
        EventType.RUNBOOK_MATCH,
        f"Matched {len(runbooks)} runbook(s)",
        {"runbook_titles": [rb.title for rb in runbooks]},
    )
    db.commit()
    db.refresh(incident)
    return incident


def draft_postmortem(db: Session, incident: Incident) -> PostmortemDraft:
    timeline = [
        {
            "at": e.created_at.isoformat(),
            "type": e.event_type.value,
            "message": e.message,
        }
        for e in sorted(incident.events, key=lambda x: x.created_at)
    ]
    system = "You draft blameless postmortems with timeline, root cause hypotheses, and action items."
    user = (
        f"Incident: {incident.title}\n"
        f"Summary: {incident.ai_summary or incident.description or 'N/A'}\n"
        f"Timeline events: {timeline}"
    )
    content = openai_client.chat(system, user)
    draft = PostmortemDraft(
        incident_id=incident.id,
        title=f"Postmortem: {incident.title}",
        content=content,
        timeline={"events": timeline},
        action_items=[
            {"item": "Add monitoring for primary failure mode", "owner": "SRE"},
            {
                "item": "Update runbook with rollback steps",
                "owner": incident.service.owner_team if incident.service else "Team",
            },
        ],
    )
    db.add(draft)
    log_event(db, incident.id, EventType.POSTMORTEM_DRAFT, "Postmortem draft created")
    db.commit()
    db.refresh(draft)
    return draft
