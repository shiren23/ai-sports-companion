"""数据源客户端"""

from .pandascore import PandaScoreClient
from .football_api import FootballAPIClient
from .base import BaseSportsClient, MatchSearchResult

__all__ = ["PandaScoreClient", "FootballAPIClient", "BaseSportsClient", "MatchSearchResult"]
