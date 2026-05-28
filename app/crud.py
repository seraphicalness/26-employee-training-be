from sqlalchemy.orm import Session

from . import models

DEFAULT_USER = {
    "id": 1,
    "name": "신입사원",
    "department": "인사팀",
    "selected_training": "mail",
}

DEFAULT_PERSONAL_INSTRUCTION = "답변은 정확하고 친절하게 해주세요."


def get_or_create_user(db: Session) -> models.UserProfile:
    user = db.get(models.UserProfile, 1)
    if user:
        return user

    user = models.UserProfile(**DEFAULT_USER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def user_to_dict(user: models.UserProfile) -> dict:
    return {
        "name": user.name,
        "department": user.department,
        "selected_training": user.selected_training,
    }


def get_or_create_settings(db: Session) -> models.AppSetting:
    settings = db.get(models.AppSetting, 1)
    if settings:
        return settings

    settings = models.AppSetting(
        id=1,
        personal_instruction=DEFAULT_PERSONAL_INSTRUCTION,
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def settings_to_dict(settings: models.AppSetting) -> dict:
    return {"personal_instruction": settings.personal_instruction}


def create_chat_message(
    db: Session,
    topic_id: str,
    role: str,
    content: str,
) -> models.ChatMessage:
    message = models.ChatMessage(
        topic_id=topic_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_latest_topic_id(db: Session) -> str | None:
    latest_message = (
        db.query(models.ChatMessage)
        .order_by(models.ChatMessage.created_at.desc(), models.ChatMessage.id.desc())
        .first()
    )
    if not latest_message:
        return None
    return latest_message.topic_id


def get_chat_history(
    db: Session,
    topic_id: str | None = None,
    limit: int = 20,
) -> list[models.ChatMessage]:
    query = db.query(models.ChatMessage)
    if topic_id:
        query = query.filter(models.ChatMessage.topic_id == topic_id)

    return list(
        reversed(
            query.order_by(models.ChatMessage.created_at.desc(), models.ChatMessage.id.desc())
            .limit(limit)
            .all()
        )
    )


def chat_message_to_dict(message: models.ChatMessage) -> dict:
    return {
        "id": message.id,
        "topic_id": message.topic_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
