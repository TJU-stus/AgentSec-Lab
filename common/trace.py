# common/trace.py
# ============================================================
# AgentSec-Lab 运行记录（Trace）共享格式模块
#
# 用途：全项目运行记录的“统一记账格式”，只维护这一份。
#   - 成员2（Runner）：调用 make_event() 生成一条条事件记录；
#   - 成员3（平台）：可用 validate_event() 校验收到的记录再入库；
#   - 成员1：格式维护者，修改字段或事件类型前先与成员1 同步。
#
# 记录五字段：run_id / timestamp / event_type / source / data
# 自测：在项目根目录执行  python common/trace.py
# ============================================================

from datetime import datetime

# ------------------------------------------------------------
# 事件类型常量（make_event 的 event_type 参数只能取这四个）
# ------------------------------------------------------------
EVENT_AGENT_TOOL_ATTEMPTED = "agent_tool_attempted"      # Agent 表示想调用工具（尚未执行）
EVENT_GATEWAY_DECISION = "gateway_policy_decision"       # 工具网关的放行决定：allow / deny
EVENT_TOOL_EXECUTED = "tool_executed"                    # 工具实际执行
EVENT_TOOL_RESULT = "tool_result"                        # 工具返回结果

# 合法事件类型全集，供 validate_event 校验用
ALL_EVENTS = [
    EVENT_AGENT_TOOL_ATTEMPTED,
    EVENT_GATEWAY_DECISION,
    EVENT_TOOL_EXECUTED,
    EVENT_TOOL_RESULT,
]

# 一条记录必须具备的五个字段
REQUIRED_FIELDS = ["run_id", "timestamp", "event_type", "source", "data"]


def make_event(event_type, source, data, run_id):
    """生成一条标准格式的运行记录。

    参数:
        event_type: 事件类型，取文件顶部的四个 EVENT_* 常量之一
        source:     谁产生的记录，如 "user" / "agent" / "gateway" / "tool"
        data:       事件的具体内容（字典），如 {"tool": "calculator", "args": {"a": 1, "b": 2}}
        run_id:     本次运行的编号，同一运行的记录共享同一个 run_id

    返回:
        dict: 含 run_id / timestamp / event_type / source / data 五个字段的记录。
              timestamp 自动取当前时间（精确到秒）。
    """
    event_record = {
        "run_id": str(run_id),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": str(event_type),
        "source": str(source),
        "data": data,
    }
    return event_record


def validate_event(event):
    """检查一条记录是否符合格式标准（入库前建议先调用）。

    检查项: 是否为字典；五个必需字段是否齐全；
            event_type 是否合法；data 是否为字典。

    参数:
        event: 待检查的记录（预期是字典）

    返回:
        (ok, problems): ok 为 True 表示合格；为 False 时，
                        problems 为问题描述的列表（合格时为空列表）。
    """
    problems = []

    if not isinstance(event, dict):
        problems.append("记录不是字典")
        return (False, problems)

    for field in REQUIRED_FIELDS:
        if field not in event:
            problems.append(f"缺少字段: {field}")

    if "event_type" in event and event["event_type"] not in ALL_EVENTS:
        problems.append(f"未知事件类型: {event['event_type']}")

    if "data" in event and not isinstance(event["data"], dict):
        problems.append("data 必须是字典")

    return (len(problems) == 0, problems)


# ------------------------------------------------------------
# 自测演示：python common/trace.py 时运行；被 import 时不运行
# ------------------------------------------------------------
if __name__ == "__main__":
    # 示例：网关记一笔“工具执行了”
    e = make_event(EVENT_TOOL_EXECUTED, "gateway", {"tool": "calculator"}, "run-1")
    print("生成的记录:", e)

    # 好记录应校验合格
    ok, problems = validate_event(e)
    print("好记录校验:", "合格" if ok else f"不合格: {problems}")

    # 坏记录（缺字段）应被逐条指出问题
    bad = {"a": 1}
    ok2, problems2 = validate_event(bad)
    print("坏记录校验:", "合格" if ok2 else f"不合格: {problems2}")
