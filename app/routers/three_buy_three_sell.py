"""
三买三卖交易系统 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.routers.auth_db import get_current_user
from app.services.three_buy_three_sell_service import ThreeBuyThreeSellService
from app.services.trading_pool_service import TradingPoolService
from app.services.monitoring_service import MonitoringService
from app.models.three_buy_three_sell import (
    TradingPoolEntry,
    SignalDetectionResult,
    PoolStatistics,
    SignalAlert,
    WatchingStock,
    ScanResult
)
import logging

logger = logging.getLogger("webapi")
router = APIRouter(tags=["three-buy-three-sell"])


# 服务实例
signal_service = ThreeBuyThreeSellService()
pool_service = TradingPoolService()
monitoring_service = MonitoringService()
from app.services.watching_stock_service import WatchingStockService
watching_service = WatchingStockService()


@router.get("/stocks/{stock_code}/analysis", response_model=SignalDetectionResult)
async def analyze_stock(
    stock_code: str,
    user: dict = Depends(get_current_user)
):
    """
    分析个股三买三卖信号
    """
    result = await signal_service.calculate_signals(stock_code)
    
    if result.stock_code == stock_code and result.current_price == 0:
        raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的数据")
    
    return result


@router.get("/scan/candidates", response_model=List[SignalDetectionResult])
async def scan_candidates(
    min_score: int = 5,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    扫描全市场，识别具备三买条件的候选股票
    """
    results = await signal_service.scan_candidate_stocks(min_score=min_score, limit=limit)
    return results


@router.post("/trading-pool/add")
async def add_to_pool(
    stock_code: str,
    pool_type: str = "buy_candidate",
    entry_signal: str = "manual",
    entry_price: Optional[float] = None,
    quantity: int = 0,
    target_position: str = "1/3",
    notes: str = "",
    user: dict = Depends(get_current_user)
):
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
    """
    if pool_type not in ["buy_candidate", "holding", "watching"]:
        raise HTTPException(status_code=400, detail="无效的池类型")
    
    entry = await pool_service.add_to_pool(
        stock_code=stock_code,
        pool_type=pool_type,
        entry_signal=entry_signal,
        entry_price=entry_price,
        quantity=quantity,
        target_position=target_position,
        notes=notes
    )
    
    return {"success": True, "entry": entry.dict()}


@router.get("/trading-pool", response_model=List[TradingPoolEntry])
async def get_trading_pool(
    pool_type: str = "all",
    user: dict = Depends(get_current_user)
):
    """
    获取交易池中的股票
    
    Args:
        pool_type: 池类型: buy_candidate | holding | watching | all
    """
    entries = await pool_service.get_pool_stocks(pool_type=pool_type)
    return entries


@router.delete("/trading-pool/{stock_code}")
async def remove_from_pool(
    stock_code: str,
    user: dict = Depends(get_current_user)
):
    """
    从交易池移除股票
    """
    success = await pool_service.remove_from_pool(stock_code)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不在交易池中")
    
    return {"success": True}


@router.put("/trading-pool/{stock_code}/move")
async def move_to_pool(
    stock_code: str,
    to_pool: str,
    user: dict = Depends(get_current_user)
):
    """
    移动股票到另一个池
    
    Args:
        stock_code: 股票代码
        to_pool: 目标池类型
    """
    if to_pool not in ["buy_candidate", "holding", "watching"]:
        raise HTTPException(status_code=400, detail="无效的池类型")
    
    success = await pool_service.move_to_pool(stock_code, to_pool)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不在交易池中")
    
    return {"success": True}


@router.get("/trading-pool/statistics", response_model=PoolStatistics)
async def get_pool_statistics(user: dict = Depends(get_current_user)):
    """
    获取交易池统计信息
    """
    stats = await pool_service.get_pool_statistics()
    return stats


@router.get("/trading-pool/signals")
async def scan_pool_signals(user: dict = Depends(get_current_user)):
    """
    扫描交易池中所有股票的信号
    """
    results = await pool_service.scan_pool_signals()
    return {"success": True, "data": results}


@router.post("/trading-pool/{stock_code}/position")
async def update_position(
    stock_code: str,
    quantity: int,
    avg_cost: float,
    user: dict = Depends(get_current_user)
):
    """
    更新持仓信息
    
    Args:
        stock_code: 股票代码
        quantity: 持仓数量
        avg_cost: 平均成本
    """
    success = await pool_service.update_position(stock_code, quantity, avg_cost)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不在交易池中")
    
    return {"success": True}


@router.post("/monitoring/start")
async def start_monitoring(
    interval_minutes: int = 5,
    user: dict = Depends(get_current_user)
):
    """
    启动实时监控服务
    """
    import asyncio
    asyncio.create_task(monitoring_service.start_monitoring(interval_minutes=interval_minutes))
    
    return {"success": True, "message": f"监控服务已启动，扫描间隔: {interval_minutes}分钟"}


@router.post("/monitoring/stop")
async def stop_monitoring(user: dict = Depends(get_current_user)):
    """
    停止实时监控服务
    """
    monitoring_service.stop_monitoring()
    return {"success": True, "message": "监控服务已停止"}


@router.get("/monitoring/status")
async def get_monitoring_status(user: dict = Depends(get_current_user)):
    """
    获取监控服务状态
    """
    return {"is_running": monitoring_service.is_running}


@router.get("/monitoring/alerts", response_model=List[SignalAlert])
async def get_pending_alerts(user: dict = Depends(get_current_user)):
    """
    获取待处理的信号告警
    """
    alerts = await monitoring_service.get_pending_notifications()
    return alerts


@router.get("/monitoring/history")
async def get_notification_history(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    获取通知历史
    """
    history = await monitoring_service.get_notification_history(limit=limit)
    return {"success": True, "data": history}


