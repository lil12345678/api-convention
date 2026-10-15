from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models import Exhibitor, ExhibitorService, User
from app.response import ok
router = APIRouter(prefix="/api", tags=["exhibitors"])

@router.get("/exhibitor-services")
def list_exhibitors_services(
    limit: int = Query(20, ge=1, le=100),
    db:Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # 输入：limit 条数，1~100，默认 20
    # 输出：最近的展商服务记录，带展商名和展位
    # 读表：exhibitor_services JOIN exhibitors
    rows = db.execute(
        select(ExhibitorService,Exhibitor)
        .join(Exhibitor, ExhibitorService.exhibitor_id == Exhibitor.id)
        .order_by(ExhibitorService.created_at.desc())
        .limit(limit)
    ).all()
    return ok(
        [
            {
                "id": service.id,
                "exhibitor_name": exhibitor.name,
                "booth": exhibitor.booth,
                "hall_name": exhibitor.hall_name,
                "service_type": service.service_type,
                "status": service.status,
                "created_at": service.created_at,

            }
            for service, exhibitor in rows
        ]
    )

@router.get("/exhibitors/province-stats")
def exhibitors_province_stats(
    db:Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # 输入：所有展商，按省份分组，统计每个省份的展商数量
    # 输出：省份 -> 展商数量
    # 读表：exhibitors
    # 输出：每个省份有多少展商，按数量从多到少，例如 [{"province": "河南", "count": 12}]
    # SQL 等价于：SELECT province, COUNT(id) FROM exhibitors GROUP BY province ORDER BY COUNT(id) DESC
    count = func.count(Exhibitor.id)
    rows = db.execute(
        select(Exhibitor.province, count)
        .group_by(Exhibitor.province).order_by(count.desc())
    ).all()
    return ok([{"province": province, "count": total} for province, total in rows])