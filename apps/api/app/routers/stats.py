from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Match
from ..services import build_overview

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/overview")
def overview(
    mode: str | None = Query(default=None, max_length=32),
    days: int | None = Query(default=None, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return build_overview(db, mode=mode, days=days)


@router.get("/backdrop")
def backdrop(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Match.id))) or 0
    if total == 0:
        return {"matches": 0, "role": None}

    count = func.count(Match.id)
    row = db.execute(
        select(Match.agent_role, count)
        .where(Match.agent_role != "")
        .group_by(Match.agent_role)
        .order_by(count.desc(), Match.agent_role.asc())
        .limit(1)
    ).first()

    role = None
    if row is not None:
        name, matches = row
        role = {
            "name": name,
            "matches": matches,
            "share": round(matches / total * 100, 1),
        }

    return {"matches": total, "role": role}
