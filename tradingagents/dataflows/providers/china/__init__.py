"""Provider 兼容层 - 提供空的 Provider 类让依赖此模块的代码可以导入"""

class ChinaDataProvider:
    """中国数据 Provider 基类（兼容层）"""
    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None


class TushareProvider(ChinaDataProvider):
    """Tushare Provider（兼容层）"""
    pass


class BaostockProvider(ChinaDataProvider):
    """Baostock Provider（兼容层）"""
    pass


class AkshareProvider(ChinaDataProvider):
    """Akshare Provider（兼容层）"""
    pass
