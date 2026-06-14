"""数据流工具（兼容层）"""

from typing import Optional, Tuple
from datetime import datetime, timedelta


def get_trading_date_range(
    end_date: Optional[str] = None,
    days: int = 90,
    *args,
    **kwargs
) -> Tuple[Optional[str], Optional[str]]:
    """获取交易日期范围（兼容层）"""
    if end_date:
        try:
            end = datetime.strptime(str(end_date), "%Y-%m-%d")
        except Exception:
            end = datetime.now()
    else:
        end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
