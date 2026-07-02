from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AlertRead, AlertWebhook, IncidentRead
from app.services.ingestion import ingest_alert
from app.workers.tasks import process_incident

router = APIRouter()


@router.post("/webhook")
def alert_webhook(payload: AlertWebhook, db: Session = Depends(get_db)) -> dict[str, object]:
    alert, incident = ingest_alert(db, payload)
    process_incident.delay(str(incident.id))
    return {
        "alert": AlertRead.model_validate(alert),
        "incident": IncidentRead.model_validate(incident),
        "queued": True,
    }
