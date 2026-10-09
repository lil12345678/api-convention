from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from app.response import ok, register_exception_handlers

from app.database import Base, engine, SessionLocal
from app.deps import get_current_user
from app.models import (
    User,
    Hall, 
    Device, 
    Exhibition, 
    ExhibitionEvent, Alarm, WorkOrder, EnergyReading,
    ParkingStat, CrowdStat, HeatmapPoint, EmergencyRecord
  )  # 必须导入，create_all 才能看到这张表
from app.seed import (
    seed_users_if_empty,
    seed_halls_if_empty, seed_devices_if_empty, seed_exhibitions_if_empty, seed_alarms_if_empty, 
    seed_work_orders_if_empty, seed_energy_readings_if_empty, 
    seed_parking_if_empty, seed_crowd_if_empty, seed_heatmap_if_empty, seed_emergency_if_empty
)

app = FastAPI(
    title="api-convention",
    description="会展大屏后端",
    version="0.1.0",
)

#挂载路由
from app.routers.auth import router as auth_router
register_exception_handlers(app)
app.include_router(auth_router)

# 创建所有表
Base.metadata.create_all(bind=engine)# 创建所有表，bind=engine 绑定引擎，用于创建表。
seed_halls_if_empty()# 填充场馆数据
seed_devices_if_empty()# 填充设备数据
seed_exhibitions_if_empty()# 填充展会数据
seed_alarms_if_empty()# 填充告警数据
seed_work_orders_if_empty()# 填充工单数据
seed_energy_readings_if_empty()# 填充能源读数数据
seed_parking_if_empty()# 填充停车场数据
seed_crowd_if_empty()# 填充人群数据
seed_heatmap_if_empty()# 填充热力图数据
seed_emergency_if_empty()# 填充应急数据
seed_users_if_empty()# 填充用户数据

app.add_middleware(# 添加中间件，用于处理跨域请求
    CORSMiddleware,
    allow_origins=[# 允许跨域请求的源
        "http://localhost:3000",# 本地开发环境
        "http://127.0.0.1:3000",# 本地开发环境
    ],
    allow_credentials=True,# 允许跨域请求的凭证
    allow_methods=["*"],# 允许跨域请求的方法
    allow_headers=["*"],# 允许跨域请求的头
)


@app.get("/health")
def health():
    return ok({"status": "ok"})


def hall_to_dict(hall: Hall): # 将数据库里的场馆对象转换为字典，用于返回给前端
    return {
        "name": hall.name,
        "sort_order": hall.sort_order,
        "hall_type": hall.hall_type,
        "area_sqm": hall.area_sqm,
        "floors": hall.floors,
        "height_m": hall.height_m,
        "capacity": hall.capacity,
        "x": hall.x,
        "y": hall.y,
        "z": hall.z,
        "intro": hall.intro,
    }

@app.get("/api/halls")
def list_halls(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(Hall).order_by(Hall.sort_order)).all()
        return ok([hall_to_dict(row) for row in rows])
    finally:
        db.close()


@app.get("/api/halls/{name}")
def get_hall(name: str, _user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        hall = db.get(Hall, name)
        if hall is None:
            raise HTTPException(status_code=404, detail=f"未找到场馆：{name}")
        return ok(hall_to_dict(hall))
    finally:
        db.close()

def device_to_dict(device: Device):
    return {
        "id": device.id,
        "code": device.code,
        "name": device.name,
        "category": device.category,
        "category_name": device.category_name,
        "leaf_type": device.leaf_type,
        "group_name": device.group_name,
        "hall_name": device.hall_name,
        "status": device.status,
        "floor": device.floor,
    }
@app.get("/api/devices")
def list_devices(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(Device).order_by(Device.id)).all()
        return ok([device_to_dict(row) for row in rows])
    finally:
        db.close()

@app.get("/api/devices/count")
def get_devices_count(_user: User = Depends(get_current_user)):
   # 输入：无
    # 输出：三种状态各有多少台，例如 {"在线": 40, "离线": 30, "故障": 14}
    # 读表：devices 的 status
    db = SessionLocal()
    try:
        result = {}
        for status in ["在线", "离线", "故障"]:
            result[status] = db.scalar(
                select(func.count()).select_from(Device).where(Device.status == status)
            )
        return ok(result)
    finally:
        db.close()

def exhibition_to_dict(item: Exhibition):
    return {
        "id": item.id,
        "name": item.name,
        "year": item.year,
        "month": item.month,
        "hall_name": item.hall_name,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "visitors": item.visitors,
        "status": item.status,
    }


def exhibition_event_to_dict(item: ExhibitionEvent):
    return {
        "id": item.id,
        "exhibition_id": item.exhibition_id,
        "event_type": item.event_type,
        "title": item.title,
        "location": item.location,
        "room": item.room,
        "start_time": item.start_time,
        "hall_name": item.hall_name,
    }


@app.get("/api/exhibitions")
def list_exhibitions(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Exhibition).order_by(Exhibition.start_date.desc())
        ).all()
        return ok([exhibition_to_dict(row) for row in rows])
    finally:
        db.close()


