"""兼容层: Tushare 数据源占位"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TushareProvider:
    """Tushare 数据源占位（兼容层）"""

    def __init__(self, *args, **kwargs):
        self.token = kwargs.get("token") or ""
        logger.warning("⚠️ [TushareProvider] 已迁移到 a_stock.py，本占位类仅用于 import 兼容")

    def get_stock_basic(self, *args, **kwargs):
        return []

    def get_daily(self, *args, **kwargs):
        return []

    def get_financial(self, *args, **kwargs):
        return {}

    def get_company_info(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            from tradingagents.dataflows.a_stock import resolve_ticker
            return resolve_ticker(code)
        except Exception:
            return None


_default_tushare = None


def get_tushare_provider(*args, **kwargs):
    """获取 TushareProvider 单例（占位）"""
    global _default_tushare
    if _default_tushare is None:
        _default_tushare = TushareProvider(*args, **kwargs)
    return _default_tushare
