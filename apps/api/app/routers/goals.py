from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import GoalCreate, GoalUpdate
from ..services import goal_create, goal_delete, goal_update, goals_list

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("")
def read_goals(db: Session = Depends(get_db)):
    return {"goals": goals_list(db)}


@router.post("")
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    return goal_create(
        db,
        title=payload.title,
        detail=payload.detail,
        rule_id=payload.rule_id,
        target=payload.target,
    )


@router.patch("/{goal_id}")
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)):
    goal = goal_update(db, goal_id, payload.status)
    if goal is None:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    return goal


@router.delete("/{goal_id}")
def remove_goal(goal_id: int, db: Session = Depends(get_db)):
    if not goal_delete(db, goal_id):
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    return {"deleted": True}
