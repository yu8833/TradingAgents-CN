"""DataSourceManager 兼容层

这个模块在新的 tradingagents 中不存在，提供空实现让依赖此模块的代码可以导入。
"""

class DataSourceManager:
    """数据源管理器（兼容层 - 空实现）"""
    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None


def get_data_source_manager():
    """获取数据源管理器（兼容层 - 返回 None）"""
    return None
