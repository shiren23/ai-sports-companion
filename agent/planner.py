"""
任务规划器

将用户的高层次意图拆解为可执行的任务序列。
例如："帮我盯着 T1" → [搜索T1比赛, 获取比赛详情, 设置监控]

目前采用简化版：直接在 LLM 的 function calling 中完成规划。
后续可扩展为更复杂的 DAG 任务调度。
"""

from typing import Any


class TaskPlanner:
    """任务规划器 - 当前版本为简化实现"""

    def plan(self, user_intent: str, context: dict) -> list[dict]:
        """
        根据用户意图生成任务计划
        
        返回任务列表，每个任务包含：
        - task_type: 任务类型
        - parameters: 任务参数
        - depends_on: 依赖的其他任务
        """
        # 简化版：直接返回空列表，由 LLM 通过 function calling 自行规划
        # 后续版本可在此实现意图分类 → 任务拆解 → 依赖分析
        return []

    def should_proactive_notify(self, user_prefs: dict, match_data: dict) -> tuple[bool, str]:
        """
        判断是否应该主动推送通知
        
        Returns:
            (should_notify, reason)
        """
        favorite_teams = user_prefs.get("favorite_teams", [])
        notification_style = user_prefs.get("notification_style", "normal")
        quiet_hours = user_prefs.get("quiet_hours", "00:00-08:00")
        
        # 检查是否关注相关队伍
        match_teams = match_data.get("teams", [])
        is_favorite = any(t in favorite_teams for t in match_teams)
        
        if not is_favorite and notification_style != "aggressive":
            return False, "非关注队伍，且通知风格非激进"
        
        # 检查勿扰时段（简化实现）
        # TODO: 完善时间区间判断
        
        # 根据通知风格判断
        if notification_style == "silent" and not is_favorite:
            return False, "静默模式，仅通知关注队伍"
        
        return True, "匹配用户关注或通知设置"
