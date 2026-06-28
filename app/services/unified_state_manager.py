"""
统一状态管理器
实现以 Redis 为准的状态存储策略
- Redis: 主状态存储（实时状态）
- MongoDB: 持久化存储（历史记录）
"""

import asyncio
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)


class UnifiedStateManager:
    """
    统一状态管理器

    设计原则:
    - Redis 作为主状态存储，所有实时状态读写都通过 Redis
    - MongoDB 作为持久化存储，定时同步或状态变更时异步同步
    - Memory 作为缓存层，提供最快的读取速度
    """

    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        self._redis_client = None
        self._mongo_client = None
        self._sync_enabled = False
        self._last_sync: Dict[str, datetime] = {}

        # 初始化连接
        self._init_redis()
        self._init_mongo()

    def _init_redis(self) -> bool:
        """初始化 Redis 连接"""
        try:
            redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
            if not redis_enabled:
                logger.info("📊 [统一状态] Redis未启用，使用内存存储")
                return False

            import redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            redis_db = int(os.getenv('REDIS_DB', 0))

            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True
            )
            self._redis_client.ping()
            logger.info("✅ [统一状态] Redis连接成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ [统一状态] Redis连接失败: {e}")
            return False

    def _init_mongo(self) -> bool:
        """初始化 MongoDB 连接"""
        try:
            from pymongo import MongoClient
            from app.core.config import settings

            self._mongo_client = MongoClient(
                settings.MONGO_URI,
                maxPoolSize=5,
                minPoolSize=1
            )
            # 测试连接
            self._mongo_client[settings.MONGO_DB].command('ping')
            self._sync_enabled = True
            logger.info("✅ [统一状态] MongoDB连接成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ [统一状态] MongoDB连接失败: {e}")
            return False

    def _get_redis_key(self, task_id: str) -> str:
        """生成 Redis 键"""
        return f"analysis:task:{task_id}:status"

    def _get_cache_key(self, task_id: str) -> str:
        """生成缓存键"""
        return f"cache:{task_id}"

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
        current_step: str = "",
        result_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 任务状态 (pending/running/completed/failed)
            progress: 进度 (0-100)
            message: 状态消息
            current_step: 当前步骤
            result_data: 结果数据
            error_message: 错误消息

        Returns:
            更新是否成功
        """
        try:
            # 构建状态数据
            state_data = {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "current_step": current_step,
                "updated_at": datetime.utcnow().isoformat()
            }

            if result_data:
                state_data["result_data"] = result_data
            if error_message:
                state_data["error_message"] = error_message
            if status == "completed":
                state_data["completed_at"] = datetime.utcnow().isoformat()
            if status == "failed":
                state_data["failed_at"] = datetime.utcnow().isoformat()

            # 1. 更新内存缓存（最快）
            with self._cache_lock:
                self._memory_cache[task_id] = state_data

            # 2. 更新 Redis（主存储）
            if self._redis_client:
                try:
                    redis_key = self._get_redis_key(task_id)
                    self._redis_client.set(
                        redis_key,
                        json.dumps(state_data),
                        ex=3600  # 1小时过期
                    )
                except Exception as redis_error:
                    logger.warning(f"⚠️ Redis更新失败: {redis_error}")

            # 3. 异步更新 MongoDB（持久化）
            if self._sync_enabled and self._mongo_client:
                asyncio.create_task(self._sync_to_mongo(task_id, state_data))

            logger.debug(f"📊 状态已更新: {task_id} -> {status} ({progress}%)")
            return True

        except Exception as e:
            logger.error(f"❌ 状态更新失败: {e}")
            return False

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        优先级: 内存缓存 > Redis > MongoDB

        Args:
            task_id: 任务ID

        Returns:
            任务状态数据
        """
        try:
            # 1. 先检查内存缓存
            with self._cache_lock:
                if task_id in self._memory_cache:
                    return self._memory_cache[task_id].copy()

            # 2. 尝试从 Redis 读取
            if self._redis_client:
                try:
                    redis_key = self._get_redis_key(task_id)
                    data = self._redis_client.get(redis_key)
                    if data:
                        state_data = json.loads(data)
                        # 回填内存缓存
                        with self._cache_lock:
                            self._memory_cache[task_id] = state_data
                        return state_data
                except Exception as redis_error:
                    logger.warning(f"⚠️ Redis读取失败: {redis_error}")

            # 3. 最后从 MongoDB 读取
            if self._mongo_client:
                return await self._get_from_mongo(task_id)

            return None

        except Exception as e:
            logger.error(f"❌ 获取状态失败: {e}")
            return None

    async def _sync_to_mongo(self, task_id: str, state_data: Dict[str, Any]):
        """异步同步到 MongoDB"""
        try:
            if not self._mongo_client:
                return

            from app.core.config import settings
            db = self._mongo_client[settings.MONGO_DB]

            db.analysis_tasks.update_one(
                {"task_id": task_id},
                {"$set": state_data},
                upsert=True
            )

            self._last_sync[task_id] = datetime.utcnow()
            logger.debug(f"📊 已同步到MongoDB: {task_id}")

        except Exception as e:
            logger.warning(f"⚠️ MongoDB同步失败: {e}")

    async def _get_from_mongo(self, task_id: str) -> Optional[Dict[str, Any]]:
        """从 MongoDB 读取"""
        try:
            if not self._mongo_client:
                return None

            from app.core.config import settings
            db = self._mongo_client[settings.MONGO_DB]

            task = db.analysis_tasks.find_one({"task_id": task_id})
            if task:
                # 移除 MongoDB 的 _id 字段
                task.pop('_id', None)
                return task

            return None

        except Exception as e:
            logger.warning(f"⚠️ MongoDB读取失败: {e}")
            return None

    def clear_cache(self, task_id: str):
        """清除内存缓存"""
        with self._cache_lock:
            self._memory_cache.pop(task_id, None)

    def close(self):
        """关闭连接"""
        if self._redis_client:
            self._redis_client.close()
        if self._mongo_client:
            self._mongo_client.close()


# 全局实例
_unified_state_manager: Optional[UnifiedStateManager] = None
_manager_lock = threading.Lock()


def get_unified_state_manager() -> UnifiedStateManager:
    """获取统一状态管理器实例"""
    global _unified_state_manager
    with _manager_lock:
        if _unified_state_manager is None:
            _unified_state_manager = UnifiedStateManager()
        return _unified_state_manager
