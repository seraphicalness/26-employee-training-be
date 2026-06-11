from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..llm import normalize_topic_id
from ..request_payload import pick, read_payload

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _pick_session_id(payload: dict) -> str | None:
    return pick(
        payload,
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "chat_id",
        "chatId",
    )


def _pick_topic_id(payload: dict) -> str | None:
    topic_id = pick(
        payload,
        "topic_id",
        "topicId",
        "topic",
        "selected_training",
        "selectedTraining",
    )
    return normalize_topic_id(topic_id) if topic_id else None


def _topic_for_prompt(
    payload: dict,
    db: Session,
    prefer_latest_saved: bool,
) -> tuple[str, str | None]:
    session_id = _pick_session_id(payload)
    if session_id:
        session = crud.get_chat_session(db, session_id)
        if session:
            return session.topic_id, session.id

    topic_id = _pick_topic_id(payload)
    if topic_id:
        return topic_id, session_id

    if prefer_latest_saved:
        latest_prompt = crud.get_latest_topic_prompt(db)
        if latest_prompt:
            return latest_prompt.topic_id, session_id

    user = crud.get_or_create_user(db)
    return normalize_topic_id(user.selected_training), session_id


@router.get("/prompt")
async def get_prompt(request: Request, db: Session = Depends(get_db)):
    topic_id, session_id = _topic_for_prompt(
        dict(request.query_params),
        db,
        prefer_latest_saved=True,
    )
    prompt = crud.get_or_create_topic_prompt(db, topic_id)
    return crud.topic_prompt_to_dict(prompt, session_id=session_id)


@router.get("/prompts")
async def get_prompts(db: Session = Depends(get_db)):
    prompts = []
    for topic_id in crud.TOPIC_NAMES:
        prompt = crud.get_or_create_topic_prompt(db, topic_id)
        prompts.append(crud.topic_prompt_to_dict(prompt))
    return {"prompts": prompts}


@router.post("/prompt")
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

    topic_id, session_id = _topic_for_prompt(payload, db, prefer_latest_saved=False)
    prompt = crud.update_topic_prompt(db, topic_id, personal_instruction)
    crud.update_selected_training(db, topic_id)
    return crud.topic_prompt_to_dict(prompt, session_id=session_id)
