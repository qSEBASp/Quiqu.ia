from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import SessionLocal, init_db
from .routers import matches, profile, stats, sync
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
)

origins = {
    settings.frontend_origin,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(sync.router)
app.include_router(matches.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": settings.provider}
