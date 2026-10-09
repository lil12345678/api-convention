import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import  User, Hall, Device, Exhibition, ExhibitionEvent, Alarm, WorkOrder, EnergyReading, ParkingStat, CrowdStat, HeatmapPoint, EmergencyRecord
from app.security import hash_password

def seed_users_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(User).limit(1))
        if exists is not None:
            return
        db.add(User(username="admin", hashed_password=hash_password("admin123"), is_active=True))
        db.commit()
    finally:
        db.close()

HALLS = [
    {
        "name": "1号馆",
        "sort_order": 1,
        "hall_type": "展馆",
        "area_sqm": 12000,
        "floors": 2,
        "height_m": 16,
        "capacity": 4000,
        "x": 80,
        "y": 0,
        "z": 40,
        "intro": "1号馆为标准单层大跨度展厅，适合机械装备、工业母机等重型展品进场。",
    },
    {
        "name": "2号馆",
        "sort_order": 2,
        "hall_type": "展馆",
        "area_sqm": 12000,
        "floors": 2,
        "height_m": 16,
        "capacity": 4000,
        "x": 160,
        "y": 0,
        "z": 40,
        "intro": "2号馆紧邻1号馆，常承接同一主题联展，便于跨馆人流组织。",
    },
    {
        "name": "3号馆",
        "sort_order": 3,
        "hall_type": "展馆",
        "area_sqm": 11000,
        "floors": 2,
        "height_m": 15,
        "capacity": 3600,
        "x": 240,
        "y": 0,
        "z": 40,
        "intro": "3号馆适合电子信息、智能制造类展览，配套会议和洽谈区较完整。",
    },
    {
        "name": "4号馆",
        "sort_order": 4,
        "hall_type": "展馆",
        "area_sqm": 11000,
        "floors": 2,
        "height_m": 15,
        "capacity": 3600,
        "x": 320,
        "y": 0,
        "z": 40,
        "intro": "4号馆可独立办展，也可与3号馆打通，用于中型专业展。",
    },
    {
        "name": "5号馆",
        "sort_order": 5,
        "hall_type": "展馆",
        "area_sqm": 10000,
        "floors": 2,
        "height_m": 14,
        "capacity": 3200,
        "x": 400,
        "y": 0,
        "z": 40,
        "intro": "5号馆靠近主登录厅一侧，适合品牌发布和开幕式配套展览。",
    },
    {
        "name": "6号馆",
        "sort_order": 6,
        "hall_type": "展馆",
        "area_sqm": 10000,
        "floors": 2,
        "height_m": 14,
        "capacity": 3200,
        "x": 80,
        "y": 0,
        "z": -40,
        "intro": "6号馆位于南侧展区，货运通道独立，适合需要频繁换展的项目。",
    },
    {
        "name": "7号馆",
        "sort_order": 7,
        "hall_type": "展馆",
        "area_sqm": 10000,
        "floors": 2,
        "height_m": 14,
        "capacity": 3200,
        "x": 160,
        "y": 0,
        "z": -40,
        "intro": "7号馆为综合展馆，一层布展、二层可安排同期会议。",
    },
    {
        "name": "8号馆",
        "sort_order": 8,
        "hall_type": "展馆",
        "area_sqm": 10000,
        "floors": 2,
        "height_m": 14,
        "capacity": 3200,
        "x": 240,
        "y": 0,
        "z": -40,
        "intro": "8号馆适合消费品、文化旅游类轻型展览，参观动线较短。",
    },
    {
        "name": "9号馆",
        "sort_order": 9,
        "hall_type": "展馆",
        "area_sqm": 9000,
        "floors": 2,
        "height_m": 13,
        "capacity": 2800,
        "x": 320,
        "y": 0,
        "z": -40,
        "intro": "9号馆面积适中，常作为专题馆或国家/地区馆使用。",
    },
    {
        "name": "10号馆",
        "sort_order": 10,
        "hall_type": "展馆",
        "area_sqm": 9000,
        "floors": 2,
        "height_m": 13,
        "capacity": 2800,
        "x": 400,
        "y": 0,
        "z": -40,
        "intro": "10号馆与东登录厅衔接较好，适合需要独立安检分流的展览。",
    },
    {
        "name": "11号馆",
        "sort_order": 11,
        "hall_type": "展馆",
        "area_sqm": 8500,
        "floors": 2,
        "height_m": 13,
        "capacity": 2600,
        "x": 80,
        "y": 0,
        "z": -120,
        "intro": "11号馆偏园区外侧，适合汽车、工程机械等需要室外延伸的展览。",
    },
    {
        "name": "12号馆",
        "sort_order": 12,
        "hall_type": "展馆",
        "area_sqm": 8500,
        "floors": 2,
        "height_m": 13,
        "capacity": 2600,
        "x": 160,
        "y": 0,
        "z": -120,
        "intro": "12号馆可承接论坛配套静态展，二层会议室数量较多。",
    },
    {
        "name": "13号馆",
        "sort_order": 13,
        "hall_type": "展馆",
        "area_sqm": 8000,
        "floors": 2,
        "height_m": 12,
        "capacity": 2400,
        "x": 240,
        "y": 0,
        "z": -120,
        "intro": "13号馆体量较小，适合专业买家对接、采样订货类活动。",
    },
    {
        "name": "14号馆",
        "sort_order": 14,
        "hall_type": "展馆",
        "area_sqm": 8000,
        "floors": 2,
        "height_m": 12,
        "capacity": 2400,
        "x": 320,
        "y": 0,
        "z": -120,
        "intro": "14号馆适合教育、医疗、科技成果转化等主题展览。",
    },
    {
        "name": "15号馆",
        "sort_order": 15,
        "hall_type": "展馆",
        "area_sqm": 7500,
        "floors": 2,
        "height_m": 12,
        "capacity": 2200,
        "x": 400,
        "y": 0,
        "z": -120,
        "intro": "15号馆靠近次登录厅，便于团队观众集中入场和疏散。",
    },
    {
        "name": "16号馆",
        "sort_order": 16,
        "hall_type": "展馆",
        "area_sqm": 7500,
        "floors": 2,
        "height_m": 12,
        "capacity": 2200,
        "x": 480,
        "y": 0,
        "z": -120,
        "intro": "16号馆为园区东侧尽端展厅，适合需要独立品牌形象的专馆。",
    },
    {
        "name": "主登录厅",
        "sort_order": 17,
        "hall_type": "登录厅",
        "area_sqm": 15000,
        "floors": 3,
        "height_m": 22,
        "capacity": 5000,
        "x": 0,
        "y": 0,
        "z": 0,
        "intro": "主登录厅是园区主入口，承担注册、安检、问询和开幕式主会场功能。",
    },
    {
        "name": "次登录厅",
        "sort_order": 18,
        "hall_type": "登录厅",
        "area_sqm": 8000,
        "floors": 2,
        "height_m": 18,
        "capacity": 2500,
        "x": -40,
        "y": 0,
        "z": -80,
        "intro": "次登录厅用于团队和工作人员分流，减轻主登录厅高峰压力。",
    },
    {
        "name": "东登录厅",
        "sort_order": 19,
        "hall_type": "登录厅",
        "area_sqm": 6000,
        "floors": 2,
        "height_m": 16,
        "capacity": 1800,
        "x": 520,
        "y": 0,
        "z": -40,
        "intro": "东登录厅服务东侧展馆集群，便于东区观众就近入场。",
    },
]


