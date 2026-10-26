"""非流式对话。系统提示词固定，模型只能使用 app.ai_tools.TOOLS。"""
#这个文件用来和DeepSeek对话，并使用工具

import json
import httpx
from app.ai_tools import TOOLS, run_tool, tool_result_message
from app.config import settings
MODEL = "deepseek-chat"
MAX_ROUNDS = 4
SYSTEM = (
    "你是会展大屏助手。只用简短中文回答。"
    "本次请求里的工具就是白名单。只能调用这些工具。"
    "白名单以外的操作一律回复暂不支持，不要假装已经执行。"
    "禁止天气、昼夜、漫游，也禁止改数据、开关真实设备、导出。"
    "数字、时间、名称、面积、容量必须来自本轮工具返回，禁止编造，禁止用常识补全。"
    "没有调用工具，就不能报任何数字，也不能说画面已经切换。"
    "工具返回里有 error 时，照 error 的内容说明失败，不要改成成功。"
    "工具没有查到就说没有。total 是总数，items 最多 10 条样例，不要把样例条数当成总数。"
    "问今天或昨天的告警时，query_alarms 必须传 date。只按返回的 date 和 total 回答。"
    "用户要求切换页面、场馆、楼层、热力图、设备分类或设备标签时，调用对应的画面工具。"
    "画面工具只做校验。根据工具返回的 message 说明指令已记下，不要说画面已经变化。"
    "一句话里有多件事时，相关工具都要调用，完成后再回答。"
    "去某馆并查告警时，调用 selectBuilding，同时调用 query_alarms，hall_name 传该馆；说了今天或昨天还要传 date。"
)

class ChatError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message

def complete(messages):
    if not settings.DEEPSEEK_API_KEY:
        raise ChatError(503, "未配置 DeepSeek API Key")
    url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
            },
            timeout=60,
        )
        body = response.json()
    except httpx.HTTPError as error:
        raise ChatError(502, f"模型接口失败：{error}") from error
    if response.status_code != 200:
        message = body.get("error", body) if isinstance(body, dict) else body
        raise ChatError(502, f"模型接口返回 {response.status_code}：{message}")
    return body["choices"][0]["message"]

#非流式对话。系统提示词固定，模型只能使用 app.ai_tools.TOOLS。
def chat_turn(db, history):
    """history 只有 user / assistant。返回 reply、画面 commands、本次工具调用。"""
    messages = [{"role": "system", "content": SYSTEM}] 
    for item in history:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            raise ChatError(422, "消息只能是 user 或 assistant，且内容不能为空")
        messages.append({"role": role, "content": content})
    if messages[-1]["role"] != "user":
        raise ChatError(422, "最后一条必须是用户消息")

    commands = []
    calls_made = []
    for i in range(MAX_ROUNDS):
        message = complete(messages)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return {
                "reply": message.get("content") or "",
                "commands": commands,
                "calls_made": calls_made,
            }
        messages.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            raw = call["function"].get("arguments") or "{}"
            arguments = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(arguments, dict):
                arguments = {}
            calls_made.append({
                "name": name,
                "arguments": arguments,
            })
            result = run_tool(db, name, arguments)
            if result.get('kind') == 'screen' and result.get('ok'):
                commands.append(
                    {
                        "action":result["action"],
                        "params":result["params"],
                        "kind":result["kind"],
                        "message":result["message"],
                    }
                )
            messages.append(tool_result_message(call, result))
    return{
        "reply": "查询次数过多，请重新提问。",
        "commands": commands,
        "tool_calls": calls_made,
    }

#流式对话
def _sse(name, payload):
    return f"event:{name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

def prepare_messages(history):
    messages = [{"role": "system", "content": SYSTEM}] 
    for item in history:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            raise ChatError(422, "消息只能是 user 或 assistant，且内容不能为空")
        messages.append({"role": role, "content": content})
    if messages[-1]["role"] != "user":
        raise ChatError(422, "最后一条必须是用户消息")
    return messages

