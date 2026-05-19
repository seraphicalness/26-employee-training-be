from fastapi import APIRouter
from ..schemas import UserUpdate

router = APIRouter(prefix="/api/user", tags=["user"])

# 임시 유저 정보 (메모리)
user_info = {
    "name": "홍길동",
    "department": "인사팀",
    "selected_training": "mail"
}

@router.get("/me")
async def get_me():
    return user_info

@router.put("/me")
async def update_me(update: UserUpdate):
    if update.name:
        user_info["name"] = update.name
    if update.department:
        user_info["department"] = update.department
    if update.selected_training:
        user_info["selected_training"] = update.selected_training
    return user_info
