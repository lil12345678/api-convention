from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
class Hall(Base):
    __tablename__ = "halls"

    name: Mapped[str] = mapped_column(String(32), primary_key=True) # 场馆名称
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False) # 排序号
    hall_type: Mapped[str] = mapped_column(String(16), nullable=False) # 场馆类型：展览馆 / 会议室 / 休息区 / 其他
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False) # 场馆面积：平方米
    floors: Mapped[int] = mapped_column(Integer, nullable=False) # 楼层数：1-3
    height_m: Mapped[float] = mapped_column(Float, nullable=False) # 场馆高度：米
    capacity: Mapped[int] = mapped_column(Integer, nullable=False) # 场馆容量：人数
    x: Mapped[float] = mapped_column(Float, nullable=False) # 场馆X坐标：3d模型坐标
    y: Mapped[float] = mapped_column(Float, nullable=False) # 场馆Y坐标：3d模型坐标
    z: Mapped[float] = mapped_column(Float, nullable=False) # 场馆Z坐标：3d模型坐标
    intro: Mapped[str] = mapped_column(Text, nullable=False) # 场馆介绍：文本

# halls.name
#    └── devices.hall_name     这个设备在哪个馆

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # 自增主键：设备ID
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False) # 设备编码
    name: Mapped[str] = mapped_column(String(64), nullable=False) # 设备名称
    category: Mapped[str] = mapped_column(String(32), nullable=False) # 设备分类
    category_name: Mapped[str] = mapped_column(String(32), nullable=False) # 设备分类名称
    leaf_type: Mapped[str] = mapped_column(String(32), nullable=False) # 设备类型：leaf / group
    group_name: Mapped[str] = mapped_column(String(32), nullable=False) # 设备组名称
    hall_name: Mapped[str] = mapped_column(
        String(32), ForeignKey("halls.name"), nullable=False, index=True
    ) # 外键 → halls.name设备所在的馆
    status: Mapped[str] = mapped_column(String(16), nullable=False) # 设备状态：在线 / 离线 / 故障
    floor: Mapped[str] = mapped_column(String(8), nullable=False) # 设备楼层：1-3

# halls.name
#    └── exhibitions.hall_name     这场展会在哪个馆
#            └── exhibition_events.exhibition_id   这条日程属于哪场展会

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # 自增主键：展会ID
    name: Mapped[str] = mapped_column(String(128), nullable=False) # 展会名称
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True) # 展会年份
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True) # 展会月份
    hall_name: Mapped[str] = mapped_column(
        String(32), ForeignKey("halls.name"), nullable=False, index=True
    ) # 外键 → halls.name展会所在的馆
    start_date: Mapped[str] = mapped_column(String(16), nullable=False) # 展会开始日期
    end_date: Mapped[str] = mapped_column(String(16), nullable=False) # 展会结束日期
    visitors: Mapped[int] = mapped_column(Integer, nullable=False) # 展会参观人数
    status: Mapped[str] = mapped_column(String(16), nullable=False) # 展会状态：进行中 / 已结束 / 未开始

class ExhibitionEvent(Base):
    __tablename__ = "exhibition_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # 自增主键：日程ID
    exhibition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exhibitions.id"), nullable=False, index=True
    ) # 外键 → exhibitions.id展会ID
    event_type: Mapped[str] = mapped_column(String(32), nullable=False) # 日程类型：讲座 / 论坛 / 展览 / 其他
    title: Mapped[str] = mapped_column(String(128), nullable=False) # 日程标题
    location: Mapped[str] = mapped_column(String(64), nullable=False) # 日程地点
    room: Mapped[str] = mapped_column(String(32), nullable=False) # 日程房间
    start_time: Mapped[str] = mapped_column(String(32), nullable=False) # 日程开始时间
    hall_name: Mapped[str] = mapped_column(
        String(32), ForeignKey("halls.name"), nullable=False, index=True
    ) # 外键 → halls.name日程所在的馆

class Alarm(Base):
    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # 自增主键：告警ID
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id"), nullable=False, index=True
    ) # 外键 → devices.id，每条告警必须有设备
    hall_name: Mapped[str] = mapped_column(
        String(32), ForeignKey("halls.name"), nullable=True, index=True
    ) # 外键 → halls.name，馆外可为 NULL
    scope: Mapped[str] = mapped_column(String(8), nullable=False)  # 馆内 / 馆外
    alarm_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # 告警类型
    alarm_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # 一般 / 重要 / 严重
    alarm_time: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # 告警时间
    alarm_content: Mapped[str] = mapped_column(Text, nullable=False) # 告警内容
    alarm_status: Mapped[str] = mapped_column(String(16), nullable=False) # 未处理 / 处理中 / 已处理


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # 自增主键：工单ID
    device_id:Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id"), nullable = True, index = True
    )
    hall_name:Mapped[str] = mapped_column(
        String(32), ForeignKey("halls.name"), nullable = True, index = True
    )
    order_type:Mapped[str] = mapped_column(String(32), nullable = False, index = True) # 工单类型：维修 / 保养 / 其他
    source:Mapped[str] = mapped_column(String(16), nullable = False, index = True) # 工单来源：系统自动生成 / 人工创建
    level:Mapped[str] = mapped_column(String(16), nullable = False) # 一般 / 重要 / 严重
    title:Mapped[str] = mapped_column(String(128), nullable = False) # 工单标题
    status:Mapped[str] = mapped_column(String(16), nullable = False, index = True) # 未处理 / 处理中 / 已处理
    overdue:Mapped[int] = mapped_column(Boolean, nullable = False) # 超时时间：小时
    created_at:Mapped[str] = mapped_column(String(32), nullable = False, index = True) # 创建时间

class EnergyReading(Base):
    __tablename__ = "energy_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(8), nullable=False, index=True)  # 电 / 水
    period: Mapped[str] = mapped_column(String(8), nullable=False, index=True)  # 日 / 月
    period_key: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # 2026-09 或 2026-09-22
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)  # kWh / m³

class ParkingStat(Base):
    __tablename__ = "parking_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_spaces: Mapped[int] = mapped_column(Integer, nullable=False)
    used_spaces: Mapped[int] = mapped_column(Integer, nullable=False)
    social_vehicles: Mapped[int] = mapped_column(Integer, nullable=False)
    logistics_vehicles: Mapped[int] = mapped_column(Integer, nullable=False)
    work_vehicles: Mapped[int] = mapped_column(Integer, nullable=False)

class CrowdStat(Base):
    __tablename__ = "crowd_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hall_name: Mapped[str] = mapped_column(String(32), ForeignKey("halls.name"), nullable=False, index=True)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False)

class HeatmapPoint(Base):
    __tablename__ = "heatmap_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hall_name: Mapped[str] = mapped_column(String(32), ForeignKey("halls.name"), nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

class EmergencyRecord(Base):
    __tablename__ = "emergency_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    period: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    period_key: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    