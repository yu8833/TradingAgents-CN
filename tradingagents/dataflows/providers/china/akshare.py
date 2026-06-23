"""兼容层: AKShare 数据源占位"""
import logging

logger = logging.getLogger(__name__)


class AkshareProvider:
    """AKShare 数据源占位（兼容层）"""

    def __init__(self, *args, **kwargs):
        logger.warning("⚠️ [AkshareProvider] 已迁移到 a_stock.py，本占位类仅用于 import 兼容")

    def get_stock_basic(self, *args, **kwargs):
        return []

    def get_daily(self, *args, **kwargs):
        return []

    def get_financial(self, *args, **kwargs):
        return {}

    def get_news(self, *args, **kwargs):
        return []


_default_akshare = None


def get_akshare_provider(*args, **kwargs):
    """获取 AkshareProvider 单例（占位）"""
    global _default_akshare
    if _default_akshare is None:
        _default_akshare = AkshareProvider(*args, **kwargs)
    return _default_akshare
