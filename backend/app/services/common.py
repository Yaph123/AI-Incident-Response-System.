from sqlalchemy.orm import Session

from app.models import IncidentEvent, ServiceCatalog
from app.models.enums import EventType


def log_event(
    db: Session,
    incident_id,
    event_type: EventType,
    message: str,
    payload: dict | None = None,
) -> IncidentEvent:
    event = IncidentEvent(
        incident_id=incident_id,
        event_type=event_type,
        message=message,
        payload=payload or {},
    )
    db.add(event)
    db.flush()
    return event


def get_or_create_service(db: Session, name: str | None) -> ServiceCatalog | None:
    if not name:
        return None
    service = db.query(ServiceCatalog).filter(ServiceCatalog.name == name).one_or_none()
    if service:
        return service
    service = ServiceCatalog(name=name)
    db.add(service)
    db.flush()
    return service