@router.get("/signals/{stock_code}")
async def check_stock_signals(
    stock_code: str,
    user: dict = Depends(get_current_user)
):
    """
    检查单只股票的当前信号（用于实时监控）
    """
    result = await signal_service.calculate_signals(stock_code)
    
    if result.stock_code == stock_code and result.current_price == 0:
        raise HTTPException(status_code=404, detail=f"未找到股票 {stock_code} 的数据")
    
    return result


# === 扫描全市场 API ===
@router.get("/scan/all")
async def scan_all_stocks_classified(
    limit_per_category: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    扫描全市场所有股票，按B1/B2/B3和S1/S2/S3分类返回

    返回结果包含:
    - buy_signals: 买入信号分类 (B1/B2/B3)
    - sell_signals: 卖出信号分类 (S1/S2/S3)
    """
    result = await signal_service.scan_all_stocks_classified(limit_per_category=limit_per_category)
    return {
        "success": True,
        "data": result,
        "message": f"扫描完成，共扫描 {result.total_scanned} 只股票，发现 {result.total_with_signals} 只有信号"
    }


# === screening 页面集成：按信号类型+可配置参数筛选股票 ===
class SignalScreeningRequest(BaseModel):
    signal_type: str
    params: Dict[str, Any] = {}


@router.post("/screen/signal")
async def screen_by_signal(
    request: SignalScreeningRequest,
    user: dict = Depends(get_current_user)
):
    """
    根据信号类型和可配置参数筛选股票（用于 screening 页面）
    
    Args:
        signal_type: B1 | B2 | B3 | S1 | S2 | S3
        params: 各信号的可调参数
    """
    if request.signal_type not in ["B1", "B2", "B3", "S1", "S2", "S3"]:
        raise HTTPException(status_code=400, detail="无效的信号类型，必须是 B1/B2/B3/S1/S2/S3")
    
    results = await signal_service.screen_by_signal_params(
        signal_type=request.signal_type,
        params=request.params
    )
    
    return {
        "success": True,
        "data": results,
        "total": len(results),
        "message": f"按 {request.signal_type} 信号筛选，共找到 {len(results)} 只股票"
    }


# === 自选股管理 API ===
@router.get("/watching", response_model=List[WatchingStock])
async def get_watching_stocks(
    user: dict = Depends(get_current_user)
):
    """
    获取自选股列表
    """
    stocks = await watching_service.get_watching_stocks()
    return stocks


@router.post("/watching/add")
async def add_to_watching(
    stock_code: str,
    stock_name: str,
    added_signal: str = "manual",
    entry_price: Optional[float] = None,
    notes: str = "",
    user: dict = Depends(get_current_user)
):
    """
    添加股票到自选股
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        added_signal: 加入时的信号: B1 | B2 | B3 | S1 | S2 | S3 | manual
        entry_price: 加入时的价格
        notes: 备注
    """
    stock = await watching_service.add_stock(
        stock_code=stock_code,
        stock_name=stock_name,
        added_signal=added_signal,
        entry_price=entry_price,
        notes=notes
    )
    
    return {"success": True, "stock": stock.model_dump()}


@router.delete("/watching/{stock_code}")
async def remove_from_watching(
    stock_code: str,
    user: dict = Depends(get_current_user)
):
    """
    从自选股移除股票
    """
    success = await watching_service.remove_stock(stock_code)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不在自选股中")
    
    return {"success": True}


@router.get("/watching/{stock_code}/status")
async def check_watching_status(
    stock_code: str,
    user: dict = Depends(get_current_user)
):
    """
    检查股票是否在自选股中
    """
    is_watching = await watching_service.is_in_watching(stock_code)
    return {"stock_code": stock_code, "is_watching": is_watching}


@router.get("/watching/count")
async def get_watching_count(user: dict = Depends(get_current_user)):
    """
    获取自选股数量
    """
    count = await watching_service.get_watching_count()
    return {"count": count}
