import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..providers import ProviderError
from ..services import (
    get_or_create_profile,
    reanalyze_all,
    reset_matches,
    sync_matches,
)

router = APIRouter(prefix="/api/sync", tags=["sync"])
logger = logging.getLogger(__name__)


@router.post("")
async def sync(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    try:
        return await sync_matches(db, profile)
    except ProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        logger.exception("Error inesperado sincronizando partidas")
        raise HTTPException(
            status_code=500,
            detail="No se pudo sincronizar. Revisa el registro del servidor.",
        ) from None


@router.post("/reanalyze")
def reanalyze(db: Session = Depends(get_db)):
    try:
        return reanalyze_all(db)
    except Exception:
        db.rollback()
        logger.exception("Error reanalizando el historial")
        raise HTTPException(
            status_code=500,
            detail="No se pudo reanalizar el historial. Revisa el registro del servidor.",
        ) from None


@router.post("/reset")
async def reset(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    reset_matches(db)
    try:
        result = await sync_matches(db, profile)
    except ProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        logger.exception("Error inesperado resincronizando partidas")
        raise HTTPException(
            status_code=500,
            detail="No se pudo resincronizar. Revisa el registro del servidor.",
        ) from None
    return {**result, "reset": True}
