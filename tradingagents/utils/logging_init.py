"""日志初始化工具（兼容层）"""

import logging
import sys


def init_logging(log_level: str = "INFO", *args, **kwargs):
    """初始化日志（兼容层）"""
    level = getattr(logging, str(log_level).upper(), logging.INFO)
    root = logging.getLogger()
    if not any(
        isinstance(h, logging.StreamHandler) for h in root.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        root.addHandler(handler)
    root.setLevel(level)
    return logging.getLogger("tradingagents")


def get_logger(name: str = "tradingagents"):
    """获取日志器（兼容层）"""
    return logging.getLogger(name)
