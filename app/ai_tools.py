"""大模型可调用的查询工具。只读数据库，不改画面。"""
#这个文件用来把白名单翻译成 AI 能看懂的"工具说明书"
import json

from sqlalchemy import select

from app.models import Alarm, EnergyReading
from app.ai_actions import ACTIONS, CommandError, check_command
from app.routers.scene import _ensure_device_type, _query_devices, _query_hall

ALARM_LEVELS = ["一般", "重要", "严重"]
ALARM_STATUSES = ["未处理", "处理中", "已处理"]


def _enum(value, allowed, label):
    if not value:
        return None
    if value not in allowed:
        raise ValueError(f"{label}不支持：{value}，可选：{'、'.join(allowed)}")
    return value


def query_alarms(db, alarm_level=None, alarm_status=None, alarm_type=None, hall_name=None):
    alarm_level = _enum(alarm_level, ALARM_LEVELS, "告警等级")
    alarm_status = _enum(alarm_status, ALARM_STATUSES, "告警状态")
    stmt = select(Alarm)
    if alarm_level:
        stmt = stmt.where(Alarm.alarm_level == alarm_level)
    if alarm_status:
        stmt = stmt.where(Alarm.alarm_status == alarm_status)
    if alarm_type:
        stmt = stmt.where(Alarm.alarm_type == alarm_type)
    if hall_name:
        stmt = stmt.where(Alarm.hall_name == hall_name)
    rows = db.scalars(stmt.order_by(Alarm.alarm_time.desc())).all()

    by_level = {name: 0 for name in ALARM_LEVELS}
    by_status = {name: 0 for name in ALARM_STATUSES}
    by_type = {}
    for row in rows:
        by_level[row.alarm_level] = by_level.get(row.alarm_level, 0) + 1
        by_status[row.alarm_status] = by_status.get(row.alarm_status, 0) + 1
        by_type[row.alarm_type] = by_type.get(row.alarm_type, 0) + 1
    return {
        "total": len(rows),
        "by_level": by_level,
        "by_status": by_status,
        "by_type": by_type,
        "items": [
            {
                "alarm_time": row.alarm_time,
                "alarm_level": row.alarm_level,
                "alarm_type": row.alarm_type,
                "alarm_status": row.alarm_status,
                "hall_name": row.hall_name,
                "alarm_content": row.alarm_content,
            }
            for row in rows[:10]
        ],
    }


def query_energy(db, kind=None, period="月"):
    kind = _enum(kind, ["电", "水"], "能耗类型")
    period = _enum(period or "月", ["日", "月"], "统计周期")
    stmt = select(EnergyReading).where(EnergyReading.period == period)
    if kind:
        stmt = stmt.where(EnergyReading.kind == kind)
    rows = db.scalars(stmt.order_by(EnergyReading.period_key.desc())).all()
    series = {}
    for row in rows:
        bucket = series.setdefault(row.kind, [])
        if len(bucket) >= 6:
            continue
        bucket.append({"period_key": row.period_key, "value": row.value, "unit": row.unit})
    return {"period": period, "series": series}

def run_screen(db, name, arguments):
    """画面指令只校验。3D 在浏览器里，这里执行不了。"""
    checked = check_command({"action": name, "params": arguments})
    if name == "showDevice":
        _ensure_device_type(db, checked["params"]["device"])
    return {**checked, "ok": True, "data": None}


def run_tool(db, name, arguments):
    """执行一个工具。参数不合法时返回 error，让模型改口，而不是把异常抛给用户。"""
    try:
        if name in ACTIONS and ACTIONS[name][0] == "screen":
            return run_screen(db, name, arguments)
        if name == "query_alarms":
            return query_alarms(db, **arguments)
        if name == "query_energy":
            return query_energy(db, **arguments)
        if name == "query_devices":
            _message, data = _query_devices(db, arguments)
            return data
        if name == "query_hall":
            _message, data = _query_hall(db, arguments.get("name"))
            return data
    except (ValueError, CommandError, TypeError) as error:
        return {"error": str(error)}
    return {"error": f"不支持的查询：{name}"}


