import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models

DEFAULT_USER = {
    "id": 1,
    "name": "신입사원",
    "department": "인사팀",
    "selected_training": "mail",
}

DEFAULT_PERSONAL_INSTRUCTION = "답변은 정확하고 친절하게 해주세요."

TOPIC_NAMES = {
    "mail": "메일쓰기",
    "comm": "커뮤니케이션",
    "org": "조직 적응",
    "collab": "협업/태도",
}


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


def update_selected_training(db: Session, topic_id: str) -> models.UserProfile:
    user = get_or_create_user(db)
    user.selected_training = topic_id
    db.commit()
    db.refresh(user)
    return user


def get_or_create_settings(db: Session) -> models.AppSetting:
    settings = db.get(models.AppSetting, 1)
    if settings:
        return settings

    settings = models.AppSetting(id=1, personal_instruction=DEFAULT_PERSONAL_INSTRUCTION)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def settings_to_dict(settings: models.AppSetting) -> dict:
    return {
        "personal_instruction": settings.personal_instruction,
        "personalInstruction": settings.personal_instruction,
        "prompt": settings.personal_instruction,
    }


def get_or_create_topic_prompt(db: Session, topic_id: str) -> models.TopicPrompt:
    prompt = db.get(models.TopicPrompt, topic_id)
    if prompt:
        return prompt

    fallback = get_or_create_settings(db)
    prompt = models.TopicPrompt(
        topic_id=topic_id,
        personal_instruction=fallback.personal_instruction,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def get_latest_topic_prompt(db: Session) -> models.TopicPrompt | None:
    return (
        db.query(models.TopicPrompt)
        .order_by(models.TopicPrompt.updated_at.desc(), models.TopicPrompt.topic_id.asc())
        .first()
    )


def update_topic_prompt(db: Session, topic_id: str, personal_instruction: str) -> models.TopicPrompt:
    prompt = get_or_create_topic_prompt(db, topic_id)
    settings = get_or_create_settings(db)
    prompt.personal_instruction = personal_instruction
    settings.personal_instruction = personal_instruction
    prompt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prompt)
    return prompt


def topic_prompt_to_dict(prompt: models.TopicPrompt, session_id: str | None = None) -> dict:
    return {
        "topic_id": prompt.topic_id,
        "topicId": prompt.topic_id,
        "topic_name": TOPIC_NAMES.get(prompt.topic_id, prompt.topic_id),
        "session_id": session_id,
        "sessionId": session_id,
        "personal_instruction": prompt.personal_instruction,
        "personalInstruction": prompt.personal_instruction,
        "prompt": prompt.personal_instruction,
        "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
    }


