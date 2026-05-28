import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import get_db
from ..llm import get_chat_response, normalize_topic_id
from ..request_payload import pick, read_payload
from ..schemas import ChatHistoryResponse, ChatResponse
from ..utils import extract_text_from_file

router = APIRouter(prefix="/api/chat", tags=["chat"])


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


@router.get("/latest", response_model=ChatHistoryResponse)
async def get_latest_chat(request: Request, db: Session = Depends(get_db)):
    topic_id = pick(
        dict(request.query_params),
        "topic_id",
        "topicId",
        "topic",
        "selected_training",
        "selectedTraining",
    )

    if topic_id:
        topic_id = normalize_topic_id(topic_id)
    else:
        topic_id = crud.get_latest_topic_id(db)

    messages = crud.get_chat_history(db, topic_id=topic_id) if topic_id else []
    return {
        "topic_id": topic_id,
        "messages": [crud.chat_message_to_dict(message) for message in messages],
    }


@router.post("/send", response_model=ChatResponse)
async def send_message(request: Request, db: Session = Depends(get_db)):
    payload = await read_payload(request)
    topic_id = normalize_topic_id(
        pick(
            payload,
            "topic_id",
            "topicId",
            "topic",
            "selected_training",
            "selectedTraining",
            default="mail",
        )
    )
    message = pick(payload, "message", "content", "text", "input")
    file_id = pick(payload, "file_id", "fileId", "file")

    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    context = ""
    if file_id:
        uploaded_file = db.get(models.UploadedFile, file_id)
        if uploaded_file:
            context = uploaded_file.content

    settings = crud.get_or_create_settings(db)

    response_text = await get_chat_response(
        topic_id=topic_id,
        message=message,
        custom_instruction=settings.personal_instruction,
        context=context,
    )

    crud.create_chat_message(db, topic_id=topic_id, role="user", content=message)
    crud.create_chat_message(db, topic_id=topic_id, role="assistant", content=response_text)

    return ChatResponse(
        response=response_text,
        suggestions=["추가 질문이 있으신가요?", "이 부분을 더 자세히 설명해드릴까요?"],
    )
