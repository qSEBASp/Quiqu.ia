from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .db import SessionLocal, init_db
from .routers import coach, export, goals, matches, profile, stats, sync
from .security import install_security
from .services import get_or_create_profile


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        get_or_create_profile(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="quiqu.ia",
    description="Analizador de partidas de Valorant con coaching automatico",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

install_security(app)

app.include_router(profile.router)
app.include_router(sync.router)
app.include_router(matches.router)
app.include_router(stats.router)
app.include_router(goals.router)
app.include_router(coach.router)
app.include_router(export.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": settings.provider}