def create_chat_session(db: Session, topic_id: str, title: str | None = None) -> models.ChatSession:
    session = models.ChatSession(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        title=title or f"{TOPIC_NAMES.get(topic_id, '교육')} 새 대화",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_session(db: Session, session_id: str | None) -> models.ChatSession | None:
    if not session_id:
        return None
    return db.get(models.ChatSession, session_id)


def get_latest_chat_session(db: Session, topic_id: str | None = None) -> models.ChatSession | None:
    query = db.query(models.ChatSession)
    if topic_id:
        query = query.filter(models.ChatSession.topic_id == topic_id)
    return query.order_by(models.ChatSession.updated_at.desc(), models.ChatSession.created_at.desc()).first()


def get_or_create_chat_session(
    db: Session,
    session_id: str | None = None,
    topic_id: str | None = None,
) -> models.ChatSession:
    session = get_chat_session(db, session_id)
    if session:
        return session

    if topic_id:
        session = get_latest_chat_session(db, topic_id=topic_id)
        if session:
            return session

    return create_chat_session(db, topic_id or DEFAULT_USER["selected_training"])


def list_chat_sessions(
    db: Session,
    topic_id: str | None = None,
    limit: int = 30,
) -> list[models.ChatSession]:
    query = db.query(models.ChatSession)
    if topic_id:
        query = query.filter(models.ChatSession.topic_id == topic_id)
    return query.order_by(models.ChatSession.updated_at.desc(), models.ChatSession.created_at.desc()).limit(limit).all()


def save_chat_exchange(
    db: Session,
    session: models.ChatSession,
    user_message: str,
    assistant_message: str,
    response_time_ms: int | None = None,
) -> tuple[models.ChatMessage, models.ChatMessage]:
    user_row = models.ChatMessage(
        session_id=session.id,
        topic_id=session.topic_id,
        role="user",
        content=user_message,
    )
    assistant_row = models.ChatMessage(
        session_id=session.id,
        topic_id=session.topic_id,
        role="assistant",
        content=assistant_message,
        response_time_ms=response_time_ms,
    )
    session.updated_at = datetime.utcnow()
    db.add(user_row)
    db.add(assistant_row)
    db.commit()
    db.refresh(user_row)
    db.refresh(assistant_row)
    db.refresh(session)
    return user_row, assistant_row


def get_chat_history(
    db: Session,
    session_id: str | None = None,
    topic_id: str | None = None,
    limit: int = 50,
) -> list[models.ChatMessage]:
    query = db.query(models.ChatMessage)
    if session_id:
        query = query.filter(models.ChatMessage.session_id == session_id)
    elif topic_id:
        query = query.filter(models.ChatMessage.topic_id == topic_id)

    return list(
        reversed(
            query.order_by(models.ChatMessage.created_at.desc(), models.ChatMessage.id.desc())
            .limit(limit)
            .all()
        )
    )


def chat_session_to_dict(session: models.ChatSession) -> dict:
    return {
        "session_id": session.id,
        "topic_id": session.topic_id,
        "topic_name": TOPIC_NAMES.get(session.topic_id, session.topic_id),
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


def chat_message_to_dict(message: models.ChatMessage) -> dict:
    return {
        "id": message.id,
        "session_id": message.session_id,
        "topic_id": message.topic_id,
        "role": message.role,
        "content": message.content,
        "response_time_ms": message.response_time_ms,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def get_chat_stats(db: Session) -> dict:
    topic_usage = [
        {
            "topic_id": topic_id,
            "topic_name": TOPIC_NAMES.get(topic_id, topic_id),
            "message_count": message_count,
            "session_count": session_count,
        }
        for topic_id, message_count, session_count in (
            db.query(
                models.ChatSession.topic_id,
                func.count(models.ChatMessage.id),
                func.count(func.distinct(models.ChatSession.id)),
            )
            .outerjoin(models.ChatMessage, models.ChatMessage.session_id == models.ChatSession.id)
            .group_by(models.ChatSession.topic_id)
            .order_by(func.count(models.ChatMessage.id).desc(), models.ChatSession.topic_id.asc())
            .all()
        )
    ]

    repeated_questions = [
        {
            "question": question,
            "count": count,
        }
        for question, count in (
            db.query(models.ChatMessage.content, func.count(models.ChatMessage.id))
            .filter(models.ChatMessage.role == "user")
            .group_by(models.ChatMessage.content)
            .having(func.count(models.ChatMessage.id) > 1)
            .order_by(func.count(models.ChatMessage.id).desc(), models.ChatMessage.content.asc())
            .limit(10)
            .all()
        )
    ]

    avg_response_time = (
        db.query(func.avg(models.ChatMessage.response_time_ms))
        .filter(
            models.ChatMessage.role == "assistant",
            models.ChatMessage.response_time_ms.isnot(None),
        )
        .scalar()
    )

    return {
        "total_sessions": db.query(func.count(models.ChatSession.id)).scalar() or 0,
        "total_messages": db.query(func.count(models.ChatMessage.id)).scalar() or 0,
        "total_user_messages": db.query(func.count(models.ChatMessage.id))
        .filter(models.ChatMessage.role == "user")
        .scalar()
        or 0,
        "average_response_time_ms": round(float(avg_response_time), 2) if avg_response_time is not None else None,
        "topic_usage": topic_usage,
        "repeated_questions": repeated_questions,
    }
