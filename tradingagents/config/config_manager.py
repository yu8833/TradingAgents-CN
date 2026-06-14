"""config_manager 兼容层
提供简单的全局配置管理对象，供旧代码使用

新 tradingagents 模块中此功能由具体应用层管理
"""

from typing import Any, Dict, Optional


class ConfigManager:
    """简单的配置管理器（兼容层）"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self.mongodb_storage = None
        self._initialized = False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config[key] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置"""
        self._config.update(config_dict)


# 全局单例
config_manager = ConfigManager()
