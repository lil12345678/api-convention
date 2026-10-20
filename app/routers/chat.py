from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_chat import ChatError, chat_turn
from app.database import get_db
from app.models import User
from app.deps import get_current_user
from app. response import ok

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    role:str
    content:str = Field(..., min_length=1, max_length=2000)

class ChatIn(BaseModel):
    messages:list[ChatRequest] = Field(min_length=1, max_length=20)


@router.post("/chat")
def chat(
    body:ChatIn,
    db:Session = Depends(get_db),
    _user:User = Depends(get_current_user),
    ):
    try:
        data = chat_turn(db, [item.model_dump() for item in body.messages])
    except ChatError as error:
        raise HTTPException(error.status, error.message)
    return ok(data)

