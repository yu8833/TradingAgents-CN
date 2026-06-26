"""
分析结果缓存管理器
缓存相同股票的分析结果，避免重复分析
"""

import threading
import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    result: Any
    stock_code: str
    mode: str
    analysis_date: str
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0

    def is_expired(self, ttl_seconds: int) -> bool:
        """检查是否过期"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl_seconds

    def touch(self):
        """刷新访问时间"""
        self.created_at = datetime.now()
        self.hit_count += 1


class AnalysisResultCache:
    """
    分析结果缓存管理器

    设计原则:
    - 基于股票代码+分析日期+模式生成缓存键
    - 缓存有效期可配置（默认5分钟）
    - 最多缓存 N 个结果，超出时清理最旧的结果
    - 线程安全
    """

    def __init__(
        self,
        max_entries: int = 100,
        ttl_seconds: int = 300,  # 5分钟
        cleanup_interval_seconds: int = 60
    ):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._last_cleanup = time.time()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

        logger.info(
            f"📊 [结果缓存] 初始化完成: "
            f"max_entries={max_entries}, "
            f"ttl={ttl_seconds}s"
        )

    def _generate_key(
        self,
        stock_code: str,
        mode: str,
        analysis_date: str,
        analysts: Optional[list] = None
    ) -> str:
        """生成缓存键"""
        # 标准化股票代码
        stock_code = stock_code.upper().strip()

        # 如果有分析师列表，进行排序以确保一致性
        analyst_key = ""
        if analysts:
            analyst_key = "|".join(sorted(analysts))

        key_parts = [stock_code, mode, analysis_date, analyst_key]
        key_string = "|".join(key_parts)

        return hashlib.md5(key_string.encode()).hexdigest()

    def get(
        self,
        stock_code: str,
        mode: str,
        analysis_date: str,
        analysts: Optional[list] = None
    ) -> Optional[Any]:
        """
        获取缓存的分析结果

        Args:
            stock_code: 股票代码
            mode: 分析模式 (quick/deep)
            analysis_date: 分析日期
            analysts: 分析师列表

        Returns:
            缓存的分析结果，如果没有或已过期则返回 None
        """
        key = self._generate_key(stock_code, mode, analysis_date, analysts)

        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                logger.debug(f"📊 [结果缓存] 未命中: {stock_code} ({mode})")
                return None

            entry = self._cache[key]

            # 检查是否过期
            if entry.is_expired(self._ttl_seconds):
                del self._cache[key]
                self._stats["misses"] += 1
                logger.info(f"📊 [结果缓存] 已过期: {stock_code} ({mode})")
                return None

            # 刷新访问时间
            entry.touch()
            self._stats["hits"] += 1
            logger.info(
                f"📊 [结果缓存] 命中: {stock_code} ({mode}), "
                f"命中次数: {entry.hit_count}"
            )

            return entry.result

    def put(
        self,
        stock_code: str,
        mode: str,
        analysis_date: str,
        result: Any,
        analysts: Optional[list] = None
    ) -> str:
        """
        缓存分析结果

        Args:
            stock_code: 股票代码
            mode: 分析模式
            analysis_date: 分析日期
            result: 分析结果
            analysts: 分析师列表

        Returns:
            缓存键
        """
        key = self._generate_key(stock_code, mode, analysis_date, analysts)

        with self._lock:
            # 检查是否需要清理
            self._maybe_cleanup()

            # 添加或更新缓存
            self._cache[key] = CacheEntry(
                result=result,
                stock_code=stock_code,
                mode=mode,
                analysis_date=analysis_date
            )

            logger.info(
                f"📊 [结果缓存] 保存: {stock_code} ({mode}), "
                f"当前缓存数: {len(self._cache)}"
            )

        return key

    def invalidate(
        self,
        stock_code: str,
        mode: Optional[str] = None
    ) -> int:
        """
        使缓存失效

        Args:
            stock_code: 股票代码
            mode: 分析模式，如果为 None 则使所有模式的缓存失效

        Returns:
            失效的缓存数量
        """
        count = 0
        stock_code = stock_code.upper().strip()

        with self._lock:
            keys_to_remove = []

            for key, entry in self._cache.items():
                if entry.stock_code == stock_code:
                    if mode is None or entry.mode == mode:
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]
                count += 1

            if count > 0:
                logger.info(
                    f"📊 [结果缓存] 失效: {stock_code} ({mode or 'all'}), "
                    f"失效数量: {count}"
                )

        return count

    def _maybe_cleanup(self):
        """检查并清理过期缓存"""
        now = time.time()

        # 检查是否需要执行清理
        if now - self._last_cleanup < self._ttl_seconds / 2:
            return

        # 清理过期缓存
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self._ttl_seconds)
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats["evictions"] += 1

        if expired_keys:
            logger.info(f"📊 [结果缓存] 清理过期缓存: {len(expired_keys)} 个")

        # 如果缓存数量超限，清理最旧的
        while len(self._cache) > self._max_entries:
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at
            )
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

            logger.info(f"📊 [结果缓存] 清理最旧缓存，缓存数超限")

        self._last_cleanup = now

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"📊 [结果缓存] 清空缓存: {count} 个结果")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total if total > 0 else 0
            )

            return {
                "count": len(self._cache),
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl_seconds,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": f"{hit_rate:.2%}",
            }


# 全局缓存实例
_analysis_result_cache: Optional[AnalysisResultCache] = None
_cache_lock = threading.Lock()


def get_analysis_result_cache() -> AnalysisResultCache:
    """获取全局分析结果缓存实例"""
    global _analysis_result_cache
    with _cache_lock:
        if _analysis_result_cache is None:
            _analysis_result_cache = AnalysisResultCache(
                max_entries=100,
                ttl_seconds=300,  # 5分钟
                cleanup_interval_seconds=60
            )
        return _analysis_result_cache
