from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    topic_id: str
    message: str
    file_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    selected_training: Optional[str] = None

class PromptUpdate(BaseModel):
    personal_instruction: str
