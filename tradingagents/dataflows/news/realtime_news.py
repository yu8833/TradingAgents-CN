"""实时新闻聚合器（兼容层）"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RealtimeNewsAggregator:
    """实时新闻聚合器（兼容层 - 空实现）"""

    def __init__(self, *args, **kwargs):
        pass

    def get_news(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """获取新闻（兼容层 - 返回空列表）"""
        return []

    def aggregate(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """聚合新闻（兼容层 - 返回空列表）"""
        return []


def get_news_aggregator(*args, **kwargs) -> RealtimeNewsAggregator:
    """获取新闻聚合器实例（兼容层）"""
    return RealtimeNewsAggregator()
