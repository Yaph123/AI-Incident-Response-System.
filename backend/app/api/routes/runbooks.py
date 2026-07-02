from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Runbook
from app.schemas import RunbookCreate, RunbookRead
from app.services.common import get_or_create_service
from app.services.orchestration import index_runbook_embedding

router = APIRouter()


@router.post("", response_model=RunbookRead)
def create_runbook(payload: RunbookCreate, db: Session = Depends(get_db)) -> Runbook:
    service = get_or_create_service(db, payload.service_name)
    runbook = Runbook(
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        service=service,
    )
    db.add(runbook)
    db.commit()
    db.refresh(runbook)
    return index_runbook_embedding(db, runbook)


@router.get("", response_model=list[RunbookRead])
def list_runbooks(
    query: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Runbook]:
    q = db.query(Runbook)
    if query:
        pattern = f"%{query}%"
        q = q.filter((Runbook.title.ilike(pattern)) | (Runbook.content.ilike(pattern)))
    return q.order_by(Runbook.updated_at.desc()).limit(100).all()
