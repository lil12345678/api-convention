from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_actions import ACTIONS, CommandError, action_catalog, check_command
from app.database import get_db
from app.deps import get_current_user
from app.models import Device, Hall, User
from app.response import ok

router = APIRouter(prefix="/api/scene", tags=["scene"])


class CommandIn(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)


def _leaf_types(db):
    return db.scalars(select(Device.leaf_type).distinct().order_by(Device.leaf_type)).all()


def _ensure_device_type(db, leaf_type):
    found = db.scalar(select(Device.id).where(Device.leaf_type == leaf_type).limit(1))
    if found is None:
        names = "、".join(_leaf_types(db))
        raise CommandError(f"没有这种设备：{leaf_type}，可选：{names}")


def _query_devices(db, params):
    if params.get("leaf_type"):
        _ensure_device_type(db, params["leaf_type"])
    if params.get("hall_name") and db.get(Hall, params["hall_name"]) is None:
        raise CommandError(f"没有这个场馆：{params['hall_name']}")

    stmt = select(Device)
    if params.get("hall_name"):
        stmt = stmt.where(Device.hall_name == params["hall_name"])
    if params.get("leaf_type"):
        stmt = stmt.where(Device.leaf_type == params["leaf_type"])
    if params.get("status"):
        stmt = stmt.where(Device.status == params["status"])
    if params.get("category"):
        stmt = stmt.where(Device.category_name == params["category"])
    rows = db.scalars(stmt.order_by(Device.id)).all()

    by_status = {"在线": 0, "离线": 0, "故障": 0}
    by_type = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
        item = by_type.setdefault(
            row.leaf_type,
            {"leaf_type": row.leaf_type, "total": 0, "在线": 0, "离线": 0, "故障": 0},
        )
        item["total"] += 1
        item[row.status] = item.get(row.status, 0) + 1

    shown = rows[:20]
    message = f"共 {len(rows)} 台，在线 {by_status['在线']}，离线 {by_status['离线']}，故障 {by_status['故障']}"
    if len(rows) > len(shown):
        message += "，仅列出前 20 台"
    return message, {
        "total": len(rows),
        "by_status": by_status,
        "by_type": list(by_type.values()),
        "items": [
            {
                "name": row.name,
                "code": row.code,
                "leaf_type": row.leaf_type,
                "status": row.status,
                "hall_name": row.hall_name,
                "floor": row.floor,
                "model": row.model,
                "scene_node": row.scene_node,
            }
            for row in shown
        ],
    }


def _query_hall(db, name):
    hall = db.get(Hall, name)
    if hall is None:
        raise CommandError(f"没有这个场馆：{name}")
    data = {
        "name": hall.name,
        "hall_type": hall.hall_type,
        "area_sqm": hall.area_sqm,
        "floors": hall.floors,
        "height_m": hall.height_m,
        "capacity": hall.capacity,
        "intro": hall.intro,
    }
    message = (
        f"{hall.name}，{hall.hall_type}，面积 {hall.area_sqm}㎡，"
        f"{hall.floors} 层，可容纳 {hall.capacity} 人"
    )
    return message, data


def _run_one(command, db):
    checked = check_command(command)
    if checked["action"] == "showDevice":
        _ensure_device_type(db, checked["params"]["device"])
    if checked["kind"] == "screen":
        return {**checked, "ok": True, "data": None}
    if checked["action"] == "queryDevices":
        message, data = _query_devices(db, checked["params"])
    else:
        message, data = _query_hall(db, checked["params"]["name"])
    return {**checked, "ok": True, "message": message, "data": data}


@router.get("/actions")
def list_actions(_user: User = Depends(get_current_user)):
    return ok(action_catalog())


@router.post("/command")
def scene_command(
    body: CommandIn | list[CommandIn],
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # 和前端一样：按顺序执行，第一条失败就停
    commands = body if isinstance(body, list) else [body]
    results = []
    for item in commands:
        raw = item.model_dump()
        try:
            results.append(_run_one(raw, db))
        except CommandError as error:
            results.append(
                {
                    "action": raw.get("action"),
                    "params": raw.get("params") or {},
                    "kind": ACTIONS.get(raw.get("action"), (None,))[0],
                    "ok": False,
                    "message": str(error),
                    "data": None,
                }
            )
            return ok({"ok": False, "results": results})
    return ok({"ok": True, "results": results})