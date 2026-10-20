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
    "你只能使用本次请求提供的工具。没有对应工具的操作一律回复暂不支持，不要假装已经执行。"
    "禁止调用或编造天气、昼夜、漫游。"
    "问到告警、能耗、设备状态、场馆资料时，必须先调用工具，只根据工具返回的数字回答。"
    "工具没有查到就说没有，禁止编造数量。"
    "用户要求切换页面、场馆、楼层、热力图、设备分类或设备标签时，调用对应的画面工具。"
    "画面工具只做校验。根据工具返回的 message 说明指令已记下，不要说画面已经变化。"
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
                "tool_chioce": "auto",
            },
            timeout=60,
        )
        body = response.json()
    except httpx.HTTPError as error:
        raise ChatError(502, f"模型接口失败：{error}") from error
    if response.status_code != 200:
        message = body.get("error", boby) if isinstance(body, dict) else boby
        raise ChatError(502, f"模型接口返回 {response.status_code}：{message}")
    return body["choices"][0]["message"]


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