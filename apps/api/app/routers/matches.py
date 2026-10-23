from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..analysis.llm import LLMUnavailable
from ..db import get_db
from ..models import Match
from ..services import list_matches, match_detail, regenerate_report

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _get_match(db: Session, match_id: str) -> Match:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return match


@router.get("")
def get_matches(
    limit: int = Query(default=100, ge=1, le=200),
    mode: str | None = Query(default=None, max_length=32),
    days: int | None = Query(default=None, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return {"matches": list_matches(db, limit, mode=mode, days=days)}


@router.get("/{match_id}")
def get_match(match_id: str, db: Session = Depends(get_db)):
    return match_detail(_get_match(db, match_id))


@router.get("/{match_id}/report")
def get_report(match_id: str, db: Session = Depends(get_db)):
    match = _get_match(db, match_id)
    if match.report is None:
        raise HTTPException(status_code=404, detail="Esta partida no tiene informe")
    return {
        "summary": match.report.summary,
        "priorities": match.report.priorities,
        "drills": match.report.drills,
        "model": match.report.model,
    }


@router.post("/{match_id}/report/ai")
def enhance_with_ai(match_id: str, db: Session = Depends(get_db)):
    match = _get_match(db, match_id)
    try:
        return regenerate_report(db, match)
    except LLMUnavailable as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
