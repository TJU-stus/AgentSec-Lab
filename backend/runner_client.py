# backend/runner_client.py
# ============================================================
# 平台 → Runner 的对接模块（成员3 调成员2）
#
# 图纸（docs/architecture.md 第 5.1 节）约定：平台只和 Runner 说话，
# 不直接碰 Dify。
#
# ⚠ 接口现状：Runner 的地址和字段名还在待确认清单（第 10 节第 5 条）。
#   下方 _real_submit 里的路径和字段是按图纸描述先占位的合理猜测，
#   成员2 回填 5.1 节后只需改这一个文件，页面和其他代码都不用动。
#
# 演示模式：Runner 尚未就绪时，PLATFORM_MOCK_RUNNER=1（当前默认），
#   由本模块伪造一份符合 common/trace.py 格式的记录，先把三个页面
#   做出来、演示「输入→结果→记录」的完整画面。
#   Runner 就绪后设为 0（或直接删掉 _mock_submit 一段）切换真实调用。
# ============================================================

import os
import re

from common.trace import (
    EVENT_AGENT_TOOL_ATTEMPTED,
    EVENT_GATEWAY_DECISION,
    EVENT_TOOL_EXECUTED,
    EVENT_TOOL_RESULT,
    make_event,
)

# Runner 服务地址（成员2 部署后确认；可用环境变量 RUNNER_BASE_URL 覆盖）
RUNNER_BASE_URL = os.environ.get("RUNNER_BASE_URL", "http://127.0.0.1:8001")

# 1 = 演示模式（不真正调 Runner）；0 = 真实调用
MOCK = os.environ.get("PLATFORM_MOCK_RUNNER", "1") == "1"


def submit_task(agent, task_text, run_id):
    """把一次任务交给 Runner，拿回最终回答和全部运行记录。

    参数:
        agent:     agents 表的一行（字典），Runner 需要知道用哪个 Agent
        task_text: 用户输入的任务文字
        run_id:    平台生成的本次运行编号

    返回:
        dict: {"final_answer": str, "trace": [事件, ...]}
              每个事件是符合 common/trace.py 五字段格式的字典。

    抛错:
        Runner 调不通或返回不合法时抛异常，由调用方记为失败运行。
    """
    if MOCK:
        return _mock_submit(task_text, run_id)
    return _real_submit(agent, task_text, run_id)


# ------------------------------------------------------------ 真实调用
# ------------------------------------------------------------

def _real_submit(agent, task_text, run_id):
    import httpx   # 放在函数内：演示模式下不强依赖网络库

    response = httpx.post(
        f"{RUNNER_BASE_URL}/run",        # ⚠ 路径为占位，待成员2 确认
        json={                           # ⚠ 字段名为占位，待成员2 确认
            "run_id": run_id,
            "task_text": task_text,
            "dify_app_id": agent.get("dify_app_id", ""),
        },
        timeout=120,                     # Agent 跑一轮任务可能较慢
    )
    response.raise_for_status()
    result = response.json()

    if not isinstance(result.get("trace"), list):
        raise ValueError(f"Runner 返回里没有合法的 trace 列表: {result!r}")
    return {
        "final_answer": str(result.get("final_answer", "")),
        "trace": result["trace"],
    }


# ------------------------------------------------------------ 演示模式
# （Runner 就绪并验证通过后，这一段可以整体删除）
# ------------------------------------------------------------

_CALC_RE = re.compile(r"计算\s*(\d+)\s*([+\-*/])\s*(\d+)")


def _deny(task_args, reason, run_id):
    """非算式输入等场景：Agent 想调工具 → 守门员拒绝。
    对应验收画面第 6 条：错误要被记录下来，而不是悄悄失败。"""
    return [
        make_event(EVENT_AGENT_TOOL_ATTEMPTED, "agent",
                   {"tool": "calculator", "args": task_args}, run_id),
        make_event(EVENT_GATEWAY_DECISION, "gateway",
                   {"tool": "calculator", "decision": "deny", "reason": reason}, run_id),
    ]


def _mock_submit(task_text, run_id):
    m = _CALC_RE.search(task_text)
    if not m:
        return {
            "final_answer": "无法处理：输入的不是合法算式（示例：计算 123+456）",
            "trace": _deny({"text": task_text}, "输入不是合法算式", run_id),
        }

    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    if op == "/" and b == 0:
        return {
            "final_answer": "无法处理：除数为零",
            "trace": _deny({"a": a, "b": b, "op": op}, "除数为零", run_id),
        }

    value = {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[op]
    trace = [
        make_event(EVENT_AGENT_TOOL_ATTEMPTED, "agent",
                   {"tool": "calculator", "args": {"a": a, "b": b, "op": op}}, run_id),
        make_event(EVENT_GATEWAY_DECISION, "gateway",
                   {"tool": "calculator", "decision": "allow"}, run_id),
        make_event(EVENT_TOOL_EXECUTED, "tool",
                   {"tool": "calculator"}, run_id),
        make_event(EVENT_TOOL_RESULT, "tool",
                   {"tool": "calculator", "result": value}, run_id),
    ]
    return {"final_answer": f"计算结果是 {value}", "trace": trace}
