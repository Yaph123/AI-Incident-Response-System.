import asyncio

from app.core.database import SessionLocal
from app.services.orchestration import run_incident_pipeline
from app.workers.celery_app import celery_app


@celery_app.task(name="process_incident")
def process_incident(incident_id: str) -> str:
    db = SessionLocal()
    try:
        asyncio.run(run_incident_pipeline(db, incident_id))
        return incident_id
    finally:
        db.close()
