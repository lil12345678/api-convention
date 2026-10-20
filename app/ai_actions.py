"""AI 指令白名单。

画面指令只校验：3D 场景在浏览器里，后端执行不了。
查询指令的名字也在这里，真正查库在 app/routers/scene.py。
天气、昼夜、漫游故意不收录，传过来就是“不支持的操作”。
"""
#这个文件用来把白名单翻译成 AI 能看懂的"指令说明书"
PAGES = {
    "comSituation": "综合态势",
    "secSituation": "安防态势",
    "device": "设备运行",
    "energy": "能源管理",
    "convention": "会展信息",
}
PAGE_ALIASES = {
    "综合态势": "comSituation",
    "首页": "comSituation",
    "安防": "secSituation",
    "安防态势": "secSituation",
    "设备": "device",
    "设备管理": "device",
    "设备运行": "device",
    "能源": "energy",
    "能耗": "energy",
    "能量管理": "energy",
    "能源管理": "energy",
    "会展": "convention",
    "会展信息": "convention",
}

BUILDINGS = [f"{i}号馆" for i in range(1, 17)] + ["主登录厅", "次登录厅", "东登录厅"]

FLOORS = {"1F": "1", "恢复": "2", "全部展开": "3"}
FLOOR_ALIASES = {"1": "1F", "1f": "1F", "一层": "1F", "收起": "恢复", "展开": "全部展开"}

CATEGORIES = {
    "监控设备": "监控设备",
    "monitor": "监控设备",
    "安防设备": "安防设备",
    "security": "安防设备",
    "楼宇自控": "楼宇自控",
    "elevator": "楼宇自控",
    "能效设备": "能效设备",
    "energy": "能效设备",
}
STATUSES = {"在线", "离线", "故障"}

# action -> (种类, 允许的参数名, 说明)
ACTIONS = {
    "navigate": ("screen", {"page"}, "切换大屏页面"),
    "overview": ("screen", set(), "回到总览视角"),
    "showVenueLabels": ("screen", set(), "显示所有场馆标签"),
    "selectBuilding": ("screen", {"building"}, "镜头定位到某个场馆"),
    "selectFloor": ("screen", {"floor"}, "场馆楼层展开或收起，需先选中场馆"),
    "toggleHeatmap": ("screen", {"visible"}, "显示或关闭人流热力图"),
    "openDeviceCategory": ("screen", {"category"}, "打开设备分类面板"),
    "showDevice": ("screen", {"device"}, "选中某类设备并显示 3D 标签"),
    "queryDevices": ("query", {"hall_name", "leaf_type", "status", "category"}, "统计设备状态"),
    "queryHall": ("query", {"name"}, "查看一个场馆的资料"),
}


class CommandError(ValueError):
    """参数或动作不在白名单里。用异常中断，调用方转成返回信息。"""


def action_catalog():
    return [
        {
            "action": name,
            "kind": kind,
            "params": sorted(params),
            "desc": desc,
        }
        for name, (kind, params, desc) in ACTIONS.items()
    ]


def _text(value, label):
    text = str(value if value is not None else "").strip()
    if not text:
        raise CommandError(f"缺少参数：{label}")
    return text


def _building(value):
    text = _text(value, "building")
    if text in BUILDINGS:
        return text
    number = text[:-2] if text.endswith("号馆") else text
    if number.isdigit() and 1 <= int(number) <= 16:
        return f"{int(number)}号馆"
    raise CommandError(f"没有这个场馆：{value}")


def _floor(value):
    text = _text(value, "floor")
    if text in FLOORS:
        return text
    name = FLOOR_ALIASES.get(text) or FLOOR_ALIASES.get(text.lower())
    if not name:
        raise CommandError(f"楼层操作不支持：{value}")
    return name


def _bool(value):
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True", "是"):
        return True
    if value in (0, "0", "false", "False", "否"):
        return False
    raise CommandError(f"visible 只能是 true 或 false：{value}")


def _normalize(action, params):
    if action == "navigate":
        page = _text(params.get("page"), "page")
        key = page if page in PAGES else PAGE_ALIASES.get(page)
        if not key:
            raise CommandError(f"没有这个页面：{page}")
        return {"page": key}
    if action == "selectBuilding":
        return {"building": _building(params.get("building"))}
    if action == "selectFloor":
        return {"floor": _floor(params.get("floor"))}
    if action == "toggleHeatmap":
        visible = True if "visible" not in params else _bool(params.get("visible"))
        return {"visible": visible}
    if action == "openDeviceCategory":
        name = _text(params.get("category"), "category")
        if name not in CATEGORIES:
            raise CommandError(f"没有这个设备分类：{name}")
        return {"category": CATEGORIES[name]}
    if action == "showDevice":
        return {"device": _text(params.get("device"), "device")}
    if action == "queryHall":
        return {"name": _building(params.get("name"))}
    if action == "queryDevices":
        result = {}
        if params.get("hall_name"):
            result["hall_name"] = _building(params.get("hall_name"))
        if params.get("leaf_type"):
            result["leaf_type"] = _text(params.get("leaf_type"), "leaf_type")
        if params.get("status"):
            status = _text(params.get("status"), "status")
            if status not in STATUSES:
                raise CommandError(f"设备状态不支持：{status}")
            result["status"] = status
        if params.get("category"):
            category = _text(params.get("category"), "category")
            if category not in CATEGORIES:
                raise CommandError(f"没有这个设备分类：{category}")
            result["category"] = CATEGORIES[category]
        return result
    return {}


def _message(action, params):
    if action == "navigate":
        return f"已校验：切换到{PAGES[params['page']]}"
    if action == "overview":
        return "已校验：回到总览视角"
    if action == "showVenueLabels":
        return "已校验：显示场馆标签"
    if action == "selectBuilding":
        return f"已校验：定位到{params['building']}"
    if action == "selectFloor":
        return f"已校验：楼层切换为{params['floor']}"
    if action == "toggleHeatmap":
        return "已校验：显示人流热力图" if params["visible"] else "已校验：关闭人流热力图"
    if action == "openDeviceCategory":
        return f"已校验：打开{params['category']}"
    if action == "showDevice":
        return f"已校验：显示{params['device']}"
    if action == "queryHall":
        return f"查询场馆：{params['name']}"
    return "查询设备状态"


def check_command(command):
    """检查一条指令。通过则返回 action、params、kind、message。"""
    if not isinstance(command, dict):
        raise CommandError('指令格式错误，应为 {"action": "...", "params": {...}}')
    action = command.get("action")
    params = command.get("params", {})
    if action not in ACTIONS:
        raise CommandError(f"不支持的操作：{action}")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise CommandError(f"{action} 的 params 必须是对象")
    _kind, allowed, _desc = ACTIONS[action]
    extra = set(params) - allowed
    if extra:
        names = "、".join(sorted(extra))
        raise CommandError(f"{action} 不接受参数：{names}")
    normalized = _normalize(action, params)
    kind = ACTIONS[action][0]
    return {
        "action": action,
        "params": normalized,
        "kind": kind,
        "message": _message(action, normalized),
    }