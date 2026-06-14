"""Baostock Provider 兼容层"""

def get_baostock_provider(*args, **kwargs):
    """获取Baostock提供者（兼容层 - 返回空对象）"""
    return BaoStockProvider()

class BaoStockProvider:
    """Baostock数据提供者（兼容层 - 空实现）"""
    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None
