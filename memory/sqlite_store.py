"""
SQLite 持久化存储

提供底层数据库操作封装。
上层使用 agent.memory.AgentMemory。
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class SQLiteStore:
    """SQLite 存储引擎"""

    def __init__(self, db_path: str = "./data/store.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self):
        """数据库连接上下文"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """执行 SQL"""
        with self._connect() as conn:
            return conn.execute(sql, parameters)

    def fetchone(self, sql: str, parameters: tuple = ()) -> dict | None:
        """查询单条"""
        with self._connect() as conn:
            row = conn.execute(sql, parameters).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, parameters: tuple = ()) -> list[dict]:
        """查询多条"""
        with self._connect() as conn:
            rows = conn.execute(sql, parameters).fetchall()
            return [dict(r) for r in rows]

    def executescript(self, script: str):
        """执行脚本"""
        with self._connect() as conn:
            conn.executescript(script)
            conn.commit()
