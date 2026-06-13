"""
三买三卖交易系统数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# === 交易池条目 ===
class TradingPoolEntry(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    pool_type: str = Field(..., description="池类型: buy_candidate | holding | watching")
    entry_date: datetime = Field(default_factory=datetime.now, description="入池日期")
    entry_price: Optional[float] = Field(None, description="入池价格")
    entry_signal: str = Field("manual", description="入池信号: B1 | B2 | B3 | manual")
    quantity: int = Field(0, description="持仓数量")
    target_position: str = Field("1/3", description="目标仓位: 1/3 | 2/3 | full")
    status: str = Field("active", description="状态: active | closed | removed")
    notes: str = Field("", description="备注")
    created_at: datetime = Field(default_factory=datetime.now)


# === 持仓记录 ===
class Position(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="平均成本")
    current_price: float = Field(0.0, description="当前价格")
    unrealized_pnl: float = Field(0.0, description="浮动盈亏")
    position_ratio: str = Field("1/3", description="仓位比例")
    entry_date: datetime = Field(default_factory=datetime.now, description="建仓日期")
    signals_triggered: List[str] = Field(default_factory=list, description="已触发信号")
    status: str = Field("holding", description="状态: holding | sold")
    created_at: datetime = Field(default_factory=datetime.now)


# === 信号历史 ===
class SignalHistory(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    signal_type: str = Field(..., description="信号类型: B1 | B2 | B3 | S1 | S2 | S3")
    signal_name: str = Field(..., description="信号名称")
    trigger_date: datetime = Field(default_factory=datetime.now, description="触发日期")
    trigger_price: float = Field(..., description="触发价格")
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, description="触发时的指标值")
    action_taken: str = Field("", description="采取的操作")
    notification_sent: bool = Field(False, description="是否已发送通知")
    is_active: bool = Field(True, description="是否有效")
    created_at: datetime = Field(default_factory=datetime.now)


# === 信号检测结果 ===
class SignalDetectionResult(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="指标值")
    signals: List[str] = Field(default_factory=list, description="当前触发的信号")
    recommendations: List[str] = Field(default_factory=list, description="操作建议")
    position_advice: str = Field("hold", description="仓位建议: hold | add | reduce | exit")


# === 监控告警 ===
class SignalAlert(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    new_signals: List[str] = Field(default_factory=list, description="新出现的信号")
    signal_strength: str = Field("mild", description="信号强度: mild | strong | critical")
    message: str = Field("", description="告警消息")
    action: str = Field("", description="建议操作")
    timestamp: datetime = Field(default_factory=datetime.now)


# === 自选股条目 ===
class WatchingStock(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    added_date: datetime = Field(default_factory=datetime.now, description="加入日期")
    added_signal: str = Field("", description="加入时的信号: B1 | B2 | B3 | S1 | S2 | S3 | manual")
    entry_price: Optional[float] = Field(None, description="加入时的价格")
    status: str = Field("active", description="状态: active | removed")
    notes: str = Field("", description="备注")
    created_at: datetime = Field(default_factory=datetime.now)


# === 扫描结果分类 ===
class ScanResultCategory(BaseModel):
    """扫描结果分类"""
    category: str = Field(..., description="分类: B1 | B2 | B3 | S1 | S2 | S3")
    category_name: str = Field(..., description="分类名称")
    category_description: str = Field(..., description="分类描述")
    stocks: List[SignalDetectionResult] = Field(default_factory=list, description="该分类下的股票")
    count: int = Field(0, description="股票数量")


class ScanResult(BaseModel):
    """扫描结果"""
    total_scanned: int = Field(0, description="扫描总数")
    total_with_signals: int = Field(0, description="有信号的股票总数")
    scan_time: datetime = Field(default_factory=datetime.now, description="扫描时间")
    buy_signals: List[ScanResultCategory] = Field(default_factory=list, description="买入信号分类")
    sell_signals: List[ScanResultCategory] = Field(default_factory=list, description="卖出信号分类")


# === 交易池统计 ===
class PoolStatistics(BaseModel):
    total_stocks: int = Field(0, description="股票总数")
    buy_candidate_count: int = Field(0, description="买入候选池数量")
    holding_count: int = Field(0, description="持仓数量")
    watching_count: int = Field(0, description="观察池数量")
    active_signals: int = Field(0, description="活跃信号数")
