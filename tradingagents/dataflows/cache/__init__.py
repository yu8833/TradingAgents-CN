"""缓存模块（兼容层）"""

from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta


class CacheProvider:
    """缓存 Provider（兼容层 - 完整实现）"""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._hit_count: Dict[str, int] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            self._hit_count[key] = self._hit_count.get(key, 0) + 1
            item = self._store[key]
            # 检查是否过期
            expire_at = item.get('expire_at')
            if expire_at and expire_at < datetime.now():
                del self._store[key]
                return None
            return item.get('value')
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        item = {
            'value': value,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'expire_at': datetime.now() + timedelta(seconds=ttl) if ttl else None,
            'type': self._detect_type(key, value),
            'size': len(str(value))
        }
        self._store[key] = item

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def exists(self, key: str) -> bool:
        return key in self._store

    def _detect_type(self, key: str, value: Any) -> str:
        """检测缓存项类型"""
        key_lower = key.lower()
        if 'stock' in key_lower or 'quote' in key_lower or 'price' in key_lower or 'kline' in key_lower:
            return 'stock_data'
        elif 'news' in key_lower or 'announcement' in key_lower:
            return 'news_data'
        elif 'fundamental' in key_lower or 'financial' in key_lower or 'f10' in key_lower:
            return 'fundamental_data'
        elif 'analysis' in key_lower or 'report' in key_lower:
            return 'analysis_data'
        return 'other'

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_files = len(self._store)
        total_size = sum(item.get('size', 0) for item in self._store.values())
        stock_data_count = sum(1 for item in self._store.values() if item.get('type') == 'stock_data')
        news_count = sum(1 for item in self._store.values() if item.get('type') == 'news_data')
        fundamentals_count = sum(1 for item in self._store.values() if item.get('type') == 'fundamental_data')

        return {
            'total_files': total_files,
            'total_size': total_size,
            'stock_data_count': stock_data_count,
            'news_count': news_count,
            'fundamentals_count': fundamentals_count
        }

    def clear_old_cache(self, days: int = 7) -> int:
        """清理过期缓存"""
        if days == 0:
            # 清空所有
            count = len(self._store)
            self._store.clear()
            return count
        cutoff = datetime.now() - timedelta(days=days)
        expired_keys = [
            k for k, v in self._store.items()
            if v.get('created_at') < cutoff
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)

    def get_cache_details(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取缓存详情列表"""
        items: List[Dict[str, Any]] = []
        for key, value in self._store.items():
            symbol = self._extract_symbol(key)
            items.append({
                'type': value.get('type', 'other'),
                'symbol': symbol,
                'size': value.get('size', 0),
                'created_at': value.get('created_at', datetime.now()).isoformat(),
                'last_accessed': value.get('last_accessed', datetime.now()).isoformat(),
                'hit_count': self._hit_count.get(key, 0)
            })

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]

        return {
            'items': paginated_items,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def get_cache_backend_info(self) -> Dict[str, Any]:
        """获取缓存后端信息"""
        return {
            'system': 'memory',
            'primary_backend': 'memory',
            'fallback_enabled': False,
            'mongodb_available': True,
            'redis_available': False
        }

    def _extract_symbol(self, key: str) -> str:
        """从 key 中提取股票代码"""
        parts = key.split(':')
        if len(parts) > 1:
            return parts[-1]
        return key


_cache_instance: Optional[CacheProvider] = None


def get_cache(*args, **kwargs) -> CacheProvider:
    """获取缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheProvider()
    return _cache_instance
