"""
工具注册与调度系统

所有 Agent 可调用的外部能力在此注册。
采用 OpenAI Function Calling 格式定义工具 schema。
"""

import json
from typing import Any, Callable

from api_clients.pandascore import PandaScoreClient
from api_clients.football_api import FootballAPIClient
from api_clients.base import MatchSearchResult


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []
        
        # 初始化 API 客户端
        self.pandascore = PandaScoreClient()
        self.football = FootballAPIClient()
        
        self._register_all()

    def _register_all(self):
        """注册所有可用工具"""
        self.register(
            name="search_matches",
            description="搜索比赛，支持按时间范围、队伍名称、游戏类型筛选",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如队伍名、联赛名。为空则查全部"
                    },
                    "game_type": {
                        "type": "string",
                        "enum": ["lol", "cs2", "dota2", "football", "basketball", "any"],
                        "description": "游戏/运动类型"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["today", "tomorrow", "week", "live", "any"],
                        "description": "时间范围"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量上限",
                        "default": 10
                    }
                },
                "required": []
            },
            func=self._search_matches
        )

        self.register(
            name="get_match_detail",
            description="获取单场比赛的详细信息",
            parameters={
                "type": "object",
                "properties": {
                    "match_id": {
                        "type": "string",
                        "description": "比赛ID"
                    },
                    "source": {
                        "type": "string",
                        "enum": ["pandascore", "football_api"],
                        "description": "数据源"
                    }
                },
                "required": ["match_id", "source"]
            },
            func=self._get_match_detail
        )

        self.register(
            name="get_team_info",
            description="获取队伍/球队信息",
            parameters={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "队伍名称"
                    }
                },
                "required": ["team_name"]
            },
            func=self._get_team_info
        )

        self.register(
            name="set_reminder",
            description="为用户设置比赛提醒",
            parameters={
                "type": "object",
                "properties": {
                    "match_id": {
                        "type": "string",
                        "description": "比赛ID"
                    },
                    "match_name": {
                        "type": "string",
                        "description": "比赛名称，用于展示"
                    },
                    "remind_before": {
                        "type": "integer",
                        "description": "赛前几分钟提醒",
                        "default": 10
                    }
                },
                "required": ["match_id", "match_name"]
            },
            func=self._set_reminder
        )

        self.register(
            name="start_monitor",
            description="开始监控比赛状态（开始、比分变化、结束）",
            parameters={
                "type": "object",
                "properties": {
                    "match_id": {
                        "type": "string",
                        "description": "比赛ID"
                    },
                    "match_name": {
                        "type": "string",
                        "description": "比赛名称"
                    },
                    "notify_start": {
                        "type": "boolean",
                        "description": "比赛开始时通知",
                        "default": True
                    },
                    "notify_end": {
                        "type": "boolean",
                        "description": "比赛结束时通知",
                        "default": True
                    },
                    "notify_score": {
                        "type": "boolean",
                        "description": "比分变化时通知",
                        "default": False
                    }
                },
                "required": ["match_id", "match_name"]
            },
            func=self._start_monitor
        )

        self.register(
            name="get_user_preferences",
            description="获取当前用户的偏好设置",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            func=self._get_user_preferences
        )

        self.register(
            name="update_user_preferences",
            description="更新用户偏好，如关注队伍、勿扰时段等",
            parameters={
                "type": "object",
                "properties": {
                    "favorite_teams": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关注的队伍列表"
                    },
                    "quiet_hours": {
                        "type": "string",
                        "description": "勿扰时段，格式 HH:MM-HH:MM"
                    },
                    "notification_style": {
                        "type": "string",
                        "enum": ["aggressive", "normal", "silent"],
                        "description": "通知风格"
                    }
                },
                "required": []
            },
            func=self._update_user_preferences
        )

    def register(self, name: str, description: str, parameters: dict, func: Callable):
        """注册一个工具"""
        self._tools[name] = func
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        })

    def get_openai_tools(self) -> list[dict]:
        """获取 OpenAI Function Calling 格式的工具定义"""
        return self._schemas

    def execute(self, name: str, arguments: dict) -> Any:
        """执行工具调用"""
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        
        try:
            return self._tools[name](**arguments)
        except Exception as e:
            return {"error": str(e)}

    # ── 工具实现 ───────────────────────────────

    def _search_matches(self, query: str = "", game_type: str = "any", time_range: str = "today", limit: int = 10) -> dict:
        """搜索比赛"""
        results = []
        
        # 电竞查询
        if game_type in ("any", "lol", "cs2", "dota2"):
            try:
                esports = self.pandascore.search_matches(
                    query=query,
                    videogame=game_type if game_type != "any" else None,
                    time_range=time_range,
                    limit=limit
                )
                results.extend(esports)
            except Exception as e:
                pass  # 忽略单个数据源错误
        
        # 足球查询
        if game_type in ("any", "football"):
            try:
                football = self.football.search_matches(
                    query=query,
                    time_range=time_range,
                    limit=limit
                )
                results.extend(football)
            except Exception as e:
                pass
        
        # 按时间排序
        results.sort(key=lambda x: x.get("scheduled_at", x.get("date", "")))
        
        return {
            "matches": results[:limit],
            "total": len(results),
            "filters": {"query": query, "game_type": game_type, "time_range": time_range}
        }

    def _get_match_detail(self, match_id: str, source: str) -> dict:
        """获取比赛详情"""
        if source == "pandascore":
            return self.pandascore.get_match_detail(match_id)
        elif source == "football_api":
            return self.football.get_match_detail(match_id)
        return {"error": "Unknown source"}

    def _get_team_info(self, team_name: str) -> dict:
        """获取队伍信息"""
        # 先查电竞，再查体育
        try:
            return self.pandascore.get_team_info(team_name)
        except:
            try:
                return self.football.get_team_info(team_name)
            except:
                return {"name": team_name, "info": "暂无详细信息"}

    def _set_reminder(self, match_id: str, match_name: str, remind_before: int = 10) -> dict:
        """设置提醒"""
        return {
            "status": "scheduled",
            "match_id": match_id,
            "match_name": match_name,
            "remind_before_minutes": remind_before,
            "message": f"已设置提醒：{match_name} 将在赛前 {remind_before} 分钟通知你"
        }

    def _start_monitor(self, match_id: str, match_name: str, notify_start: bool = True, notify_end: bool = True, notify_score: bool = False) -> dict:
        """开始监控"""
        from .memory import AgentMemory
        memory = AgentMemory()
        monitor_id = memory.add_match_monitor(
            user_id="default",
            match_id=match_id,
            match_name=match_name,
            notify_start=notify_start,
            notify_end=notify_end,
            notify_score=notify_score,
        )
        return {
            "status": "monitoring_started",
            "monitor_id": monitor_id,
            "match_name": match_name,
            "notifications": {
                "start": notify_start,
                "end": notify_end,
                "score_change": notify_score
            }
        }

    def _get_user_preferences(self) -> dict:
        """获取用户偏好"""
        from .memory import AgentMemory
        memory = AgentMemory()
        return memory.get_user_preferences("default")

    def _update_user_preferences(self, favorite_teams: list = None, quiet_hours: str = None, notification_style: str = None) -> dict:
        """更新用户偏好"""
        from .memory import AgentMemory
        memory = AgentMemory()
        
        kwargs = {}
        if favorite_teams is not None:
            kwargs["favorite_teams"] = favorite_teams
        if quiet_hours is not None:
            kwargs["quiet_hours"] = quiet_hours
        if notification_style is not None:
            kwargs["notification_style"] = notification_style
        
        updated = memory.update_user_preferences("default", **kwargs)
        return {
            "status": "updated",
            "preferences": updated
        }
