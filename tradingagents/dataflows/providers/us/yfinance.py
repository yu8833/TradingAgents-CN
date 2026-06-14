"""美国股票数据 Provider 兼容层"""


class YFinanceUtils:
    """YFinance 工具类（兼容层 - 空实现）"""

    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None

    @staticmethod
    def get_stock_info(*args, **kwargs):
        return None

    @staticmethod
    def get_historical_data(*args, **kwargs):
        return None

    @staticmethod
    def get_quote(*args, **kwargs):
        return None
