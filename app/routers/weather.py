import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.deps import get_current_user
from app.models import User
from app.response import ok

router = APIRouter(prefix="/api", tags=["weather"])

AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

@router.get("/weather")
def get_weather(_user: User = Depends(get_current_user)):
    # 后端代前端调高德天气接口：Key 只放在服务器上，浏览器看不到
    if not settings.AMAP_KEY:
        raise HTTPException(status_code=503, detail="未配置天气服务（AMAP_KEY）")
    try:
        resp = httpx.get(AMAP_WEATHER_URL, 
            params={
                "key": settings.AMAP_KEY,
                "city": settings.WEATHER_CITY,
                "extensions": "base",
            },
            timeout=10,
        )
        body = resp.json()
    except (httpx.HTTPStatusError,ValueError):
        raise HTTPException(status_code=502, detail="天气服务请求失败")
    if body.get("status") != "1" or not body.get("lives"):
        raise HTTPException(status_code=502, detail="天气服务返回数据异常")
    live = body["lives"][0]
    return ok({
            "city": live["city"],
            "weather": live["weather"],
            "temperature": live["temperature"],
            "humidity": live["humidity"],
            "wind": f"{live['winddirection']}风{live['windpower']}级",
            "report_time": live["reporttime"],
    })