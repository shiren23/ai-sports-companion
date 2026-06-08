"""
数据源客户端抽象基类

统一不同数据源的接口，方便后续扩展更多数据源。
"""

from abc import ABC, abstractmethod
from typing import Any


class MatchSearchResult(dict):
    """统一的比赛搜索结果格式"""
    
    @classmethod
    def from_esports(
        cls,
        match_id: str,
        name: str,
        status: str,
        scheduled_at: str,
        league: str,
        videogame: str,
        opponents: list[dict],
        **extra
    ) -> "MatchSearchResult":
        return cls({
            "id": match_id,
            "name": name,
            "status": status,  # not_started / running / finished
            "scheduled_at": scheduled_at,
            "league": league,
            "game_type": videogame,
            "teams": [o.get("opponent", {}).get("name", "") for o in opponents],
            "source": "pandascore",
            "extra": extra,
        })
    
    @classmethod
    def from_football(
        cls,
        match_id: str,
        name: str,
        status: str,
        date: str,
        league: str,
        home_team: str,
        away_team: str,
        home_score: int | None = None,
        away_score: int | None = None,
        **extra
    ) -> "MatchSearchResult":
        return cls({
            "id": match_id,
            "name": name,
            "status": status,
            "scheduled_at": date,
            "league": league,
            "game_type": "football",
            "teams": [home_team, away_team],
            "score": f"{home_score}-{away_score}" if home_score is not None else None,
            "source": "football_api",
            "extra": extra,
        })


class BaseSportsClient(ABC):
    """体育数据源客户端基类"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def search_matches(self, **kwargs) -> list[dict]:
        """搜索比赛"""
        pass

    @abstractmethod
    def get_match_detail(self, match_id: str) -> dict:
        """获取比赛详情"""
        pass

    @abstractmethod
    def get_team_info(self, team_name: str) -> dict:
        """获取队伍信息"""
        pass
