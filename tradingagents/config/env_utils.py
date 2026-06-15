"""环境变量工具。

提供统一的环境变量读取接口，支持类型转换和默认值。
"""

import os
from typing import Any, List, Optional


def parse_bool_env(key: str, default: bool = False) -> bool:
    """解析布尔环境变量。

    支持值: true/false, yes/no, 1/0, on/off (大小写不敏感)。
    """
    value = os.getenv(key)
    if value is None:
        return default
    value = str(value).strip().lower()
    if value in ("true", "yes", "1", "on"):
        return True
    if value in ("false", "no", "0", "off", ""):
        return False
    return default


def parse_int_env(key: str, default: int = 0) -> int:
    """解析整数环境变量。"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default


def parse_float_env(key: str, default: float = 0.0) -> float:
    """解析浮点环境变量。"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


def parse_list_env(key: str, default: Optional[List[str]] = None, sep: str = ",") -> List[str]:
    """解析列表环境变量（按逗号或自定义分隔符拆分）。"""
    if default is None:
        default = []
    value = os.getenv(key)
    if value is None or value == "":
        return list(default)
    return [s.strip() for s in value.split(sep) if s.strip()]


def parse_env(key: str, default: Any = None) -> str:
    """通用字符串环境变量读取。"""
    return os.getenv(key, default)


__all__ = [
    "parse_bool_env",
    "parse_int_env",
    "parse_float_env",
    "parse_list_env",
    "parse_env",
]
