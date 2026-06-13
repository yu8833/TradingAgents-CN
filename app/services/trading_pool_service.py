"""
交易池管理服务
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.database import get_mongo_db
from app.models.three_buy_three_sell import TradingPoolEntry, Position, SignalHistory, PoolStatistics
from app.services.three_buy_three_sell_service import ThreeBuyThreeSellService
import logging

logger = logging.getLogger(__name__)


class TradingPoolService:
    """
    交易池管理服务
    
    交易池类型:
    - buy_candidate: 买入候选池 - 具备三买信号的股票
    - holding: 持仓中 - 当前持有的股票
    - watching: 观察池 - 关注但未建仓的股票
    """
    
    def __init__(self):
        self.db = None
        self.signal_service = ThreeBuyThreeSellService()
    
    async def _get_db(self):
        """延迟获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db
    
    async def add_to_pool(
        self,
        stock_code: str,
        pool_type: str,
        entry_signal: str = "manual",
        entry_price: Optional[float] = None,
        quantity: int = 0,
        target_position: str = "1/3",
        notes: str = ""
    ) -> TradingPoolEntry:
        """
        添加股票到交易池
        
        Args:
            stock_code: 股票代码
            pool_type: 池类型: buy_candidate | holding | watching
            entry_signal: 入池信号: B1 | B2 | B3 | manual
            entry_price: 入池价格
            quantity: 持仓数量
            target_position: 目标仓位
            notes: 备注
        
        Returns:
            TradingPoolEntry: 交易池条目
        """
        try:
            db = await self._get_db()
            # 获取股票名称
            collection = db["stock_screening_view"]
            doc = await collection.find_one(
                {"code": {"$in": [stock_code, stock_code.zfill(6)]}},
                projection={"_id": 0, "name": 1}
            )
            stock_name = doc.get("name", stock_code) if doc else stock_code
            
            # 检查是否已存在
            pool_collection = db["trading_pool"]
            existing = await pool_collection.find_one({
                "stock_code": stock_code,
                "status": "active"
            })
            
            if existing:
                # 更新现有记录
                update_data = {
                    "pool_type": pool_type,
                    "entry_signal": entry_signal,
                    "entry_price": entry_price if entry_price else existing.get("entry_price"),
                    "quantity": quantity if quantity > 0 else existing.get("quantity", 0),
                    "target_position": target_position,
                    "notes": notes if notes else existing.get("notes", ""),
                    "updated_at": datetime.now()
                }
                await pool_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_data}
                )
                updated = await pool_collection.find_one({"_id": existing["_id"]})
                return TradingPoolEntry(**updated)
            
            # 创建新记录
            entry = TradingPoolEntry(
                stock_code=stock_code,
                stock_name=stock_name,
                pool_type=pool_type,
                entry_signal=entry_signal,
                entry_price=entry_price,
                quantity=quantity,
                target_position=target_position,
                notes=notes
            )
            
            await pool_collection.insert_one(entry.dict())
            
            logger.info(f"股票 {stock_code} 已添加到 {pool_type} 池")
            return entry
            
        except Exception as e:
            logger.error(f"添加股票 {stock_code} 到交易池失败: {e}", exc_info=True)
            raise
    
    async def remove_from_pool(self, stock_code: str) -> bool:
        """
        从交易池移除股票（软删除）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            bool: 是否成功
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            result = await pool_collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$set": {"status": "removed", "removed_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"股票 {stock_code} 已从交易池移除")
                return True
            return False
            
        except Exception as e:
            logger.error(f"移除股票 {stock_code} 失败: {e}", exc_info=True)
            return False
    
    async def move_to_pool(self, stock_code: str, to_pool: str) -> bool:
        """
        移动股票到另一个池
        
        Args:
            stock_code: 股票代码
            to_pool: 目标池类型
        
        Returns:
            bool: 是否成功
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            result = await pool_collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$set": {"pool_type": to_pool, "updated_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"股票 {stock_code} 已从移动到 {to_pool} 池")
                return True
            return False
            
        except Exception as e:
            logger.error(f"移动股票 {stock_code} 失败: {e}", exc_info=True)
            return False
    
    async def get_pool_stocks(self, pool_type: str = "all") -> List[TradingPoolEntry]:
        """
        获取交易池中的股票
        
        Args:
            pool_type: 池类型: buy_candidate | holding | watching | all
        
        Returns:
            List[TradingPoolEntry]: 交易池条目列表
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            
            query = {"status": "active"}
            if pool_type != "all":
                query["pool_type"] = pool_type
            
            cursor = pool_collection.find(query).sort("entry_date", -1)
            entries = await cursor.to_list(length=1000)
            
            return [TradingPoolEntry(**entry) for entry in entries]
            
        except Exception as e:
            logger.error(f"获取交易池股票失败: {e}", exc_info=True)
            return []
    
    async def get_pool_entry(self, stock_code: str) -> Optional[TradingPoolEntry]:
        """
        获取单只股票的交易池信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Optional[TradingPoolEntry]: 交易池条目
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            entry = await pool_collection.find_one({
                "stock_code": stock_code,
                "status": "active"
            })
            
            if entry:
                return TradingPoolEntry(**entry)
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 交易池信息失败: {e}", exc_info=True)
            return None
    
    async def update_position(self, stock_code: str, quantity: int, avg_cost: float) -> bool:
        """
        更新持仓信息
        
        Args:
            stock_code: 股票代码
            quantity: 持仓数量
            avg_cost: 平均成本
        
        Returns:
            bool: 是否成功
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            result = await pool_collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$set": {
                    "quantity": quantity,
                    "avg_cost": avg_cost,
                    "pool_type": "holding",
                    "updated_at": datetime.now()
                }}
            )
            
            # 更新持仓记录
            positions_collection = db["positions"]
            position = await positions_collection.find_one({"stock_code": stock_code, "status": "holding"})
            
            if position:
                await positions_collection.update_one(
                    {"_id": position["_id"]},
                    {"$set": {"quantity": quantity, "avg_cost": avg_cost, "updated_at": datetime.now()}}
                )
            else:
                position_entry = Position(
                    stock_code=stock_code,
                    stock_name="",
                    quantity=quantity,
                    avg_cost=avg_cost,
                    position_ratio="1/3"
                )
                await positions_collection.insert_one(position_entry.dict())
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}", exc_info=True)
            return False
    
    async def record_signal_action(self, stock_code: str, signal: str, action: str, price: float):
        """
        记录信号触发的操作
        
        Args:
            stock_code: 股票代码
            signal: 信号类型
            action: 采取的操作
            price: 操作价格
        """
        try:
            db = await self._get_db()
            # 更新交易池中的已触发信号
            pool_collection = db["trading_pool"]
            await pool_collection.update_one(
                {"stock_code": stock_code, "status": "active"},
                {"$addToSet": {"signals_triggered": signal}}
            )
            
            # 创建信号历史记录
            history_entry = SignalHistory(
                stock_code=stock_code,
                signal_type=signal,
                signal_name=self._get_signal_name(signal),
                trigger_price=price,
                action_taken=action,
                notification_sent=True
            )
            
            history_collection = db["signal_history"]
            await history_collection.insert_one(history_entry.dict())
            
            logger.info(f"记录信号操作: {stock_code} {signal} -> {action}")
            
        except Exception as e:
            logger.error(f"记录信号操作失败: {e}", exc_info=True)
    
    def _get_signal_name(self, signal: str) -> str:
        """获取信号名称"""
        signal_names = {
            "B1": "左侧买点",
            "B2": "突破买点",
            "B3": "回踩买点",
            "S1": "加速卖点",
            "S2": "跌破卖点",
            "S3": "清仓卖点"
        }
        return signal_names.get(signal, signal)
    
    async def get_pool_statistics(self) -> PoolStatistics:
        """
        获取交易池统计信息
        
        Returns:
            PoolStatistics: 统计信息
        """
        try:
            db = await self._get_db()
            pool_collection = db["trading_pool"]
            
            total_stocks = await pool_collection.count_documents({"status": "active"})
            buy_candidate_count = await pool_collection.count_documents({
                "status": "active",
                "pool_type": "buy_candidate"
            })
            holding_count = await pool_collection.count_documents({
                "status": "active",
                "pool_type": "holding"
            })
            watching_count = await pool_collection.count_documents({
                "status": "active",
                "pool_type": "watching"
            })
            
            # 获取活跃信号数
            history_collection = db["signal_history"]
            active_signals = await history_collection.count_documents({"is_active": True})
            
            return PoolStatistics(
                total_stocks=total_stocks,
                buy_candidate_count=buy_candidate_count,
                holding_count=holding_count,
                watching_count=watching_count,
                active_signals=active_signals
            )
            
        except Exception as e:
            logger.error(f"获取交易池统计失败: {e}", exc_info=True)
            return PoolStatistics()
    
    async def scan_pool_signals(self) -> List[Dict[str, Any]]:
        """
        扫描交易池中所有股票的信号
        
        Returns:
            List[Dict]: 包含信号信息的股票列表
        """
        try:
            pool_stocks = await self.get_pool_stocks()
            results = []
            
            for entry in pool_stocks:
                signal_result = await self.signal_service.calculate_signals(entry.stock_code)
                
                results.append({
                    "stock_code": entry.stock_code,
                    "stock_name": entry.stock_name,
                    "pool_type": entry.pool_type,
                    "current_price": signal_result.current_price,
                    "signals": signal_result.signals,
                    "recommendations": signal_result.recommendations,
                    "position_advice": signal_result.position_advice,
                    "indicators": signal_result.indicators
                })
            
            return results
            
        except Exception as e:
            logger.error(f"扫描交易池信号失败: {e}", exc_info=True)
            return []
