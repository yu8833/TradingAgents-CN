"""数据库管理（兼容层）。

为旧代码提供 `get_database_manager()` 和 `get_mongodb_client()` 接口。
当 pymongo 未安装或 MongoDB 不可用时，返回空实现但不崩溃。
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class _DatabaseManager:
    """简化的数据库管理器。"""

    def __init__(self):
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None

    def _init_connection(self) -> Optional[Any]:
        """懒加载 MongoDB 连接。"""
        try:
            from pymongo import MongoClient
        except ImportError:
            logger.debug("pymongo 未安装，跳过 MongoDB 连接")
            return None

        try:
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.getenv("MONGODB_DB", "tradingagentscn")
            self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[db_name]
            self._client.admin.command("ping")
            logger.info("数据库管理器已连接: %s/%s", uri, db_name)
            return self._db
        except Exception as exc:
            logger.warning("数据库连接失败: %s", exc)
            return None

    def get_database(self) -> Optional[Any]:
        if self._db is None:
            self._init_connection()
        return self._db

    def get_client(self) -> Optional[Any]:
        if self._client is None:
            self._init_connection()
        return self._client

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._db = None


_db_manager = _DatabaseManager()


def get_database_manager() -> _DatabaseManager:
    """获取全局数据库管理器。"""
    return _db_manager


def get_mongodb_client() -> Optional[Any]:
    """获取 MongoDB 客户端（无依赖时返回 None）。"""
    try:
        from pymongo import MongoClient
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        return MongoClient(uri, serverSelectionTimeoutMS=5000)
    except ImportError:
        logger.debug("pymongo 未安装，跳过 MongoDB 客户端创建")
        return None
    except Exception as exc:
        logger.warning("MongoDB 客户端创建失败: %s", exc)
        return None


def get_mongodb_database() -> Optional[Any]:
    """获取 MongoDB 数据库对象。"""
    mgr = get_database_manager()
    return mgr.get_database() if mgr else None


__all__ = [
    "get_database_manager",
    "get_mongodb_client",
    "get_mongodb_database",
]
