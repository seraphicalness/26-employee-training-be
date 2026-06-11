import os
import uuid

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if DATABASE_URL.startswith("sqlite"):
        _migrate_sqlite()


def _migrate_sqlite():
    with engine.begin() as conn:
        inspector = inspect(conn)
        table_names = inspector.get_table_names()
        if "chat_messages" not in table_names:
            return

        columns = {column["name"] for column in inspector.get_columns("chat_messages")}
        if "session_id" not in columns:
            conn.execute(text("ALTER TABLE chat_messages ADD COLUMN session_id VARCHAR(36)"))

        if "chat_sessions" not in table_names:
            return

        legacy_topics = conn.execute(
            text(
                """
                SELECT topic_id, MIN(created_at) AS created_at, MAX(created_at) AS updated_at
                FROM chat_messages
                WHERE session_id IS NULL
                GROUP BY topic_id
                """
            )
        ).mappings()

        for row in legacy_topics:
            session_id = str(uuid.uuid4())
            conn.execute(
                text(
                    """
                    INSERT INTO chat_sessions (id, topic_id, title, created_at, updated_at)
                    VALUES (:id, :topic_id, :title, :created_at, :updated_at)
                    """
                ),
                {
                    "id": session_id,
                    "topic_id": row["topic_id"],
                    "title": "이전 대화",
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )
            conn.execute(
                text(
                    """
                    UPDATE chat_messages
                    SET session_id = :session_id
                    WHERE session_id IS NULL AND topic_id = :topic_id
                    """
                ),
                {"session_id": session_id, "topic_id": row["topic_id"]},
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
