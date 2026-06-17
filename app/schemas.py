from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AppBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ChatRequest(AppBaseModel):
    topic_id: str = Field(
        validation_alias=AliasChoices(
            "topic_id",
            "topicId",
            "topic",
            "selected_training",
            "selectedTraining",
        )
    )
    message: str = Field(validation_alias=AliasChoices("message", "content", "text", "input"))
    file_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("file_id", "fileId", "file"),
    )
    session_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "session_id",
            "sessionId",
            "conversation_id",
            "conversationId",
            "chat_id",
            "chatId",
        ),
    )


class ChatResponse(AppBaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    session_id: Optional[str] = None
    topic_id: Optional[str] = None
    response_time_ms: Optional[int] = None


class ChatMessageResponse(AppBaseModel):
    id: int
    session_id: Optional[str] = None
    topic_id: str
    role: str
    content: str
    response_time_ms: Optional[int] = None
    created_at: Optional[str] = None


class ChatSessionResponse(AppBaseModel):
    session_id: str
    topic_id: str
    topic_name: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatHistoryResponse(AppBaseModel):
    session_id: Optional[str] = None
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    title: Optional[str] = None
    messages: List[ChatMessageResponse] = Field(default_factory=list)


class TopicUsageResponse(AppBaseModel):
    topic_id: str
    topic_name: str
    message_count: int
    session_count: int


class RepeatedQuestionResponse(AppBaseModel):
    question: str
    count: int


class ChatStatsResponse(AppBaseModel):
    total_sessions: int
    total_messages: int
    total_user_messages: int
    average_response_time_ms: Optional[float] = None
    topic_usage: List[TopicUsageResponse] = Field(default_factory=list)
    repeated_questions: List[RepeatedQuestionResponse] = Field(default_factory=list)


class ChatSessionsResponse(AppBaseModel):
    sessions: List[ChatSessionResponse] = Field(default_factory=list)


class UserUpdate(AppBaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    selected_training: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("selected_training", "selectedTraining"),
    )


class PromptUpdate(AppBaseModel):
    personal_instruction: str = Field(
        validation_alias=AliasChoices(
            "personal_instruction",
            "personalInstruction",
            "custom_instruction",
            "customInstruction",
            "prompt",
            "instruction",
        )
    )
