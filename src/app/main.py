from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import router
from app.db.init_db import init_db
from app.observability.telemetry import configure_telemetry

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app=FastAPI(title="Production RAG Agent",version="0.1.0",lifespan=lifespan)
app.include_router(router)
STATIC_DIR=Path(__file__).resolve().parent/"web"/"static"
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")
configure_telemetry(app)
