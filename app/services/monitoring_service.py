"""
实时监控服务
定时扫描自选股内股票的信号变化
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.database import get_mongo_db
from app.services.three_buy_three_sell_service import ThreeBuyThreeSellService
from app.services.watching_stock_service import WatchingStockService
from app.models.three_buy_three_sell import SignalAlert
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    实时监控服务
    
    功能:
    - 定时扫描自选股内的股票
    - 检测新的三买三卖信号
    - 发送通知提醒
    """
    
    def __init__(self):
        self.db = None
        self.signal_service = ThreeBuyThreeSellService()
        self.watching_service = WatchingStockService()
        self.is_running = False
        self.last_checked_signals: Dict[str, List[str]] = {}
        self.notification_queue: List[SignalAlert] = []
    
    async def _get_db(self):
        """延迟获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db
        
    async def start_monitoring(self, interval_minutes: int = 5):
        """
        启动监控任务
        
        Args:
            interval_minutes: 扫描间隔（分钟）
        """
        if self.is_running:
            logger.warning("监控服务已在运行中")
            return
        
        self.is_running = True
        logger.info(f"监控服务已启动，扫描间隔: {interval_minutes}分钟")
        
        while self.is_running:
            try:
                await self._scan_all_stocks()
            except Exception as e:
                logger.error(f"监控扫描异常: {e}", exc_info=True)
            
            await asyncio.sleep(interval_minutes * 60)
    
    def stop_monitoring(self):
        """停止监控任务"""
        self.is_running = False
        logger.info("监控服务已停止")
    
    async def _scan_all_stocks(self):
        """扫描所有自选股内的股票"""
        try:
            watching_stocks = await self.watching_service.get_watching_stocks()
            
            if not watching_stocks:
                logger.debug("自选股为空，跳过扫描")
                return
            
            logger.info(f"开始监控 {len(watching_stocks)} 只自选股...")
            
            for entry in watching_stocks:
                stock_code = entry.stock_code
                last_signals = self.last_checked_signals.get(stock_code, [])
                
                try:
                    alert = await self.signal_service.check_signal_alert(stock_code, last_signals)
                    
                    if alert:
                        # 添加到通知队列
                        self.notification_queue.append(alert)
                        
                        # 发送通知
                        await self._send_notification(alert)
                        
                        logger.warning(f"检测到新信号: {stock_code} -> {alert.new_signals}")
                    
                    # 更新上次检查的信号
                    current_result = await self.signal_service.calculate_signals(stock_code)
                    self.last_checked_signals[stock_code] = current_result.signals
                    
                except Exception as e:
                    logger.error(f"扫描股票 {stock_code} 失败: {e}")
            
            logger.info(f"监控扫描完成，共处理 {len(watching_stocks)} 只股票")
            
        except Exception as e:
            logger.error(f"扫描自选股失败: {e}", exc_info=True)
    
    async def _send_notification(self, alert: SignalAlert):
        """
        发送通知
        
        Args:
            alert: 信号告警
        """
        try:
            db = await self._get_db()
            # 保存通知到数据库
            notification_collection = db["signal_notifications"]
            await notification_collection.insert_one({
                "stock_code": alert.stock_code,
                "stock_name": alert.stock_name,
                "signals": alert.new_signals,
                "signal_strength": alert.signal_strength,
                "message": alert.message,
                "action": alert.action,
                "timestamp": alert.timestamp,
                "status": "pending"
            })
            
            logger.info(f"通知已记录: {alert.stock_code} - {alert.message}")
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}", exc_info=True)
    
    async def check_signals(self, stock_code: str) -> Optional[SignalAlert]:
        """
        检查单只股票的信号变化
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Optional[SignalAlert]: 信号告警
        """
        last_signals = self.last_checked_signals.get(stock_code, [])
        return await self.signal_service.check_signal_alert(stock_code, last_signals)
    
    async def get_pending_notifications(self) -> List[SignalAlert]:
        """
        获取待处理的通知
        
        Returns:
            List[SignalAlert]: 待处理通知列表
        """
        try:
            db = await self._get_db()
            notification_collection = db["signal_notifications"]
            cursor = notification_collection.find({"status": "pending"}).sort("timestamp", -1)
            notifications = await cursor.to_list(length=100)
            
            return [SignalAlert(**n) for n in notifications]
            
        except Exception as e:
            logger.error(f"获取待处理通知失败: {e}", exc_info=True)
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
        
        Returns:
            bool: 是否成功
        """
        try:
            db = await self._get_db()
            notification_collection = db["signal_notifications"]
            from bson import ObjectId
            result = await notification_collection.update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"status": "read"}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"标记通知已读失败: {e}", exc_info=True)
            return False
    
    async def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取通知历史
        
        Args:
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 通知历史列表
        """
        try:
            db = await self._get_db()
            notification_collection = db["signal_notifications"]
            cursor = notification_collection.find().sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"获取通知历史失败: {e}", exc_info=True)
            return []
