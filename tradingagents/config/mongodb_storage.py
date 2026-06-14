"""mongodb_storage 兼容层
提供 MongoDBStorage 类的简化实现，供旧代码使用

新 tradingagents 模块中此功能由具体应用层管理
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MongoDBStorage:
    """简化的 MongoDB 存储适配器（兼容层）

    只提供最小可用的接口，不做实际的复杂存储操作
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "tradingagentscn",
        *args,
        **kwargs
    ):
        self.connection_string = connection_string
        self.database_name = database_name
        self._client = None
        self._db = None
        self._connected = False

        self._try_connect()

    def _try_connect(self) -> bool:
        """尝试连接 MongoDB"""
        if not self.connection_string:
            logger.debug("MongoDBStorage: 未提供连接字符串，跳过连接")
            return False

        try:
            import pymongo
            self._client = pymongo.MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
            # 测试连接
            self._client.admin.command("ping")
            self._db = self._client[self.database_name]
            self._connected = True
            logger.info(f"MongoDBStorage: 成功连接到 {self.database_name}")
            return True
        except Exception as e:
            logger.warning(f"MongoDBStorage: 连接失败: {e}")
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def save(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """保存数据到指定集合"""
        if not self._connected or self._db is None:
            return False
        try:
            self._db[collection].update_one(
                {"_id": doc_id},
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.warning(f"MongoDBStorage.save 失败: {e}")
            return False

    def load(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """从指定集合加载数据"""
        if not self._connected or self._db is None:
            return None
        try:
            return self._db[collection].find_one({"_id": doc_id})
        except Exception as e:
            logger.warning(f"MongoDBStorage.load 失败: {e}")
            return None

    def close(self):
        """关闭连接"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
        self._connected = False
