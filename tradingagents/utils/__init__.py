"""tradingagents.utils 公共入口。

导出
----
StockUtils          股票代码工具类
init_logging        日志初始化（带默认 StreamHandler）
setup_logging       setup_logging(...) = init_logging(...) 别名
get_logger          获取 logging.Logger
prepare_stock_data_async   异步数据准备（兼容层）
get_trading_date_range     获取日期范围
"""

from tradingagents.utils.logging_init import get_logger, init_logging
from tradingagents.utils.stock_utils import StockUtils
from tradingagents.utils.stock_validator import prepare_stock_data_async
from tradingagents.utils.dataflow_utils import get_trading_date_range


def setup_logging(*args, **kwargs):
    """init_logging 的别名，保持 API 兼容性。"""
    return init_logging(*args, **kwargs)


__all__ = [
    "StockUtils",
    "init_logging",
    "setup_logging",
    "get_logger",
    "prepare_stock_data_async",
    "get_trading_date_range",
]
