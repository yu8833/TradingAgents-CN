"""香港股票数据 Provider 兼容层"""


class HKStockProvider:
    """HK股票数据 Provider（兼容层 - 空实现）"""

    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None


def get_hk_stock_provider(*args, **kwargs):
    """获取HK股票 Provider（兼容层）"""
    return HKStockProvider()