def _tool(name, description, properties, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }

#把白名单翻译成 AI 能看懂的"工具说明书"
TOOLS = [
    _tool(
        "query_alarms",
        "查询告警记录和数量。用户问告警、未处理、严重告警时调用。没有查到就说明没有，不要编造数量。",
        {
            "alarm_level": {"type": "string", "enum": ALARM_LEVELS, "description": "告警等级"},
            "alarm_status": {"type": "string", "enum": ALARM_STATUSES, "description": "处理状态"},
            "alarm_type": {"type": "string", "description": "告警类型，如 AI视频告警、入侵告警、消防告警、设备告警"},
            "hall_name": {"type": "string", "description": "场馆名称，如 1号馆"},
        },
    ),
    _tool(
        "query_energy",
        "查询用电或用水。用户问电、水、能耗时调用。series 按时间从新到旧，第一条是最近一期。",
        {
            "kind": {"type": "string", "enum": ["电", "水"], "description": "不填则电和水都返回"},
            "period": {"type": "string", "enum": ["日", "月"], "description": "默认按月"},
        },
    ),
    _tool(
        "query_devices",
        "统计设备在线、离线、故障数量。用户问设备状态时调用。",
        {
            "hall_name": {"type": "string", "description": "场馆名称"},
            "leaf_type": {"type": "string", "description": "设备类型，如 门禁、电表"},
            "status": {"type": "string", "enum": ["在线", "离线", "故障"]},
            "category": {"type": "string", "description": "监控设备、安防设备、楼宇自控、能效设备"},
        },
    ),
    _tool(
        "query_hall",
        "查看一个场馆的面积、层数、容量和介绍。",
        {"name": {"type": "string", "description": "场馆名称，如 1号馆、主登录厅"}},
        ["name"],
    ),
    _tool("navigate", "切换大屏页面。用户要看综合态势、安防、设备、能源、会展时调用。", {
        "page": {
            "type": "string",
            "description": "comSituation 综合态势，secSituation 安防态势，device 设备运行，energy 能源管理，convention 会展信息。也可传中文。",
            },
        },
        ["page"]),
    _tool("overview", "回到总览视角。", {}),
    _tool("showVenueLabels", "显示所有场馆名称标签。", {}),
    _tool(
        "selectBuilding",
        "镜头定位到某个场馆。用户说切到几号馆、看登录厅时调用。",
        {"building": {"type": "string", "description": "1号馆到16号馆，或主登录厅、次登录厅、东登录厅。也可以只传数字，如 5。"}},
        ["building"],
        ),
    _tool(
        "selectFloor",
        "展开或收起当前场馆的楼层。需要已经选中场馆。",
        {"floor": {"type": "string", "enum": ["1F", "恢复", "全部展开"], "description": "一层用 1F，收起用 恢复，展开用 全部展开。"}},
        ["floor"],
        ),
    _tool(
        "toggleHeatmap",
        "打开或关闭人流热力图。",
        {"visible": {"type": "boolean", "description": "true 显示，false 关闭。不传则显示。"}},
    ),
    _tool(
        "openDeviceCategory",
        "打开设备分类面板。",
        {"category": {"type": "string", "enum": ["监控设备", "安防设备", "楼宇自控", "能效设备"]}},
        ["category"],
    ),
   _tool(
        "showDevice",
        "选中一类设备并显示它的 3D 标签。device 必须是库里真实的设备类型。",
        {"device": {"type": "string", "description": "如 门禁、停车场道闸、电表、水表、入侵探测器、空调用电、照明。"}},
        ["device"],
    ),
    ]


def tool_result_message(call, result):
    return {
        "role": "tool",
        "tool_call_id": call["id"],
        "content": json.dumps(result, ensure_ascii=False),
    }
