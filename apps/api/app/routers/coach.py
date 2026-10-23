from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..analysis.llm import LLMUnavailable, coach_chat, historical_summary
from ..db import get_db
from ..schemas import ChatRequest
from ..services import build_overview, get_or_create_profile, list_matches

router = APIRouter(prefix="/api/coach", tags=["coach"])


def _context(db: Session) -> dict:
    overview = build_overview(db)
    profile = get_or_create_profile(db)
    recent = list_matches(db, limit=12)
    return {
        "jugador": {
            "riot_id": profile.riot_id,
            "tag": profile.tag,
            "rango": profile.rank_name,
            "region": profile.region,
        },
        "totales": overview["totals"],
        "rango": overview["rank"]["current"],
        "benchmarks": overview["benchmarks"],
        "patrones": [
            {"titulo": p["title"], "categoria": p["category"], "repeticiones": p["count"]}
            for p in overview["top_patterns"]
        ],
        "puntos_fuertes": [
            {"titulo": s["title"], "categoria": s["category"], "repeticiones": s["count"]}
            for s in overview["strengths"]
        ],
        "economia": overview["economy"],
        "clutches": overview["clutches"],
        "objetivos": [
            {"titulo": g["title"], "estado": g["status"]} for g in overview["goals"]
        ],
        "ultimas_partidas": [
            {
                "fecha": match["started_at"],
                "mapa": match["map"],
                "agente": match["agent"],
                "modo": match["mode"],
                "resultado": match["result"],
                "marcador": f"{match['score_us']}-{match['score_them']}",
                "acs": match["acs"],
                "kast": match["kast"],
                "hs_pct": match["hs_pct"],
                "hallazgo_principal": match["top_insight"],
            }
            for match in recent
        ],
    }


@router.post("/summary")
def summary(db: Session = Depends(get_db)):
    try:
        return historical_summary(_context(db))
    except LLMUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        return coach_chat(
            _context(db),
            [{"role": message.role, "content": message.content} for message in payload.messages],
        )
    except LLMUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
