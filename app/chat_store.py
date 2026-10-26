from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession


def current_session(db: Session, user_id: int) -> ChatSession:
    session = db.scalar(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.id.desc())
        .limit(1)
    )
    if session is not None:
        return session
    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def session_payload(db: Session, user_id: int) -> dict:
    session = current_session(db, user_id)
    rows = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id)
    ).all()
    return {
        "session_id": session.id,
        "messages": [
            {"id": row.id, "role": row.role, "content": row.content}
            for row in rows
        ],
    }


def save_user_message(db: Session, user_id: int, content: str) -> None:
    text = str(content or "").strip()
    if not text:
        return
    session = current_session(db, user_id)
    db.add(ChatMessage(session_id=session.id, role="user", content=text))
    db.commit()


def save_assistant_message(db: Session, user_id: int, content: str) -> None:
    text = str(content or "").strip()
    if not text:
        return
    session = current_session(db, user_id)
    db.add(ChatMessage(session_id=session.id, role="assistant", content=text))
    db.commit()