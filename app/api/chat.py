from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import Optional
import uuid
from ..schemas import ChatRequest, ChatResponse
from ..llm import get_chat_response
from ..utils import extract_text_from_file

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 임시 파일 저장소 (메모리)
temp_file_storage = {}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    text = await extract_text_from_file(file)
    temp_file_storage[file_id] = {
        "filename": file.filename,
        "content": text
    }
    return {"file_id": file_id, "filename": file.filename}

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    context = ""
    if request.file_id and request.file_id in temp_file_storage:
        context = temp_file_storage[request.file_id]["content"]
    
    # 여기서 DB에서 사용자의 custom_instruction을 가져오는 로직이 필요함 (현재는 빈 값)
    response_text = await get_chat_response(
        topic_id=request.topic_id,
        message=request.message,
        context=context
    )
    
    return ChatResponse(
        response=response_text,
        suggestions=["추가 질문이 있으신가요?", "이 부분을 더 자세히 설명해드릴까요?"]
    )
