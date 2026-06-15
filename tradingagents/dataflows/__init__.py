"""tradingagents.dataflows 公共入口。

统一的数据源访问入口。功能模块通过子模块路径导入:
  - tradingagents.dataflows.a_stock   A 股 (东方财富/腾讯/新浪)
  - tradingagents.dataflows.y_finance 美股 (yfinance)
  - tradingagents.dataflows.cache     内存缓存
  - tradingagents.dataflows.news      实时新闻聚合
  - tradingagents.dataflows.providers 各市场 provider
  - tradingagents.dataflows.config    配置/数据源状态

注意: 本文件不依赖任何第三方包，保证 import 始终成功。
"""

from tradingagents.dataflows.config import (
    get_config,
    initialize_config,
    set_config,
)
from tradingagents.dataflows.utils import (
    get_current_date,
    get_next_weekday,
    safe_ticker_component,
)

__all__ = [
    "get_config",
    "initialize_config",
    "set_config",
    "safe_ticker_component",
    "get_current_date",
    "get_next_weekday",
]
