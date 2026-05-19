from fastapi import APIRouter
from ..schemas import PromptUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

# 임시 맞춤 프롬프트 (메모리)
settings = {
    "personal_instruction": "답변을 정중하고 친절하게 해주세요."
}

@router.get("/prompt")
async def get_prompt():
    return settings

@router.put("/prompt")
async def update_prompt(update: PromptUpdate):
    settings["personal_instruction"] = update.personal_instruction
    return settings
