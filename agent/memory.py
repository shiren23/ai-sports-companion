"""
Agent 记忆系统

管理用户偏好、对话历史、长期记忆。
使用 SQLite 持久化，支持多用户隔离。
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class AgentMemory:
    """智能体记忆管理器"""

    def __init__(self, db_path: str = "./data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    favorite_teams TEXT DEFAULT '[]',
                    favorite_games TEXT DEFAULT '["LoL", "CS2", "足球", "篮球"]',
                    quiet_hours TEXT DEFAULT '00:00-08:00',
                    notification_style TEXT DEFAULT 'normal',
                    language TEXT DEFAULT 'zh-CN',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS match_monitor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    match_id TEXT NOT NULL,
                    match_name TEXT NOT NULL,
                    notify_start INTEGER DEFAULT 1,
                    notify_end INTEGER DEFAULT 1,
                    notify_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_history(user_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_monitor_user ON match_monitor(user_id, status);
            """)

    # ── 用户偏好 ───────────────────────────────

    def get_user_preferences(self, user_id: str) -> dict:
        """获取用户偏好"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM user_preferences WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if row is None:
                # 创建默认偏好
                self._create_default_preferences(user_id)
                return self.get_user_preferences(user_id)

            return {
                "user_id": row["user_id"],
                "favorite_teams": json.loads(row["favorite_teams"]),
                "favorite_games": json.loads(row["favorite_games"]),
                "quiet_hours": row["quiet_hours"],
                "notification_style": row["notification_style"],
                "language": row["language"],
            }

    def _create_default_preferences(self, user_id: str):
        """创建默认用户偏好"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO user_preferences 
                    (user_id, favorite_teams, favorite_games) 
                    VALUES (?, '[]', '["LoL", "CS2", "足球", "篮球"]')""",
                (user_id,)
            )

    def update_user_preferences(self, user_id: str, **kwargs) -> dict:
        """更新用户偏好"""
        allowed_fields = {
            "favorite_teams", "favorite_games", "quiet_hours",
            "notification_style", "language"
        }
        
        updates = {}
        for key, value in kwargs.items():
            if key in allowed_fields:
                if isinstance(value, (list, dict)):
                    updates[key] = json.dumps(value, ensure_ascii=False)
                else:
                    updates[key] = value

        if not updates:
            return self.get_user_preferences(user_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [user_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""UPDATE user_preferences 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?""",
                values
            )

        return self.get_user_preferences(user_id)

    def add_favorite_team(self, user_id: str, team_name: str):
        """添加关注队伍"""
        prefs = self.get_user_preferences(user_id)
        teams = prefs["favorite_teams"]
        if team_name not in teams:
            teams.append(team_name)
            self.update_user_preferences(user_id, favorite_teams=teams)

    def remove_favorite_team(self, user_id: str, team_name: str):
        """移除关注队伍"""
        prefs = self.get_user_preferences(user_id)
        teams = prefs["favorite_teams"]
        if team_name in teams:
            teams.remove(team_name)
            self.update_user_preferences(user_id, favorite_teams=teams)

    # ── 对话历史 ───────────────────────────────

    def add_conversation(self, user_id: str, role: str, content: str):
        """添加对话记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            # 清理过期历史（保留最近100条）
            conn.execute(
                """DELETE FROM conversation_history 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM conversation_history 
                        WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100
                    )""",
                (user_id, user_id)
            )

    def get_conversation_history(self, user_id: str, limit: int = 20) -> list[dict]:
        """获取对话历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT role, content, timestamp FROM conversation_history 
                    WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()

            return [
                {"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]}
                for r in reversed(rows)
            ]

    def clear_conversation_history(self, user_id: str):
        """清空对话历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM conversation_history WHERE user_id = ?",
                (user_id,)
            )

    # ── 比赛监控 ───────────────────────────────

    def add_match_monitor(
        self, 
        user_id: str, 
        match_id: str, 
        match_name: str,
        notify_start: bool = True,
        notify_end: bool = True,
        notify_score: bool = False,
    ) -> int:
        """添加比赛监控任务"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO match_monitor 
                    (user_id, match_id, match_name, notify_start, notify_end, notify_score)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, match_id, match_name, int(notify_start), int(notify_end), int(notify_score))
            )
            return cursor.lastrowid

    def get_active_monitors(self, user_id: str | None = None) -> list[dict]:
        """获取活跃监控任务"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM match_monitor WHERE user_id = ? AND status = 'active'",
                    (user_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM match_monitor WHERE status = 'active'"
                ).fetchall()

            return [dict(r) for r in rows]

    def update_monitor_status(self, monitor_id: int, status: str):
        """更新监控状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE match_monitor SET status = ? WHERE id = ?",
                (status, monitor_id)
            )

    def remove_monitor(self, monitor_id: int):
        """移除监控任务"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM match_monitor WHERE id = ?",
                (monitor_id,)
            )
