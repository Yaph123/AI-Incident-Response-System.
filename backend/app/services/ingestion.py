from sqlalchemy.orm import Session

from app.models import Alert, Incident
from app.models.enums import EventType, EvidenceSource, IncidentStatus
from app.schemas import AlertWebhook
from app.services.common import get_or_create_service, log_event


def ingest_alert(db: Session, payload: AlertWebhook) -> tuple[Alert, Incident]:
    service = get_or_create_service(db, payload.service_name)
    incident = Incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=IncidentStatus.OPEN,
        service=service,
    )
    db.add(incident)
    db.flush()

    alert = Alert(
        incident_id=incident.id,
        source=payload.source,
        external_id=payload.external_id,
        title=payload.title,
        payload=payload.payload,
    )
    db.add(alert)

    log_event(
        db,
        incident.id,
        EventType.ALERT_RECEIVED,
        f"Alert received from {payload.source}: {payload.title}",
        {"alert_source": payload.source, "severity": payload.severity},
    )
    db.commit()
    db.refresh(incident)
    db.refresh(alert)
    return alert, incident
