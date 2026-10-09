"""统一 API 信封：{code, msg, data}

成功：HTTP 200，code=0，业务数据在 data。
失败：仍用真实 HTTP 状态码（401/404/422…），body 同样是信封，code 与状态码一致。
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def ok(data: Any = None, msg: str = "ok") -> dict[str, Any]:
    return {"code": 0, "msg": msg, "data": data}


def fail_body(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def _detail_to_msg(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                loc = ".".join(str(x) for x in item.get("loc", []) if x != "body")
                parts.append(f"{loc}: {item.get('msg', '')}" if loc else str(item.get("msg", item)))
            else:
                parts.append(str(item))
        return "; ".join(parts) if parts else "请求参数错误"
    return str(detail)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail_body(exc.status_code, _detail_to_msg(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(_request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail_body(exc.status_code, _detail_to_msg(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=fail_body(422, _detail_to_msg(exc.errors()), data=exc.errors()),
        )
