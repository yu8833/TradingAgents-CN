"""香港股票 Provider（兼容层）"""


class HKStockProvider:
    """HKStockProvider（兼容层 - 空实现）"""

    def __init__(self, *args, **kwargs):
        pass

    def get_data(self, *args, **kwargs):
        return None

    def get_stock_list(self, *args, **kwargs):
        return []

    def get_quote(self, *args, **kwargs):
        return None
