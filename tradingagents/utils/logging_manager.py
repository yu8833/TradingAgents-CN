"""日志管理工具（兼容层）"""

import logging


def get_logger(name: str = "tradingagents"):
    """获取日志器（兼容层）"""
    return logging.getLogger(name)
