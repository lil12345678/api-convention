"""终端里和大模型说几句话。查数字时模型只能调用数据库工具。Key 从 .env 读取。"""
#这个文件用来查看DeepSeek的工具是否可用，
# 为什么先在终端测？因为终端没有前端、没有 FastAPI 这些干扰，
# 通了就是 DeepSeek 这边没问题，断了就是 key/网络问题——好排查
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.ai_tools import TOOLS, run_tool, tool_result_message
from app.config import settings
from app.database import SessionLocal

MODEL = "deepseek-chat"
SYSTEM = (
    "你是会展大屏助手。用简短中文回答。"
    "问到告警、能耗、设备状态、场馆资料时，必须先调用工具，再根据工具返回的数字回答。"
    "工具没有查到就说没有，禁止编造数量。"
    "用户要求切换页面、场馆、楼层、热力图或设备标签时，调用对应的画面工具。"
    "画面工具只负责校验，不会真的移动 3D。根据返回的 message 告诉用户指令已记下。"
    "天气、昼夜、漫游没有工具，直接说暂不支持。"
)


def complete(messages):
    if not settings.DEEPSEEK_API_KEY:
        raise SystemExit("未配置 DEEPSEEK_API_KEY，请写在 .env 里")
    url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={"model": MODEL, "messages": messages, "tools": TOOLS},
            timeout=60,
        )
        body = response.json()
    except httpx.HTTPError as error:
        raise SystemExit(f"请求失败：{error}") from error
    if response.status_code != 200:
        message = body.get("error", body) if isinstance(body, dict) else body
        raise SystemExit(f"接口返回 {response.status_code}：{message}")
    return body["choices"][0]["message"]


def ask(messages):
    db = SessionLocal()
    try:
        for _ in range(4):
            message = complete(messages)
            calls = message.get("tool_calls") or []
            if not calls:
                return message.get("content") or ""
            messages.append(message)
            for call in calls:
                raw = call["function"].get("arguments") or "{}"
                arguments = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(arguments, dict):
                    arguments = {}
                print(f"[工具] {call['function']['name']} {json.dumps(arguments, ensure_ascii=False)}")
                result = run_tool(db, call["function"]["name"], arguments)
                messages.append(tool_result_message(call, result))
        return "查询次数过多，请换个问法"
    finally:
        db.close()


def main():
    messages = [{"role": "system", "content": SYSTEM}]
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:]).strip()
        messages.append({"role": "user", "content": text})
        print(ask(messages))
        return

    print("输入内容后回车，空行退出。")
    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            break
        messages.append({"role": "user", "content": text})
        reply = ask(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"助手：{reply}")


if __name__ == "__main__":
    main()
