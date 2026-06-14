"""Analysis 兼容层 - 提供空的技术指标模块"""

from typing import Any, Dict, List, Optional

# IndicatorSpec 类
class IndicatorSpec:
    """技术指标规格（兼容层）"""
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}

# compute_many 函数
def compute_many(specs: List[IndicatorSpec], data: Any) -> Dict[str, Any]:
    """计算多个技术指标（兼容层 - 返回空结果）"""
    return {}