def complete_stream(messages):
    """逐行读 DeepSeek 的 SSE。成功时 yield 每个 JSON 块。"""
    if not settings.DEEPSEEK_API_KEY:
        raise ChatError(503, "未配置 DeepSeek API Key")
    url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        with httpx.stream(
            "POST",
            url,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "stream": True,
            },
            timeout=60,
        ) as response:
            if response.status_code != 200:
                raw = response.read().decode("utf-8",errors="replace")
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    body = raw
                message = body.get("error", body) if isinstance(body, dict) else body
                raise ChatError(502, f"模型接口返回 {response.status_code}：{message}")
            for line in response.iter_lines():
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                yield json.loads(data)
    except ChatError as error:
        raise ChatError(502, f"模型接口失败：{error}") from error

def _take_tool_piece(bucket, piece):
    index = piece.get("index", 0)
    current = bucket.setdefault(index, {"id": "", "name": "", "arguments": ""})
    if piece.get("id"):
        current["id"] = piece["id"]
    function = piece.get("function") or {}
    if function.get("name"):
        current["name"] += function["name"]
    if function.get("arguments"):
        current["arguments"] += function["arguments"]


def _chat_events(db, history, reply_parts = None):
    if reply_parts is None:
        reply_parts = []
    messages = prepare_messages(history)
    commands = []
    for _ in range(MAX_ROUNDS):
        content_parts = []
        bucket = {}
        for chunk in complete_stream(messages):
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            if delta.get("content"):
                content_parts.append(delta["content"])
                reply_parts.append(delta["content"])
                yield _sse("delta", {"text": delta["content"]})
            for piece in delta.get("tool_calls") or []:
                _take_tool_piece(bucket, piece)
        if not bucket:
            yield _sse("commands", {"commands": commands})
            yield _sse("done", {"reply": "".join(reply_parts)})
            return
        tool_calls = [
           {
                "id": bucket[index]["id"],
                "type": "function",
                "function": {
                "name": bucket[index]["name"],
                "arguments": bucket[index]["arguments"] or "{}",
                },
           } 
           for index in sorted(bucket)
        ]
        
        messages.append({
            "role": "assistant",
            "content": "".join(content_parts) or None,
            "tool_calls": tool_calls,
        })
        for call in tool_calls:
            name = call["function"]["name"]
            raw = call["function"].get("arguments")
            arguments = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(arguments, dict):
                arguments = {}
            yield _sse("tool", {
                "name": name,
                "arguments": arguments,
            })
            result = run_tool(db, name, arguments)
            if result.get('kind') == 'screen' and result.get('ok'):
                commands.append(
                    {
                        "action":result["action"],
                        "params":result["params"],
                        "kind":result["kind"],
                        "message":result["message"],
                    }
                )
            messages.append(tool_result_message(call, result))
    yield _sse("commands", {"commands": commands})
    yield _sse("done",{"reply":"查询次数过多，请重新提问"})

# def iter_chat_events(history):
#     """给路由用的生成器。数据库连接放在流里面开，避免流还没写完连接就被关掉。"""
    
#     from app.database import SessionLocal

#     db = SessionLocal()
#     try:
#         yield from _chat_events(db, history)
#     except ChatError as error:
#         yield _sse("error", {"message": error.message})
#     finally:
#         db.close()
def iter_chat_events(history, user_id=None):
    """给路由用的生成器。本轮问题一开始就落库，回答在流结束时落库。"""
    from app.database import SessionLocal
    from app.chat_store import save_assistant_message, save_user_message

    db = SessionLocal()
    reply_parts = []
    try:
        if user_id is not None and history:
            save_user_message(db, user_id, history[-1].get("content"))
        for piece in _chat_events(db, history, reply_parts):
            yield piece
        if user_id is not None:
            save_assistant_message(db, user_id, "".join(reply_parts))
    except ChatError as error:
        yield _sse("error", {"message": error.message})
    finally:
        db.close()