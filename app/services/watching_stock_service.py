"""
自选股管理服务
管理用户的自选股，支持实时监控
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.database import get_mongo_db
from app.models.three_buy_three_sell import WatchingStock
import logging

logger = logging.getLogger(__name__)


class WatchingStockService:
    """
    自选股管理服务
    
    功能:
    - 添加股票到自选股
    - 从自选股移除股票
    - 获取自选股列表
    - 记录自选股的信号状态
    """
    
    def __init__(self):
        self.db = None
        self.collection_name = "watching_stocks"
    
    async def _get_db(self):
        """延迟获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db
    
    async def _get_collection(self):
        """获取自选股集合"""
        db = await self._get_db()
        collection = db[self.collection_name]
        
        # 确保索引存在
        await collection.create_index([("stock_code", 1)], unique=True)
        await collection.create_index([("status", 1)])
        await collection.create_index([("added_date", -1)])
        
        return collection
    
    async def add_stock(
        self,
        stock_code: str,
        stock_name: str,
        added_signal: str = "manual",
        entry_price: Optional[float] = None,
        notes: str = ""
    ) -> WatchingStock:
        """
        添加股票到自选股
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            added_signal: 加入时的信号
            entry_price: 加入时的价格
            notes: 备注
        
        Returns:
            WatchingStock: 自选股条目
        """
        try:
            collection = await self._get_collection()
            
            # 检查是否已存在
            existing = await collection.find_one({"stock_code": stock_code, "status": "active"})
            if existing:
                logger.info(f"股票 {stock_code} 已在自选股中")
                return WatchingStock(**existing)
            
            # 创建新条目
            watching = WatchingStock(
                stock_code=stock_code,
                stock_name=stock_name,
                added_date=datetime.now(),
                added_signal=added_signal,
                entry_price=entry_price,
                status="active",
                notes=notes,
                created_at=datetime.now()
            )
            
            await collection.insert_one(watching.model_dump())
            logger.info(f"股票 {stock_code} 已添加到自选股")
            
            return watching
            
        except Exception as e:
            logger.error(f"添加自选股失败: {e}", exc_info=True)
            raise
    
    async def remove_stock(self, stock_code: str) -> bool:
        """
        从自选股移除股票
        
        Args:
            stock_code: 股票代码
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$set": {"status": "removed", "removed_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"股票 {stock_code} 已从自选股移除")
                return True
            else:
                logger.warning(f"股票 {stock_code} 不在自选股中")
                return False
                
        except Exception as e:
            logger.error(f"移除自选股失败: {e}", exc_info=True)
            return False
    
    async def get_watching_stocks(self, include_removed: bool = False) -> List[WatchingStock]:
        """
        获取自选股列表
        
        Args:
            include_removed: 是否包含已移除的
        
        Returns:
            List[WatchingStock]: 自选股列表
        """
        try:
            collection = await self._get_collection()
            
            query = {} if include_removed else {"status": "active"}
            cursor = collection.find(query).sort("added_date", -1)
            
            stocks = await cursor.to_list(length=1000)
            return [WatchingStock(**s) for s in stocks]
            
        except Exception as e:
            logger.error(f"获取自选股列表失败: {e}", exc_info=True)
            return []
    
    async def get_stock(self, stock_code: str) -> Optional[WatchingStock]:
        """
        获取单个自选股信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Optional[WatchingStock]: 自选股信息
        """
        try:
            collection = await self._get_collection()
            stock = await collection.find_one({"stock_code": stock_code, "status": "active"})
            
            if stock:
                return WatchingStock(**stock)
            return None
            
        except Exception as e:
            logger.error(f"获取自选股信息失败: {e}", exc_info=True)
            return None
    
    async def is_in_watching(self, stock_code: str) -> bool:
        """
        检查股票是否在自选股中
        
        Args:
            stock_code: 股票代码
        
        Returns:
            bool: 是否在自选股中
        """
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({"stock_code": stock_code, "status": "active"})
            return count > 0
            
        except Exception as e:
            logger.error(f"检查自选股失败: {e}", exc_info=True)
            return False
    
    async def get_watching_count(self) -> int:
        """
        获取自选股数量
        
        Returns:
            int: 自选股数量
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"status": "active"})
            
        except Exception as e:
            logger.error(f"获取自选股数量失败: {e}", exc_info=True)
            return 0
    
    async def update_notes(self, stock_code: str, notes: str) -> bool:
        """
        更新自选股备注
        
        Args:
            stock_code: 股票代码
            notes: 备注内容
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = await self._get_collection()
            result = await collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$set": {"notes": notes, "updated_at": datetime.now()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新自选股备注失败: {e}", exc_info=True)
            return False
