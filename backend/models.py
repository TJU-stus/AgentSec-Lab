# backend/models.py
# ============================================================
# AgentSec-Lab 平台数据表定义（成员3）
#
# 三张表（按 MVP 最小需求设计，不提前做复杂功能）：
#   agents        Agent 信息：名称、描述、Dify App ID（问成员2要）
#   runs          每次运行：run_id、任务文字、最终回答、状态、时间
#   trace_events  运行记录流水账：字段含义以 common/trace.py 为准
#
# 说明：runs.note 是特意留的「备注」位——以后记「这次运行用的什么
# 模型、Agent 什么配置」，第二阶段做开/关防护对比实验时要用。
# ============================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    dify_app_id  TEXT NOT NULL DEFAULT '',      -- Dify 里该 Agent 的编号，由成员2提供
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,              -- 本次运行的唯一编号，平台生成
    agent_id     INTEGER NOT NULL REFERENCES agents(id),
    task_text    TEXT NOT NULL,                 -- 用户输入的任务文字
    final_answer TEXT,                          -- 最终回答；失败时存错误提示
    status       TEXT NOT NULL DEFAULT 'running',   -- running / success / failed
    note         TEXT NOT NULL DEFAULT '',      -- 备注：以后记模型、配置等
    created_at   TEXT NOT NULL,                 -- 创建（提交任务）时间
    finished_at  TEXT                           -- 结束时间
);

CREATE TABLE IF NOT EXISTS trace_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,   -- 自增序号即事件到达顺序
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    timestamp  TEXT NOT NULL,                     -- 事件自带的时间（common/trace.py 格式）
    event_type TEXT NOT NULL,
    source     TEXT NOT NULL,
    data       TEXT NOT NULL                      -- JSON 字符串，含义以 common/trace.py 为准
);

CREATE INDEX IF NOT EXISTS idx_trace_events_run ON trace_events(run_id);
"""