@app.get("/api/exhibition-events")
def list_exhibition_events(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(ExhibitionEvent).order_by(ExhibitionEvent.start_time)
        ).all()
        return ok([exhibition_event_to_dict(row) for row in rows])
    finally:
        db.close()

def alarm_to_dict(item: Alarm):
    return {
        "id": item.id,
        "device_id": item.device_id,
        "hall_name": item.hall_name,
        "scope": item.scope,
        "alarm_type": item.alarm_type,
        "alarm_level": item.alarm_level,
        "alarm_time": item.alarm_time,
        "alarm_content": item.alarm_content,
        "alarm_status": item.alarm_status,
    }

@app.get("/api/alarms")
def list_alarms(
    alarm_level:str | None = None,
    year: int | None = None,
    month: int | None = None,
    _user: User = Depends(get_current_user)
):
 # 输入：等级、年、月都可以不填
    # 输出：告警列表。填了的条件都要满足
    # 读表：alarms。年、月看的是 alarm_time 开头的 2026-09
    db = SessionLocal() # 获取数据库会话
    try:
        stmt = select(Alarm).order_by(Alarm.alarm_time.desc())
        if alarm_level:
            stmt = stmt.where(Alarm.alarm_level == alarm_level)
        if year is not None and month is not None:
            prefix = f"{year:04d}-{month:02d}"
            stmt = stmt.where(Alarm.alarm_time.like(prefix + "%"))
        rows = db.scalars(stmt).all()
        return ok([alarm_to_dict(row) for row in rows])
    finally:
        db.close()

def work_order_to_dict(item: WorkOrder):
    return {
        "id": item.id,
        "device_id": item.device_id,
        "hall_name": item.hall_name,
        "order_type": item.order_type,
        "source": item.source,
        "level": item.level,
        "title": item.title,
        "status": item.status,
        "overdue": item.overdue,
        "created_at": item.created_at,
    }

@app.get("/api/work-orders")
def list_work_orders(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(WorkOrder).order_by(WorkOrder.created_at.desc())).all()
        return ok([work_order_to_dict(row) for row in rows])
    finally:
        db.close()

def energy_to_dict(item: EnergyReading):
    return {
        "id": item.id,
        "kind": item.kind,
        "unit": item.unit,
        "period": item.period,
        "period_key": item.period_key,
        "value": item.value,
    }

@app.get("/api/energy")
def list_energy(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(EnergyReading).order_by(
                EnergyReading.period_key.desc(),
                EnergyReading.kind,
                )
            ).all()
        return ok([energy_to_dict(row) for row in rows])
    finally:
        db.close()

def parking_to_dict(item: ParkingStat):
    free_spaces = item.total_spaces - item.used_spaces
    usage_rate = 0
    if item.total_spaces:
        usage_rate = round(item.used_spaces / item.total_spaces * 100)
    return {
        "id": item.id,
        "total_spaces": item.total_spaces,
        "used_spaces": item.used_spaces,
        "free_spaces": free_spaces,
        "usage_rate": usage_rate,
        "social_vehicles": item.social_vehicles,
        "logistics_vehicles": item.logistics_vehicles,
        "work_vehicles": item.work_vehicles,
    }

@app.get("/api/parking")
def get_parking(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        item = db.scalar(select(ParkingStat).limit(1))
        if item is None:
            raise HTTPException(status_code=404, detail="未找到车位数据")
        return ok(parking_to_dict(item))
    finally:
        db.close()

def crowd_to_dict(item: CrowdStat):
    return {
        "id": item.id,
        "hall_name": item.hall_name,   
        "headcount": item.headcount,
    }

@app.get("/api/crowd")
def list_crowd(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(CrowdStat).order_by(CrowdStat.id)).all()
        items = [crowd_to_dict(row) for row in rows]
        total = sum(item["headcount"] for item in items)
        return ok({"total":total, "items":items})
    finally:
        db.close()

def heatmap_to_dict(item: HeatmapPoint):
    return {
        "id": item.id,
        "hall_name": item.hall_name,
        "x": item.x,
        "y": item.y,
        "value": item.value,
    }

@app.get("/api/heatmap")
def list_heatmap(hall: str, _user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(select(HeatmapPoint).where(HeatmapPoint.hall_name == hall).order_by(HeatmapPoint.id)).all()
        items = [heatmap_to_dict(row) for row in rows]
        if not rows:
            raise HTTPException(status_code=404, detail=f"未找到场馆：{hall}")
        return ok([heatmap_to_dict(row) for row in rows])
    finally:
        db.close()

def emergency_to_dict(item: EmergencyRecord):
    return {
        "id": item.id,
        "record_type": item.record_type,
        "name": item.name,
        "period": item.period,
        "period_key": item.period_key,
        "value": item.value,
    }

@app.get("/api/emergency")
def list_emergency(_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(EmergencyRecord).order_by(
                EmergencyRecord.record_type, 
                EmergencyRecord.period_key.desc(),
            EmergencyRecord.name
            )).all()
        return ok([emergency_to_dict(row) for row in rows])
    finally:
        db.close()