def seed_halls_if_empty():
    db = SessionLocal()
    try:
        # 已经有数据就不要再插，避免重复报错
        exists = db.scalar(select(Hall).limit(1))
        if exists is not None:
            return
        for item in HALLS:
            db.add(Hall(**item))
        db.commit()
    finally:
        db.close()

DEVICE_TYPES = [
    {"leaf_type": "空调用电", "category": "monitor", "category_name": "监控设备", "group_name": "电气设备"},
    {"leaf_type": "集中空调", "category": "monitor", "category_name": "监控设备", "group_name": "暖通设备"},
    {"leaf_type": "辐射空调", "category": "monitor", "category_name": "监控设备", "group_name": "暖通设备"},
    {"leaf_type": "应急照明", "category": "monitor", "category_name": "监控设备", "group_name": "电气设备"},
    {"leaf_type": "照明插座", "category": "monitor", "category_name": "监控设备", "group_name": "电气设备"},
    {"leaf_type": "景观照明", "category": "monitor", "category_name": "监控设备", "group_name": "电气设备"},
    {"leaf_type": "入侵探测器", "category": "security", "category_name": "安防设备", "group_name": "弱电设备"},
    {"leaf_type": "停车场匝道", "category": "security", "category_name": "安防设备", "group_name": "弱电设备"},
    {"leaf_type": "门禁", "category": "security", "category_name": "安防设备", "group_name": "弱电设备"},
    {"leaf_type": "照明", "category": "elevator", "category_name": "楼宇自控", "group_name": "电气设备"},
    {"leaf_type": "冷热源", "category": "elevator", "category_name": "楼宇自控", "group_name": "暖通设备"},
    {"leaf_type": "空调", "category": "elevator", "category_name": "楼宇自控", "group_name": "暖通设备"},
    {"leaf_type": "电表", "category": "energy", "category_name": "能效设备", "group_name": "电气设备"},
    {"leaf_type": "水表", "category": "energy", "category_name": "能效设备", "group_name": "给排水设备"},
]

