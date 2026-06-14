"""优化版中国股票数据（兼容层）"""

_force_refresh_global: bool = False


def set_force_refresh_global(value: bool) -> None:
    """设置全局强制刷新标志（兼容层）"""
    global _force_refresh_global
    _force_refresh_global = value


def get_force_refresh_global() -> bool:
    """获取全局强制刷新标志（兼容层）"""
    return _force_refresh_global
