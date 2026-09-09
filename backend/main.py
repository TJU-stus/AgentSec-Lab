# backend/main.py
# ============================================================
# AgentSec-Lab 平台后端入口（成员3）
#
# 文件分工：
#   main.py           本文件：路由（JSON 接口 + 三个页面）
#   models.py         三张数据表怎么定义
#   database.py       数据库怎么连（SQLite）
#   runner_client.py  怎么调用成员2 的 Runner（演示 / 真实两种模式）
#
# 启动（务必在仓库根目录，不是 backend/ 里）：
#   .venv\Scripts\activate
#   uvicorn backend.main:app --reload
# 页面: http://127.0.0.1:8000    接口说明页: http://127.0.0.1:8000/docs
# ============================================================

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend import database, runner_client
from common.trace import validate_event   # 成员1 的共享模块：校验记录格式

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="AgentSec-Lab 平台后端")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

if runner_client.MOCK:
    print("⚠ 演示模式（PLATFORM_MOCK_RUNNER=1）：未真正调用 Runner，记录为伪造数据。"
          "Runner 就绪后设为 0 切换真实调用。")

database.init_db()   # 首次访问自动建表；IF NOT EXISTS，重复执行无害


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _new_run_id():
    return f"run-{uuid.uuid4().hex[:12]}"


def _get_agent_or_404(agent_id):
    agent = database.query_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} 不存在")
    return agent


def execute_run(agent, task_text):
    """执行一次运行的完整流程：建 run → 调 Runner → 存记录 → 收尾。

    返回 (run_id, status)。Runner 调不通时记为失败运行
    （status=failed，错误信息写进 runs.final_answer），
    不抛异常、不悄悄失败——这是验收标准之一。
    """
    run_id = _new_run_id()
    database.execute(
        "INSERT INTO runs (run_id, agent_id, task_text, status, created_at) "
        "VALUES (?, ?, ?, 'running', ?)",
        (run_id, agent["id"], task_text, _now()),
    )
    try:
        result = runner_client.submit_task(agent, task_text, run_id)
        for event in result["trace"]:
            database.execute(
                "INSERT INTO trace_events (run_id, timestamp, event_type, source, data) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    run_id,
                    str(event.get("timestamp", _now())),
                    str(event.get("event_type", "")),
                    str(event.get("source", "")),
                    json.dumps(event.get("data", {}), ensure_ascii=False, default=str),
                ),
            )
        status, final_answer = "success", str(result.get("final_answer", ""))
    except Exception as exc:   # 网络不通、返回不合法等：把失败也记下来
        status, final_answer = "failed", f"运行失败：{exc}"

    database.execute(
        "UPDATE runs SET status = ?, final_answer = ?, finished_at = ? WHERE run_id = ?",
        (status, final_answer, _now(), run_id),
    )
    return run_id, status


# ============================================================
# JSON 接口（/docs 页面可见；给联调和成员1 的验收脚本用）
# ============================================================

class AgentCreate(BaseModel):
    name: str
    description: str = ""
    dify_app_id: str = ""


class RunCreate(BaseModel):
    agent_id: int
    task_text: str


@app.get("/api/agents")
def api_list_agents():
    return database.query_all("SELECT * FROM agents ORDER BY id")


@app.post("/api/agents", status_code=201)
def api_create_agent(body: AgentCreate):
    cur = database.execute(
        "INSERT INTO agents (name, description, dify_app_id, created_at) VALUES (?, ?, ?, ?)",
        (body.name, body.description, body.dify_app_id, _now()),
    )
    return database.query_one("SELECT * FROM agents WHERE id = ?", (cur.lastrowid,))


@app.get("/api/runs")
def api_list_runs():
    return database.query_all(
        "SELECT r.*, a.name AS agent_name FROM runs r "
        "LEFT JOIN agents a ON a.id = r.agent_id "
        "ORDER BY r.created_at DESC, r.run_id DESC"
    )


@app.get("/api/runs/{run_id}")
def api_get_run(run_id: str):
    run = _get_run_or_404(run_id)
    events = database.query_all(
        "SELECT * FROM trace_events WHERE run_id = ? ORDER BY id", (run_id,))
    return {"run": run, "events": events}


@app.post("/api/runs", status_code=201)
def api_create_run(body: RunCreate):
    agent = _get_agent_or_404(body.agent_id)
    run_id, status = execute_run(agent, body.task_text)
    return {"run_id": run_id, "status": status}


# ============================================================
# 页面（首页 / 运行页 / 记录页）
# ============================================================

@app.get("/")
def page_home(request: Request):
    agents = database.query_all("SELECT * FROM agents ORDER BY id")
    recent_runs = database.query_all(
        "SELECT r.*, a.name AS agent_name FROM runs r "
        "LEFT JOIN agents a ON a.id = r.agent_id "
        "ORDER BY r.created_at DESC, r.run_id DESC LIMIT 10")
    return templates.TemplateResponse(
        request, "index.html", {"agents": agents, "recent_runs": recent_runs})


@app.post("/agents")
def page_create_agent(name: str = Form(...), description: str = Form(""),
                      dify_app_id: str = Form("")):
    database.execute(
        "INSERT INTO agents (name, description, dify_app_id, created_at) VALUES (?, ?, ?, ?)",
        (name, description, dify_app_id, _now()),
    )
    return RedirectResponse("/", status_code=303)


@app.get("/agents/{agent_id}/run")
def page_run_form(request: Request, agent_id: int):
    agent = _get_agent_or_404(agent_id)
    return templates.TemplateResponse(request, "run.html", {"agent": agent})


@app.post("/agents/{agent_id}/run")
def page_run_submit(agent_id: int, task_text: str = Form(...)):
    agent = _get_agent_or_404(agent_id)
    run_id, _status = execute_run(agent, task_text)
    return RedirectResponse(f"/runs/{run_id}", status_code=303)


@app.get("/runs")
def page_runs_list(request: Request):
    runs = database.query_all(
        "SELECT r.*, a.name AS agent_name FROM runs r "
        "LEFT JOIN agents a ON a.id = r.agent_id "
        "ORDER BY r.created_at DESC, r.run_id DESC")
    return templates.TemplateResponse(request, "runs_list.html", {"runs": runs})


def _get_run_or_404(run_id):
    run = database.query_one(
        "SELECT r.*, a.name AS agent_name FROM runs r "
        "LEFT JOIN agents a ON a.id = r.agent_id WHERE r.run_id = ?", (run_id,))
    if not run:
        raise HTTPException(status_code=404, detail=f"运行 {run_id} 不存在")
    return run


@app.get("/runs/{run_id}")
def page_trace(request: Request, run_id: str):
    run = _get_run_or_404(run_id)

    # 展示前先用成员1 的校验函数逐条检查；不合格的标警示，而不是白屏
    events = []
    for row in database.query_all(
            "SELECT * FROM trace_events WHERE run_id = ? ORDER BY id", (run_id,)):
        try:
            data = json.loads(row["data"])
        except (ValueError, TypeError):
            data = {"raw": row["data"]}
        record = {
            "run_id": row["run_id"],
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "source": row["source"],
            "data": data,
        }
        ok, problems = validate_event(record)
        events.append({
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "source": row["source"],
            "data_pretty": json.dumps(data, ensure_ascii=False, indent=2),
            "ok": ok,
            "problems": "；".join(problems),
        })

    return templates.TemplateResponse(
        request, "trace.html", {"run": run, "events": events})