HALL_NAMES = [item["name"] for item in HALLS]
STATUSES = ["在线", "在线", "在线", "在线", "离线", "故障"]


def seed_devices_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(Device).limit(1))
        if exists is not None:
            return
        index = 1
        for kind in DEVICE_TYPES:
            for n in range(1, 7):
                hall_name = HALL_NAMES[(index - 1) % len(HALL_NAMES)]
                db.add(
                    Device(
                        code=f"{kind['leaf_type']}-{n:02d}",
                        name=f"{kind['leaf_type']}-{n:02d}",
                        category=kind["category"],
                        category_name=kind["category_name"],
                        leaf_type=kind["leaf_type"],
                        group_name=kind["group_name"],
                        hall_name=hall_name,
                        status=STATUSES[(index - 1) % len(STATUSES)],
                        floor="1F" if n % 2 else "2F",
                    )
                )
                index += 1
        db.commit()
    finally:
        db.close()

EXHIBITIONS = [
    {
        "name": "中国（中原）工业技术装备博览会",
        "year": 2026,
        "month": 9,
        "hall_name": "1号馆",
        "start_date": "2026-09-06",
        "end_date": "2026-09-08",
        "visitors": 18600,
        "status": "已结束",
        "events": [
            {"event_type": "主题交流", "title": "智能制造开幕交流", "location": "博览会展会", "room": "会议室A", "start_time": "2026-09-06 09:00", "hall_name": "1号馆"},
            {"event_type": "专题研讨", "title": "工业母机技术研讨", "location": "博览会展会", "room": "会议室B", "start_time": "2026-09-06 14:00", "hall_name": "1号馆"},
        ],
    },
    {
        "name": "中原汽车暨零部件展览会",
        "year": 2026,
        "month": 8,
        "hall_name": "11号馆",
        "start_date": "2026-08-20",
        "end_date": "2026-08-23",
        "visitors": 15200,
        "status": "已结束",
        "events": [
            {"event_type": "主题交流", "title": "新能源车供应链交流", "location": "汽车展区", "room": "会议室", "start_time": "2026-08-20 09:30", "hall_name": "11号馆"},
        ],
    },
    {
        "name": "数字经济与人工智能展览会",
        "year": 2026,
        "month": 9,
        "hall_name": "3号馆",
        "start_date": "2026-09-18",
        "end_date": "2026-09-21",
        "visitors": 9800,
        "status": "进行中",
        "events": [
            {"event_type": "主题交流", "title": "大模型产业应用交流", "location": "数字展区", "room": "会议室A", "start_time": "2026-09-18 10:00", "hall_name": "3号馆"},
            {"event_type": "专题研讨", "title": "算力基础设施研讨", "location": "数字展区", "room": "会议室C", "start_time": "2026-09-19 14:30", "hall_name": "3号馆"},
        ],
    },
    {
        "name": "中原医疗健康产业博览会",
        "year": 2026,
        "month": 10,
        "hall_name": "14号馆",
        "start_date": "2026-10-12",
        "end_date": "2026-10-15",
        "visitors": 0,
        "status": "未开始",
        "events": [
            {"event_type": "专题研讨", "title": "医疗器械注册研讨", "location": "医疗展区", "room": "会议室", "start_time": "2026-10-12 09:00", "hall_name": "14号馆"},
        ],
    },
    {
        "name": "中国（中原）工业博览会展示会",
        "year": 2025,
        "month": 12,
        "hall_name": "2号馆",
        "start_date": "2025-12-06",
        "end_date": "2025-12-08",
        "visitors": 21000,
        "status": "已结束",
        "events": [
            {"event_type": "主题交流", "title": "工业博览开幕交流", "location": "博览会展会", "room": "会议室", "start_time": "2025-12-06 09:00", "hall_name": "2号馆"},
            {"event_type": "专题研讨", "title": "先进材料专题研讨", "location": "博览会展会", "room": "会议室", "start_time": "2025-12-07 09:00", "hall_name": "2号馆"},
        ],
    },
    {
        "name": "消费品进出口交易会",
        "year": 2026,
        "month": 7,
        "hall_name": "8号馆",
        "start_date": "2026-07-08",
        "end_date": "2026-07-11",
        "visitors": 13400,
        "status": "已结束",
        "events": [
            {"event_type": "主题交流", "title": "品牌出海交流", "location": "消费展区", "room": "会议室A", "start_time": "2026-07-08 10:00", "hall_name": "8号馆"},
        ],
    },
]


