"""股票工具类（兼容层）"""

from typing import Any, Optional


class StockUtils:
    """股票工具类（兼容层 - 空实现）"""

    @staticmethod
    def format_symbol(symbol: str) -> str:
        """格式化股票代码（兼容层）"""
        return str(symbol).strip().upper()

    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """验证股票代码是否有效（兼容层）"""
        return bool(symbol and len(str(symbol).strip()) > 0)

    @staticmethod
    def get_market_from_symbol(symbol: str) -> Optional[str]:
        """从股票代码推断市场类型（兼容层）"""
        if not symbol:
            return None
        s = str(symbol).upper().strip()
        if s.startswith("HK") or s.startswith("0"):
            return "HK"
        if any(s.startswith(c) for c in ["A", "B", "N"]):
            return "US"
        return "A"

    @staticmethod
    def get_stock_info(*args, **kwargs) -> Optional[Any]:
        """获取股票信息（兼容层 - 返回 None）"""
        return None

    @staticmethod
    def get_market_cap(*args, **kwargs) -> Optional[Any]:
        """获取市值（兼容层 - 返回 None）"""
        return None
