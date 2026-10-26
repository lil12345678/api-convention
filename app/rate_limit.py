import time
import threading

from fastapi import HTTPException

WINDOW_SECONDS = 60
MAX_CALLS = 10
_lock = threading.Lock()
_hits: dict[str, list[float]] = {}

def check_chat_rate(user_id: str) -> None:
    now = time.monotonic()
    with _lock:
        recent = [t for t in _hits.get(user_id, []) if t > now - WINDOW_SECONDS]
        if len(recent) >= MAX_CALLS:
            raise HTTPException(429, "发送太频繁，请稍后再试")
        recent.append(now)
        _hits[user_id] = recent