def seed_exhibitions_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(Exhibition).limit(1))
        if exists is not None:
            return
        for item in EXHIBITIONS:
            exhibition = Exhibition(
                name=item["name"],
                year=item["year"],
                month=item["month"],
                hall_name=item["hall_name"],
                start_date=item["start_date"],
                end_date=item["end_date"],
                visitors=item["visitors"],
                status=item["status"],
            )
            db.add(exhibition)
            db.flush()
            for event in item["events"]:
                db.add(
                    ExhibitionEvent(
                        exhibition_id=exhibition.id,
                        event_type=event["event_type"],
                        title=event["title"],
                        location=event["location"],
                        room=event["room"],
                        start_time=event["start_time"],
                        hall_name=event["hall_name"],
                    )
                )
        db.commit()
    finally:
        db.close()

def seed_alarms_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(Alarm).limit(1))
        if exists is not None:
            return

        devices = db.scalars(select(Device).order_by(Device.id)).all()
        if not devices:
            return

        types = ["AI视频告警", "入侵告警", "消防告警", "设备告警"]
        levels = ["一般", "重要", "严重"]
        statuses = ["未处理", "处理中", "已处理"]
        now = datetime.now()
        for i in range(40):
            device = devices[i % len(devices)]
            is_outdoor = i % 5 == 0
            occurred = now - timedelta(days=i% 30, hours=i% 12)
            alarm_type = types[i % len(types)]
            db.add(
                Alarm(
                    device_id=device.id,
                    hall_name=None if is_outdoor else device.hall_name,
                    scope="馆外" if is_outdoor else "馆内",
                    alarm_type=alarm_type,
                    alarm_level = levels[i % len(levels)],
                    alarm_time = occurred.strftime("%Y-%m-%d %H:%M"),
                    alarm_content = f"{device.name}发生{alarm_type}",
                    alarm_status = statuses[i % len(statuses)],
                )
            )
        db.commit()
    finally:
        db.close()

