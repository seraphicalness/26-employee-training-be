from typing import Optional, List

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


class ChatResponse(AppBaseModel):
    response: str
    suggestions: Optional[List[str]] = None


class ChatMessageResponse(AppBaseModel):
    id: int
    topic_id: str
    role: str
    content: str
    created_at: Optional[str] = None


class ChatHistoryResponse(AppBaseModel):
    topic_id: Optional[str] = None
    messages: List[ChatMessageResponse] = Field(default_factory=list)


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
