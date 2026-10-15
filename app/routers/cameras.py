from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models import Camera, User
from app.response import ok

router = APIRouter(prefix="/api", tags=["cameras"])

@router.get("/cameras")
def list_camera(
    db:Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = db.scalars(select(Camera).order_by(Camera.id))
    return ok(
        [
            {
                "id": row.id,
                "name": row.name,
                "hall_name": row.hall_name,
                "stream_url": row.stream_url,
                "status": row.status,
            }
            for row in rows
        ]
    )