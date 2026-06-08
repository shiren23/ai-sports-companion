"""
API-Football 客户端

足球数据：全球 1200+ 联赛
免费版：100 requests/day
"""

import os
from datetime import datetime, timedelta

import httpx

from .base import BaseSportsClient, MatchSearchResult


class FootballAPIClient(BaseSportsClient):
    """API-Football 客户端"""

    DEFAULT_BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("FOOTBALL_API_KEY", "")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-apisports-key": self.api_key,
                "Accept": "application/json",
            },
            timeout=10.0,
        )

    def search_matches(
        self,
        query: str = "",
        time_range: str = "today",
        limit: int = 10,
    ) -> list[dict]:
        """搜索足球比赛"""
        now = datetime.now()
        
        if time_range == "today":
            date_str = now.strftime("%Y-%m-%d")
        elif time_range == "tomorrow":
            date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif time_range == "week":
            # 获取未来7天的比赛
            return self._get_week_matches(limit)
        elif time_range == "live":
            return self._get_live_matches(limit)
        else:
            date_str = now.strftime("%Y-%m-%d")

        try:
            response = self.client.get("/fixtures", params={"date": date_str})
            response.raise_for_status()
            data = response.json()
            matches = data.get("response", [])
        except Exception:
            if not self.api_key or self.api_key == "your_api_football_key_here":
                return self._get_demo_data(query, time_range)
            return []

        # 本地过滤
        if query:
            matches = [
                m for m in matches
                if query.lower() in m.get("teams", {}).get("home", {}).get("name", "").lower()
                or query.lower() in m.get("teams", {}).get("away", {}).get("name", "").lower()
                or query.lower() in m.get("league", {}).get("name", "").lower()
            ]

        results = []
        for match in matches[:limit]:
            fixture = match.get("fixture", {})
            teams = match.get("teams", {})
            goals = match.get("goals", {})
            league = match.get("league", {})
            
            date = fixture.get("date", "")
            scheduled = ""
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    scheduled = dt.strftime("%m月%d日 %H:%M")
                except:
                    scheduled = date

            results.append(MatchSearchResult.from_football(
                match_id=str(fixture.get("id", "")),
                name=f"{teams.get('home', {}).get('name', '')} vs {teams.get('away', {}).get('name', '')}",
                status=fixture.get("status", {}).get("short", "NS"),
                date=scheduled,
                league=league.get("name", "未知联赛"),
                home_team=teams.get("home", {}).get("name", ""),
                away_team=teams.get("away", {}).get("name", ""),
                home_score=goals.get("home"),
                away_score=goals.get("away"),
            ))

        return results

    def _get_week_matches(self, limit: int) -> list[dict]:
        """获取一周比赛"""
        results = []
        for i in range(7):
            date_str = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                response = self.client.get("/fixtures", params={"date": date_str, "league": 39, "season": 2024})
                data = response.json()
                matches = data.get("response", [])
                # 简化处理
                for match in matches[:3]:
                    fixture = match.get("fixture", {})
                    teams = match.get("teams", {})
                    date = fixture.get("date", "")
                    scheduled = ""
                    if date:
                        try:
                            dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                            scheduled = dt.strftime("%m月%d日 %H:%M")
                        except:
                            scheduled = date
                    results.append(MatchSearchResult.from_football(
                        match_id=str(fixture.get("id", "")),
                        name=f"{teams.get('home', {}).get('name', '')} vs {teams.get('away', {}).get('name', '')}",
                        status=fixture.get("status", {}).get("short", "NS"),
                        date=scheduled,
                        league=match.get("league", {}).get("name", "英超"),
                        home_team=teams.get("home", {}).get("name", ""),
                        away_team=teams.get("away", {}).get("name", ""),
                    ))
            except Exception:
                break
        return results[:limit]

    def _get_live_matches(self, limit: int) -> list[dict]:
        """获取实时比赛"""
        try:
            response = self.client.get("/fixtures", params={"live": "all"})
            data = response.json()
            matches = data.get("response", [])[:limit]
            results = []
            for match in matches:
                fixture = match.get("fixture", {})
                teams = match.get("teams", {})
                goals = match.get("goals", {})
                results.append(MatchSearchResult.from_football(
                    match_id=str(fixture.get("id", "")),
                    name=f"{teams.get('home', {}).get('name', '')} vs {teams.get('away', {}).get('name', '')}",
                    status="LIVE",
                    date="进行中",
                    league=match.get("league", {}).get("name", ""),
                    home_team=teams.get("home", {}).get("name", ""),
                    away_team=teams.get("away", {}).get("name", ""),
                    home_score=goals.get("home"),
                    away_score=goals.get("away"),
                ))
            return results
        except Exception:
            return []

    def get_match_detail(self, match_id: str) -> dict:
        """获取比赛详情"""
        try:
            response = self.client.get("/fixtures", params={"id": match_id})
            response.raise_for_status()
            data = response.json()
            matches = data.get("response", [])
            return matches[0] if matches else {"error": "比赛未找到"}
        except Exception as e:
            return {"error": str(e)}

    def get_team_info(self, team_name: str) -> dict:
        """搜索球队信息"""
        try:
            response = self.client.get("/teams", params={"search": team_name})
            response.raise_for_status()
            data = response.json()
            teams = data.get("response", [])
            if teams:
                return {
                    "name": teams[0].get("team", {}).get("name", team_name),
                    "country": teams[0].get("team", {}).get("country", ""),
                    "founded": teams[0].get("team", {}).get("founded", ""),
                    "logo": teams[0].get("team", {}).get("logo", ""),
                }
        except Exception:
            pass
        return {"name": team_name, "info": "暂无详细信息"}

    def _get_demo_data(self, query: str, time_range: str) -> list[dict]:
        """演示数据"""
        demos = [
            MatchSearchResult.from_football(
                match_id="demo_f_001",
                name="利物浦 vs 曼城",
                status="NS",
                date="06月10日 23:00",
                league="英超",
                home_team="利物浦",
                away_team="曼城",
                note="演示数据 - 请配置 FOOTBALL_API_KEY 获取真实数据"
            ),
            MatchSearchResult.from_football(
                match_id="demo_f_002",
                name="皇家马德里 vs 巴塞罗那",
                status="NS",
                date="06月11日 03:00",
                league="西甲",
                home_team="皇家马德里",
                away_team="巴塞罗那",
                note="演示数据 - 请配置 FOOTBALL_API_KEY 获取真实数据"
            ),
            MatchSearchResult.from_football(
                match_id="demo_f_003",
                name="拜仁慕尼黑 vs 多特蒙德",
                status="NS",
                date="06月11日 21:30",
                league="德甲",
                home_team="拜仁慕尼黑",
                away_team="多特蒙德",
                note="演示数据 - 请配置 FOOTBALL_API_KEY 获取真实数据"
            ),
        ]

        if query:
            demos = [d for d in demos if query.lower() in d.get("name", "").lower()]

        return demos
