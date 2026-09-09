# 平台（成员3）使用与开发说明

> 对应《第一阶段任务分配指导书》成员3 任务 1-3：后端骨架、三张数据表、三个页面。
> 状态：页面与数据层已完成自测（演示模式）；待成员2 的 Runner 就绪后切真实调用并联调。

## 怎么启动

```bash
# 1. 在仓库根目录（不是 backend/ 里）
cd AgentSec-Lab

# 2. 激活虚拟环境、装依赖（首次）
.venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. 启动
uvicorn backend.main:app --reload
```

- 页面：<http://127.0.0.1:8000>
- 接口说明页（自动生成）：<http://127.0.0.1:8000/docs>
- 数据库：`backend/agentsec.db`（SQLite 单文件，已被 .gitignore 忽略，不入仓库；重启数据仍在）

## 三个页面

| 页面 | 地址 | 说明 |
| --- | --- | --- |
| 首页 | `/` | Agent 列表 + 新建 Agent 表单 + 最近运行 |
| 运行页 | `/agents/{id}/run` | 输入任务文字 → 调 Runner → 跳转记录页 |
| 记录页 | `/runs/{run_id}` | 该次运行的完整流水账，逐条经 `common/trace.py` 校验，不合格标警示 |

另有 `/runs` 运行历史页（验收画面第 5 条「每次运行独立编号、记录互不混淆」的演示入口，超出任务书的加分项）。

## JSON 接口（给联调和成员1 的验收脚本用）

- `GET /api/agents`、`POST /api/agents`（name / description / dify_app_id）
- `POST /api/runs`（agent_id / task_text → 返回 run_id）
- `GET /api/runs`、`GET /api/runs/{run_id}`（run + events）

## 演示模式与真实模式（重要）

成员2 的 Runner 尚未就绪，当前默认**演示模式**：`runner_client.py` 伪造符合
`common/trace.py` 格式的记录（能算「计算 a±b」类算式、对非算式走拒绝路径），
用于先把页面做完、演示完整画面。启动时控制台会打印警告。

环境变量开关：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `PLATFORM_MOCK_RUNNER` | `1`（演示） | 设为 `0` 切换真实调用 Runner |
| `RUNNER_BASE_URL` | `http://127.0.0.1:8001` | Runner 服务地址，待成员2 确认 |

## 待办（依赖成员2）

1. Runner 接口（路径、字段）确认后，修改 `backend/runner_client.py` 的
   `_real_submit` 一处即可，页面和数据层不用动；随后把默认值改为真实模式并
   删除 `_mock_submit` 演示段。
2. `agents` 表的 Dify App ID 由成员2 提供，页面上可后补。

## 数据表

见 `backend/models.py`：agents / runs / trace_events 三张表，
`trace_events` 字段含义以 `common/trace.py`（成员1）为准。
