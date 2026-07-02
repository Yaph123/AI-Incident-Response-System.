from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.runbooks import router as runbooks_router
from app.api.routes.services import router as services_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["incidents"])
api_router.include_router(runbooks_router, prefix="/runbooks", tags=["runbooks"])
api_router.include_router(services_router, prefix="/services", tags=["services"])