def seed_work_orders_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(WorkOrder).limit(1))
        if exists is not None:
            return

        devices = db.scalars(select(Device).order_by(Device.id)).all()
        if not devices:
            return
        
        order_types = ["维修工单", "报事工单", "投诉工单"]
        sources = ["设备", "能源", "综合"]
        levels = ["一般", "重要", "紧急"]
        statuses = ["待处理", "处理中", "已处理"]
        now = datetime.now()

        for i in range(35):
            device = devices[i % len(devices)]
            has_device = i % 4 == 0
            order_type = order_types[i % len(order_types)]
            status = statuses[i % len(statuses)]
            overdue = status != "已处理" and i % 6 == 0
            db.add(
                WorkOrder(
                    device_id=device.id if has_device else None,
                    hall_name=device.hall_name if has_device else None,
                    order_type=order_type,
                    source=sources[i % len(sources)],
                    level=levels[i % len(levels)],
                    title=f"{order_type} - {device.name if has_device else '馆外'}",
                    status=status,
                    overdue=overdue,
                    created_at=(now - timedelta(days=i % 30, hours=i % 10)).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                )
            )
        db.commit()
    finally:
        db.close()

def seed_energy_readings_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(EnergyReading).limit(1))
        if exists is not None:
            return

        now = datetime.now()
        kids = [
            ("电", "kWh", 80000, 2200),
            ("水", "m³", 12000, 1000),
        ]
        for kind, unit, month_base, day_base in kids:
            year = now.year
            month = now.month
            for i in range(12):
                db.add(
                    EnergyReading(
                        kind=kind,
                        period="月",
                        period_key=f"{year:04d}-{month:02d}",
                        value=month_base + i * 2500 + (i % 3) * 800,
                        unit=unit,
                    )
                )
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            for i in range(9):
                day = now - timedelta(days=i)
                db.add(
                    EnergyReading(
                        kind=kind,
                        period="日",
                        period_key=day.strftime("%Y-%m-%d"),
                        value=day_base + i * 70 + (i % 2) * 20,
                        unit=unit,
                    )
                )
        db.commit()
    finally:
        db.close()

def seed_parking_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(ParkingStat).limit(1))
        if exists is not None:
            return
        db.add(ParkingStat(
            total_spaces=1000,
            used_spaces=500,
            social_vehicles=300,
            logistics_vehicles=100,
            work_vehicles=100,
        ))
        db.commit()
    finally:
        db.close()

def seed_crowd_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(CrowdStat).limit(1))
        if exists is not None:
            return
        halls = db.scalars(select(Hall).order_by(Hall.sort_order)).all()
        for hall in halls:
            db.add(CrowdStat(
            hall_name=hall.name,
            headcount=180 + hall.sort_order * 40,
            ))
        db.commit()
    finally:
        db.close()

def seed_heatmap_if_empty():
    # 与前端热力图一致：画布 300×300，每个馆 100 个点，x、y、value 随机。
    db = SessionLocal()
    try:
        exists = db.scalar(select(HeatmapPoint).limit(1))
        if exists is not None:
            return
        halls = db.scalars(select(Hall).order_by(Hall.sort_order)).all()
        width = 300
        height = 300
        for hall in halls:
            for _ in range(100):
                db.add(
                    HeatmapPoint(
                        hall_name=hall.name,
                        x=random.randrange(width),
                        y=random.randrange(height),
                        value=random.randrange(100),
                    )
                )
        db.commit()
    finally:
        db.close()

def seed_emergency_if_empty():
    db = SessionLocal()
    try:
        exists = db.scalar(select(EmergencyRecord).limit(1))
        if exists is not None:
            return
        
        overviews = [
            ('应急预案', 12),
            ('应急队伍', 10),
            ('应急仓库', 8),
            ('应急物资', 6),
            ('应急车辆', 4)
        ]

        for name, value in overviews:
            db.add(
                EmergencyRecord(
                    record_type="概况",
                    name=name,
                    period="当前",
                    period_key="当前",
                    value=value,
                )
            )
        event_types = ["公共卫生", "自然灾害", "社会安全", "事故灾害", "其它"]
        now = datetime.now()
        for type_index, name in enumerate(event_types):
            year = now.year
            month = now.month
            for i in range(12):
                db.add(
                    EmergencyRecord(
                        record_type="事件",
                        name=name,
                        period="月",
                        period_key=f"{year:04d}-{month:02d}",
                        value=2 + i + type_index * 3,
                    )
                )
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
        db.commit()
    finally:
        db.close()