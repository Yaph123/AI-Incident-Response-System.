from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.database import engine, init_db
from app.core.logging import setup_logging
from app.models import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    init_db()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI Incident Response System", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI Incident Response API"}
