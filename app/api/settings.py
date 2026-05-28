from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..request_payload import pick, read_payload

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/prompt")
async def get_prompt(db: Session = Depends(get_db)):
    settings = crud.get_or_create_settings(db)
    return crud.settings_to_dict(settings)


@router.put("/prompt")
async def update_prompt(request: Request, db: Session = Depends(get_db)):
    payload = await read_payload(request)
    personal_instruction = pick(
        payload,
        "personal_instruction",
        "personalInstruction",
        "custom_instruction",
        "customInstruction",
        "prompt",
        "instruction",
    )

    if personal_instruction is None:
        raise HTTPException(status_code=400, detail="Missing personal_instruction")

    settings = crud.get_or_create_settings(db)
    settings.personal_instruction = personal_instruction

    db.commit()
    db.refresh(settings)
    return crud.settings_to_dict(settings)
