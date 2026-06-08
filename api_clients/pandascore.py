"""
PandaScore API 客户端

电竞数据：LoL, CS2, Dota2, Valorant, RL 等
免费版：1000 requests/hour，赛程+基础数据免费
"""

import os
from datetime import datetime, timedelta

import httpx

from .base import BaseSportsClient, MatchSearchResult


class PandaScoreClient(BaseSportsClient):
    """PandaScore 电竞数据客户端"""

    DEFAULT_BASE_URL = "https://api.pandascore.co"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("PANDASCORE_API_KEY", "")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=10.0,
        )

    def search_matches(
        self,
        query: str = "",
        videogame: str | None = None,
        time_range: str = "today",
        limit: int = 10,
    ) -> list[dict]:
        """搜索电竞比赛"""
        params = {"page[size]": limit}

        # 时间范围过滤
        now = datetime.utcnow()
        if time_range == "today":
            begin = now.strftime("%Y-%m-%dT00:00:00Z")
            end = (now + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            params["filter[begin_at]"] = f"{begin},{end}"
        elif time_range == "tomorrow":
            begin = (now + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            end = (now + timedelta(days=2)).strftime("%Y-%m-%dT00:00:00Z")
            params["filter[begin_at]"] = f"{begin},{end}"
        elif time_range == "week":
            begin = now.strftime("%Y-%m-%dT00:00:00Z")
            end = (now + timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
            params["filter[begin_at]"] = f"{begin},{end}"
        elif time_range == "live":
            params["filter[status]"] = "running"

        # 游戏类型过滤
        videogame_ids = {
            "lol": 1,
            "cs2": 4,
            "csgo": 4,
            "dota2": 4,  # Dota2
            "valorant": 26,
            "rl": 14,  # Rocket League
        }
        if videogame and videogame.lower() in videogame_ids:
            params["filter[videogame]"] = videogame_ids[videogame.lower()]

        # 队伍搜索（简化：先查所有 upcoming matches，再本地过滤）
        endpoint = "/matches/upcoming" if time_range != "live" else "/matches/running"
        
        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return [MatchSearchResult({"error": "API 请求超限，请稍后再试"})]
            raise
        except Exception:
            # 如果没有 API key，返回演示数据
            if not self.api_key or self.api_key == "your_pandascore_token_here":
                return self._get_demo_data(query, videogame, time_range)
            raise

        results = []
        for match in data:
            # 如果有 query，本地过滤
            if query:
                match_text = json.dumps(match, ensure_ascii=False).lower()
                if query.lower() not in match_text:
                    continue

            # 格式化时间
            begin_at = match.get("begin_at", "")
            scheduled = ""
            if begin_at:
                try:
                    dt = datetime.fromisoformat(begin_at.replace("Z", "+00:00"))
                    scheduled = dt.strftime("%m月%d日 %H:%M")
                except:
                    scheduled = begin_at

            results.append(MatchSearchResult.from_esports(
                match_id=str(match.get("id", "")),
                name=match.get("name", "未知比赛"),
                status=match.get("status", "unknown"),
                scheduled_at=scheduled,
                league=match.get("league", {}).get("name", "未知联赛"),
                videogame=match.get("videogame", {}).get("name", "未知游戏"),
                opponents=match.get("opponents", []),
                series=match.get("serie", {}).get("full_name", ""),
            ))

        return results

    def get_match_detail(self, match_id: str) -> dict:
        """获取比赛详情"""
        try:
            response = self.client.get(f"/matches/{match_id}")
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"error": f"无法获取比赛 {match_id} 的详情"}

    def get_team_info(self, team_name: str) -> dict:
        """搜索队伍信息"""
        try:
            response = self.client.get("/teams", params={"search[name]": team_name})
            response.raise_for_status()
            data = response.json()
            if data:
                return {
                    "name": data[0].get("name", team_name),
                    "acronym": data[0].get("acronym", ""),
                    "location": data[0].get("location", ""),
                    "image_url": data[0].get("image_url", ""),
                }
        except Exception:
            pass
        return {"name": team_name, "info": "暂无详细信息"}

    def _get_demo_data(self, query: str, videogame: str | None, time_range: str) -> list[dict]:
        """演示数据（无 API key 时使用）"""
        demos = [
            MatchSearchResult.from_esports(
                match_id="demo_001",
                name="T1 vs GEN",
                status="not_started",
                scheduled_at="06月10日 16:00",
                league="LCK 2025 Summer",
                videogame="League of Legends",
                opponents=[
                    {"opponent": {"name": "T1"}},
                    {"opponent": {"name": "Gen.G"}}
                ],
                note="演示数据 - 请配置 PANDASCORE_API_KEY 获取真实数据"
            ),
            MatchSearchResult.from_esports(
                match_id="demo_002",
                name="NAVI vs Vitality",
                status="not_started",
                scheduled_at="06月10日 22:00",
                league="BLAST Premier",
                videogame="CS2",
                opponents=[
                    {"opponent": {"name": "NAVI"}},
                    {"opponent": {"name": "Team Vitality"}}
                ],
                note="演示数据 - 请配置 PANDASCORE_API_KEY 获取真实数据"
            ),
            MatchSearchResult.from_esports(
                match_id="demo_003",
                name="G2 Esports vs BLG",
                status="not_started",
                scheduled_at="06月11日 20:00",
                league="MSI 2025",
                videogame="League of Legends",
                opponents=[
                    {"opponent": {"name": "G2 Esports"}},
                    {"opponent": {"name": "Bilibili Gaming"}}
                ],
                note="演示数据 - 请配置 PANDASCORE_API_KEY 获取真实数据"
            ),
        ]

        # 过滤
        if videogame and videogame != "any":
            vg_map = {"lol": "league of legends", "cs2": "cs2", "dota2": "dota2"}
            target = vg_map.get(videogame.lower(), videogame.lower())
            demos = [d for d in demos if target in d.get("game_type", "").lower()]

        if query:
            demos = [d for d in demos if query.lower() in d.get("name", "").lower()]

        return demos


import json  # noqa: E402
