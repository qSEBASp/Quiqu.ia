from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..constants import REGIONS
from ..db import get_db
from ..models import utcnow
from ..schemas import ProfileUpdate
from ..services import get_or_create_profile, profile_dict, reset_data

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
def read_profile(db: Session = Depends(get_db)):
    return profile_dict(get_or_create_profile(db))


@router.put("")
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    region = payload.region.lower().strip()
    if region not in REGIONS:
        raise HTTPException(status_code=400, detail=f"Región no válida: {region}")

    changed_identity = (
        profile.riot_id != payload.riot_id
        or profile.tag != payload.tag
        or profile.region != region
        or profile.provider != payload.provider
    )

    profile.riot_id = payload.riot_id
    profile.tag = payload.tag
    profile.region = region
    profile.provider = payload.provider

    if payload.henrik_api_key is not None:
        profile.henrik_api_key = payload.henrik_api_key.strip()

    if profile.provider == "henrik" and not profile.henrik_api_key:
        raise HTTPException(
            status_code=400,
            detail="Para usar HenrikDev necesitas una API key. Consíguela en api.henrikdev.xyz.",
        )

    if changed_identity:
        profile.puuid = None
        profile.rank_name = None
        profile.rank_tier = None
        # Las metricas son de una sola cuenta: al cambiar de identidad o de
        # fuente, el historial anterior deja de ser comparable.
        reset_data(db)

    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return profile_dict(profile)
