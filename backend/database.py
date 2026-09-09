# backend/database.py
# ============================================================
# AgentSec-Lab 平台数据库连接（成员3）
#
# 用 SQLite：整个数据库就是 backend/agentsec.db 一个文件。
# 该文件已在 .gitignore 中忽略（数据库不入仓库，各自本地保留），
# 程序重启后数据仍在——这正是验收标准之一。
# 表结构定义见 backend/models.py。
# ============================================================

import sqlite3
from pathlib import Path

from backend import models

DB_PATH = Path(__file__).resolve().parent / "agentsec.db"


def get_connection():
    """拿一个数据库连接。row_factory 让查询结果可以按列名取值。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # 让 REFERENCES 约束真正生效
    return conn


def init_db():
    """建表。SQL 全部带 IF NOT EXISTS，重复调用不报错、不丢数据。"""
    conn = get_connection()
    try:
        conn.executescript(models.SCHEMA)
        conn.commit()
    finally:
        conn.close()


def query_all(sql, params=()):
    """查多行，返回字典列表（页面模板直接可用）。"""
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_one(sql, params=()):
    """查一行，返回字典；查不到返回 None。"""
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """执行写操作（INSERT / UPDATE / DELETE），返回游标（可取 lastrowid、rowcount）。"""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur
    finally:
        conn.close()
