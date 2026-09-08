# common/trace.py
# ============================================================
# AgentSec-Lab 记录格式共享模块（第一阶段 v1）
#
# 这个文件是"记账本格式"的唯一标准，成员2（Runner）、成员3（平台）
# 都会 import 它来造记录、查记录。
#
# 运行演示：在项目根目录执行  python common/trace.py
# ============================================================

# 第一行 import：借用 Python 自带的"时钟"，等会儿用来生成时间
from datetime import datetime

# ------------------------------------------------------------
# 第 1 块：四类事件（每类 = 记账本上允许写的一种"行"）
# 这里不需要你填，看懂就行：
#   - agent_tool_attempted  : Agent 说"我想调用工具"（还没执行）
#   - gateway_policy_decision: 守门员决定放行 allow / 拒绝 deny
#   - tool_executed          : 工具真正执行了
#   - tool_result            : 工具返回了结果
# ------------------------------------------------------------
EVENT_AGENT_TOOL_ATTEMPTED = "agent_tool_attempted"
EVENT_GATEWAY_DECISION = "gateway_policy_decision"
EVENT_TOOL_EXECUTED = "tool_executed"
EVENT_TOOL_RESULT = "tool_result"

# 全部事件类型收进一个列表，validate_event 检查时会用到
ALL_EVENTS = [
    EVENT_AGENT_TOOL_ATTEMPTED,
    EVENT_GATEWAY_DECISION,
    EVENT_TOOL_EXECUTED,
    EVENT_TOOL_RESULT,
]

# 一条记录必须有的五个字段（图纸 5.4 节）
REQUIRED_FIELDS = ["run_id", "timestamp", "event_type", "source", "data"]


# ------------------------------------------------------------
# 第 2 块：make_event —— "开单员"
# 别人想记一笔账时调用它，传入 4 个信息，它返回一条标准记录（字典）
#
#   event_type: 事件类型（上面四个之一）
#   source    : 谁产生的，如 "agent" / "gateway" / "tool"
#   data      : 具体内容（一个字典，如 {"tool": "calculator", "args": {...}}）
#   run_id    : 本次运行的编号（如 "run-20260908-001"）
#
# 返回的记录长这样：
#   {
#     "run_id": "run-20260908-001",
#     "timestamp": "2026-09-08T15:30:00",
#     "event_type": "tool_executed",
#     "source": "gateway",
#     "data": {"tool": "calculator"}
#   }
# ------------------------------------------------------------
def make_event(event_type, source, data, run_id):
    # ================= TODO 1（你来填） =================
    # 任务：返回一个字典，包含五个字段：
    #   "run_id"     -> run_id 参数
    #   "timestamp"  -> 当前时间，用 datetime.now().isoformat(timespec="seconds")
    #   "event_type" -> event_type 参数
    #   "source"     -> source 参数
    #   "data"       -> data 参数
    # 提示：字典写法  {"key": 值, "key2": 值2}，函数返回用 return
    # 写好后下面演示区会打印出你造的记录
    # ====================================================
        event_record = {
             "run_id" : str(run_id),
             "timestamp" : datetime.now().isoformat(timespec="seconds"),
             "event_type" : str(event_type),
             "source" : str(source),
             "data" : data
        }

        return event_record


# ------------------------------------------------------------
# 第 3 块：validate_event —— "质检员"
# 别人交来一条记录，检查它合不合格。
# 返回 (ok, problems)：
#   ok       : True 合格 / False 不合格
#   problems : 问题列表，没问题时是空列表 []
# ------------------------------------------------------------
def validate_event(event):
    problems = []  # 先假设没问题，发现问题就往里加

    # ================= TODO 2（你来填） =================
    # 任务：按顺序做下面 4 个检查，发现问题就把描述文字加进 problems
    # 1. event 是不是字典？（不是就加 "记录不是字典"，然后直接返回）
    #    检查方法：isinstance(event, dict)  返回 True/False
    # 2. 五个必需字段（REQUIRED_FIELDS）是否都在？
    #    检查方法：for 循环遍历 REQUIRED_FIELDS，
    #             如果某个字段不在 event 里，加 f"缺少字段: {字段名}"
    # 3. event 的 "event_type" 是否在 ALL_EVENTS 列表里？
    #    不在就加 "未知事件类型: {event_type}"
    #    注意：如果 event 里没有 event_type 字段，先跳过（否则会报错）
    # 4. event 的 "data" 是不是字典？（如果不是且存在，加 "data 必须是字典"）
    # ====================================================
    if not isinstance(event, dict):
        problems.append("记录不是字典")
        return (False, problems)

    for field  in REQUIRED_FIELDS:
        if field not in event:
            problems.append(f"缺少字段: {field}")
    if "event_type" in event and event["event_type"] not in ALL_EVENTS:
        problems.append(f"未知事件类型: {event['event_type']}")
    if "data" in event and not isinstance(event["data"], dict):
        problems.append("data 必须是字典")
    # 最后一行的结论：没问题 -> (True, [])，有问题 -> (False, problems)
    return (len(problems) == 0, problems)


# ------------------------------------------------------------
# 第 4 块：演示区
# 只有当你直接运行这个文件（python common/trace.py）时，下面代码才执行；
# 当别人 import 它时，下面代码不会执行（这是 if __name__ 的作用，先不深究）
# ------------------------------------------------------------
if __name__ == "__main__":
    # 1) 造一条"工具执行了"的记录
    e = make_event(EVENT_TOOL_EXECUTED, "gateway", {"tool": "calculator"}, "run-1")
    print("生成的记录:", e)

    # 2) 拿质检员检查这条好记录，应该输出 合格
    ok, problems = validate_event(e)
    print("好记录校验:", "合格" if ok else f"不合格: {problems}")

    # 3) 故意造一条坏记录（缺字段），质检员应该抓出来
    bad = {"a": 1}
    ok2, problems2 = validate_event(bad)
    print("坏记录校验:", "合格" if ok2 else f"不合格: {problems2}")
