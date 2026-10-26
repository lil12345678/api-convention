from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse


# from app.ai_chat import ChatError, chat_turn
from app.database import get_db
from app.models import User
from app.deps import get_current_user
from app. response import ok
from app.ai_chat import ChatError, chat_turn, iter_chat_events
from app.chat_store import session_payload
from app.rate_limit import check_chat_rate

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    role:str
    content:str = Field(..., min_length=1, max_length=2000)

class ChatIn(BaseModel):
    messages:list[ChatRequest] = Field(min_length=1, max_length=20)

#非流式对话
@router.post("/chat")
def chat(
    body:ChatIn,
    db:Session = Depends(get_db),
    _user:User = Depends(get_current_user),
    ):
    check_chat_rate(_user.id)
    try:
        data = chat_turn(db, [item.model_dump() for item in body.messages])
    except ChatError as error:
        raise HTTPException(error.status, error.message)
    return ok(data)

#流式对话
@router.post("/chat/stream")
def chat_stream(
    body:ChatIn,
    _user:User = Depends(get_current_user),
):
    check_chat_rate(_user.id)
    history = [item.model_dump() for item in body.messages]
    return StreamingResponse(
        iter_chat_events(history, _user.id), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
        )

#获取对话历史
@router.get("/chat/session")
def chat_session(
    db:Session = Depends(get_db),
    _user:User = Depends(get_current_user),
):
    return ok(session_payload(db, _user.id))