"""Alpha Vantage 通用工具（兼容层）"""

from typing import Optional


def get_api_key(*args, **kwargs) -> Optional[str]:
    """获取 Alpha Vantage API Key（兼容层 - 返回 None）"""
    import os
    return os.environ.get("ALPHA_VANTAGE_API_KEY")


def _make_api_request(*args, **kwargs):
    """发起 API 请求（兼容层 - 返回 None）"""
    return None
