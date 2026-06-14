"""MongoDB 缓存适配器（兼容层）"""

from typing import Any, Optional


class MongoDBMemoryCache:
    """基于内存的 MongoDB 风格缓存（兼容层）"""

    def __init__(self):
        self._store: dict = {}

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]


_cache_adapter_instance: Optional[MongoDBMemoryCache] = None


def get_mongodb_cache_adapter(*args, **kwargs) -> MongoDBMemoryCache:
    """获取 MongoDB 缓存适配器（兼容层）"""
    global _cache_adapter_instance
    if _cache_adapter_instance is None:
        _cache_adapter_instance = MongoDBMemoryCache()
    return _cache_adapter_instance
