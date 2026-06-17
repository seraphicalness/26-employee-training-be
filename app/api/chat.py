import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import get_db
from ..llm import get_chat_response, normalize_topic_id
from ..request_payload import pick, read_payload
from ..schemas import ChatHistoryResponse, ChatResponse, ChatSessionsResponse, ChatStatsResponse
from ..utils import extract_text_from_file

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _session_history_response(db: Session, session: models.ChatSession | None) -> dict:
    if not session:
        return {"session_id": None, "topic_id": None, "messages": []}

    messages = crud.get_chat_history(db, session_id=session.id)
    return {
        **crud.chat_session_to_dict(session),
        "messages": [crud.chat_message_to_dict(message) for message in messages],
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_id = str(uuid.uuid4())
    text = await extract_text_from_file(file)

    uploaded_file = models.UploadedFile(
        file_id=file_id,
        filename=file.filename or "uploaded_file",
        content=text,
    )
    db.add(uploaded_file)
    db.commit()

    return {"file_id": file_id, "filename": file.filename}


@router.post("/start", response_model=ChatHistoryResponse)
@router.post("/new", response_model=ChatHistoryResponse)
async def start_chat(request: Request, db: Session = Depends(get_db)):
    payload = await read_payload(request)
    user = crud.get_or_create_user(db)
    topic_id = normalize_topic_id(
        pick(
            payload,
            "topic_id",
            "topicId",
            "topic",
            "selected_training",
            "selectedTraining",
            default=user.selected_training,
        )
    )
    title = pick(payload, "title", "name")

    session = crud.create_chat_session(db, topic_id=topic_id, title=title)
    crud.update_selected_training(db, topic_id)
    return _session_history_response(db, session)


@router.get("/sessions", response_model=ChatSessionsResponse)
async def get_chat_sessions(request: Request, db: Session = Depends(get_db)):
    topic_id = pick(
        dict(request.query_params),
        "topic_id",
        "topicId",
        "topic",
        "selected_training",
        "selectedTraining",
    )
    normalized_topic_id = normalize_topic_id(topic_id) if topic_id else None
    sessions = crud.list_chat_sessions(db, topic_id=normalized_topic_id)
    return {"sessions": [crud.chat_session_to_dict(session) for session in sessions]}


@router.get("/latest", response_model=ChatHistoryResponse)
async def get_latest_chat(request: Request, db: Session = Depends(get_db)):
    query = dict(request.query_params)
    session_id = pick(
        query,
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "chat_id",
        "chatId",
    )
    topic_id = pick(
        query,
        "topic_id",
        "topicId",
        "topic",
        "selected_training",
        "selectedTraining",
    )

    session = crud.get_chat_session(db, session_id)
    if not session:
        normalized_topic_id = normalize_topic_id(topic_id) if topic_id else None
        session = crud.get_latest_chat_session(db, topic_id=normalized_topic_id)

    return _session_history_response(db, session)


@router.get("/session/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    session = crud.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return _session_history_response(db, session)


@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(db: Session = Depends(get_db)):
    return crud.get_chat_stats(db)


@router.post("/send", response_model=ChatResponse)
async def send_message(request: Request, db: Session = Depends(get_db)):
    payload = await read_payload(request)
    session_id = pick(
        payload,
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "chat_id",
        "chatId",
    )
    topic_id = pick(
        payload,
        "topic_id",
        "topicId",
        "topic",
        "selected_training",
        "selectedTraining",
    )
    message = pick(payload, "message", "content", "text", "input")
    file_id = pick(payload, "file_id", "fileId", "file")

    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    user = crud.get_or_create_user(db)
    normalized_topic_id = normalize_topic_id(topic_id or user.selected_training)
    session = crud.get_chat_session(db, session_id)
    if not session:
        session = crud.get_or_create_chat_session(db, topic_id=normalized_topic_id)

    context = ""
    if file_id:
        uploaded_file = db.get(models.UploadedFile, file_id)
        if uploaded_file:
            context = uploaded_file.content

    prompt = crud.get_or_create_topic_prompt(db, session.topic_id)

    existing_messages = crud.get_chat_history(db, session_id=session.id, limit=1)
    if not existing_messages and session.title.endswith("새 대화"):
        session.title = message[:40]

    started_at = time.perf_counter()
    response_text = await get_chat_response(
        topic_id=session.topic_id,
        message=message,
        custom_instruction=prompt.personal_instruction,
        context=context,
    )
    response_time_ms = int((time.perf_counter() - started_at) * 1000)

    crud.save_chat_exchange(
        db,
        session=session,
        user_message=message,
        assistant_message=response_text,
        response_time_ms=response_time_ms,
    )
    crud.update_selected_training(db, session.topic_id)

    return ChatResponse(
        response=response_text,
        suggestions=None,
        session_id=session.id,
        topic_id=session.topic_id,
        response_time_ms=response_time_ms,
    )
