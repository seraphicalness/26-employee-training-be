from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..llm import normalize_topic_id
from ..schemas import UserUpdate

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me")
async def get_me(db: Session = Depends(get_db)):
    user = crud.get_or_create_user(db)
    return crud.user_to_dict(user)


@router.put("/me")
async def update_me(update: UserUpdate, db: Session = Depends(get_db)):
    user = crud.get_or_create_user(db)

    if update.name is not None:
        user.name = update.name
    if update.department is not None:
        user.department = update.department
    if update.selected_training is not None:
        user.selected_training = normalize_topic_id(update.selected_training)

    db.commit()
    db.refresh(user)
    return crud.user_to_dict(user)
