from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Incident
from app.models.enums import EventType
from app.schemas import IncidentDetail, IncidentRead, IncidentUpdate
from app.services.common import log_event
from app.services.orchestration import run_incident_pipeline

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db)) -> list[Incident]:
    return db.query(Incident).order_by(Incident.created_at.desc()).limit(100).all()


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: UUID, db: Session = Depends(get_db)) -> Incident:
    incident = (
        db.query(Incident)
        .options(
            selectinload(Incident.events),
            selectinload(Incident.evidence_items),
            selectinload(Incident.slack_messages),
            selectinload(Incident.postmortem_drafts),
        )
        .filter(Incident.id == incident_id)
        .one_or_none()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident(incident_id: UUID, payload: IncidentUpdate, db: Session = Depends(get_db)) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(incident, key, value)
    log_event(db, incident.id, EventType.STATUS_CHANGED, "Incident manually updated", updates)
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/run", response_model=IncidentRead)
async def rerun_pipeline(incident_id: UUID, db: Session = Depends(get_db)) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    await run_incident_pipeline(db, incident.id)
    db.refresh(incident)
    return incident
