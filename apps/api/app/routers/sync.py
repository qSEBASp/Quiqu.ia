from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..providers import ProviderError
from ..services import get_or_create_profile, reset_data, sync_matches

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("")
async def sync(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    try:
        return await sync_matches(db, profile)
    except ProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network/format edge cases
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error sincronizando: {exc}"
        ) from exc


@router.post("/reset")
async def reset(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    reset_data(db)
    try:
        result = await sync_matches(db, profile)
    except ProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {**result, "reset": True}
