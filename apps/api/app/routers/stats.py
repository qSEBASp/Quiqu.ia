from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import build_overview

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    return build_overview(db)
