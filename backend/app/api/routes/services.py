from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ServiceCatalog
from app.schemas import ServiceCreate, ServiceRead

router = APIRouter()


@router.post("", response_model=ServiceRead)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)) -> ServiceCatalog:
    service = ServiceCatalog(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get("", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)) -> list[ServiceCatalog]:
    return db.query(ServiceCatalog).order_by(ServiceCatalog.name.asc()).all()
