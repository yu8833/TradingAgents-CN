from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# 统一指标库
from tradingagents.tools.analysis.indicators import IndicatorSpec, compute_many
# 统一多数据源DF接口（按优先级降级）
from tradingagents.dataflows.data_source_manager import get_data_source_manager
from tradingagents.dataflows.providers.china.fundamentals_snapshot import get_cn_fund_snapshot


from app.services.screening.eval_utils import (
    collect_fields_from_conditions as _collect_fields_from_conditions_util,
    evaluate_conditions as _evaluate_conditions_util,
    evaluate_fund_conditions as _evaluate_fund_conditions_util,
    safe_float as _safe_float_util,
)

# --- DSL 约束 ---
# 允许用于筛选的所有字段名（覆盖行情、技术指标、基本面、标志信号）
ALLOWED_FIELDS = {
    # 原始行情（统一为小写列）
    "open", "high", "low", "close", "vol", "amount",
    # 派生
    "pct_chg",  # 当日涨跌幅
    # MA（固定参数）
    "ma5", "ma10", "ma20", "ma60",
    # EMA / MACD
    "ema12", "ema26",
    "dif", "dea", "macd_hist",
    # 振荡 / 波动率
    "rsi14",
    "boll_mid", "boll_upper", "boll_lower",
    "atr14",
    # KDJ
    "kdj_k", "kdj_d", "kdj_j",
    # 基本面（基础快照 / 扩展）
    "pe", "pb", "pe_ttm", "pb_mrq", "roe", "market_cap",
    "total_mv", "circ_mv",
    # 交易指标（从股票基础信息 / 视图拿到）
    "turnover_rate", "volume_ratio",
    # 板块 / 市场
    "market", "board", "industry", "area",
    # 技术信号标志字段（金叉 / 站上均线）
    "macd_golden_fork", "kdj_golden_fork",
    "ma5_cross", "ma10_cross", "ma20_cross", "ma60_cross",
}

# 分类：基础行情字段、技术指标字段、基本面字段
BASE_FIELDS = {"open", "high", "low", "close", "vol", "amount", "pct_chg"}
TECH_FIELDS = {
    "ma5", "ma10", "ma20", "ma60",
    "ema12", "ema26",
    "dif", "dea", "macd_hist",
    "rsi14",
    "boll_mid", "boll_upper", "boll_lower",
    "atr14",
    "kdj_k", "kdj_d", "kdj_j",
    # 标志字段
    "macd_golden_fork", "kdj_golden_fork",
    "ma5_cross", "ma10_cross", "ma20_cross", "ma60_cross",
}
FUND_FIELDS = {"pe", "pb", "pe_ttm", "pb_mrq", "roe", "market_cap", "total_mv", "circ_mv",
               "turnover_rate", "volume_ratio", "market", "board", "industry", "area"}

# 允许的操作符（注意：前端可能发送 'eq' 代替 '=='，这里全部接纳，并在评估时归一化）
ALLOWED_OPS = {">", "<", ">=", "<=", "==", "!=", "eq", "ne",
                "between", "in", "not_in", "contains", "cross_up", "cross_down"}


@dataclass
class ScreeningParams:
    market: str = "CN"
    date: Optional[str] = None  # YYYY-MM-DD，None=最近交易日
    adj: str = "qfq"  # 预留参数，当前实现使用Tdx数据，不区分复权
    limit: int = 50
    offset: int = 0
    order_by: Optional[List[Dict[str, str]]] = None  # [{field, direction}]


import logging
logger = logging.getLogger("agents")

class ScreeningService:
    def __init__(self):
        # 数据源通过统一DF接口获取，不直接绑定具体源
        self.provider = None

    # --- 公共入口 ---
    def run(self, conditions: Dict[str, Any], params: ScreeningParams) -> Dict[str, Any]:
        symbols = self._get_universe()
        # 为控制时长，先限制样本规模（后续用批量/缓存优化）
        symbols = symbols[:120]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=220)
        end_s = end_date.strftime("%Y-%m-%d")
        start_s = start_date.strftime("%Y-%m-%d")

        results: List[Dict[str, Any]] = []

        # 解析条件中涉及的字段，决定是否需要技术指标/行情
        needed_fields = self._collect_fields_from_conditions(conditions)
        order_fields = {o.get("field") for o in (params.order_by or []) if o.get("field")}
        all_needed = set(needed_fields) | set(order_fields)
        need_tech = any(f in TECH_FIELDS for f in all_needed)
        need_base = any(f in BASE_FIELDS for f in all_needed) or need_tech
        need_fund = any(f in FUND_FIELDS for f in all_needed)

        for code in symbols:
            try:
                dfc = None
                last = None

                # 如需要基础行情/技术指标才取K线
                if need_base:
                    manager = get_data_source_manager()
                    df = manager.get_stock_dataframe(code, start_s, end_s)
                    if df is None or df.empty:
                        continue
                    # 统一列为小写
                    dfu = df.rename(columns={
                        "Open": "open", "High": "high", "Low": "low", "Close": "close",
                        "Volume": "vol", "Amount": "amount"
                    }).copy()
                    # 计算派生：pct_chg
                    if "close" in dfu.columns:
                        dfu["pct_chg"] = dfu["close"].pct_change() * 100.0

                    # 仅在需要技术指标时计算
                    if need_tech:
                        specs = [
                            IndicatorSpec("ma", {"n": 5}),
                            IndicatorSpec("ma", {"n": 10}),
                            IndicatorSpec("ma", {"n": 20}),
                            IndicatorSpec("ema", {"n": 12}),
                            IndicatorSpec("ema", {"n": 26}),
                            IndicatorSpec("macd"),
                            IndicatorSpec("rsi", {"n": 14}),
                            IndicatorSpec("boll", {"n": 20, "k": 2}),
                            IndicatorSpec("atr", {"n": 14}),
                            IndicatorSpec("kdj", {"n": 9, "m1": 3, "m2": 3}),
                        ]
                        dfc = compute_many(dfu, specs)
                    else:
                        dfc = dfu

                    last = dfc.iloc[-1]

                # 评估条件（若条件完全是基本面且不涉及行情/技术，这里可跳过K线）
                passes = True
                if need_base:
                    passes = self._evaluate_conditions(dfc, conditions)
                elif need_fund and not need_base and not need_tech:
                    # 仅基本面条件：使用基本面快照判断
                    snap = get_cn_fund_snapshot(code)
                    if not snap:
                        passes = False
                    else:
                        passes = self._evaluate_fund_conditions(snap, conditions)

                if passes:
                    item = {"code": code}
                    if last is not None:
                        item.update({
                            "close": self._safe_float(last.get("close")),
                            "pct_chg": self._safe_float(last.get("pct_chg")),
                            "amount": self._safe_float(last.get("amount")),
                            "ma20": self._safe_float(last.get("ma20")) if need_tech else None,
                            "rsi14": self._safe_float(last.get("rsi14")) if need_tech else None,
                            "kdj_k": self._safe_float(last.get("kdj_k")) if need_tech else None,
                            "kdj_d": self._safe_float(last.get("kdj_d")) if need_tech else None,
                            "kdj_j": self._safe_float(last.get("kdj_j")) if need_tech else None,
                            "dif": self._safe_float(last.get("dif")) if need_tech else None,
                            "dea": self._safe_float(last.get("dea")) if need_tech else None,
                            "macd_hist": self._safe_float(last.get("macd_hist")) if need_tech else None,
                        })
                    results.append(item)
            except Exception:
                continue

        total = len(results)
        # 排序
        if params.order_by:
            for order in reversed(params.order_by):  # 后者优先级低
                f = order.get("field")
                d = order.get("direction", "desc").lower()
                if f in ALLOWED_FIELDS:
                    results.sort(key=lambda x: (x.get(f) is None, x.get(f)), reverse=(d == "desc"))

        # 分页
        start = params.offset or 0
        end = start + (params.limit or 50)
        page_items = results[start:end]

        return {
            "total": total,
            "items": page_items,
        }
    def _evaluate_fund_conditions(self, snap: Dict[str, Any], node: Dict[str, Any]) -> bool:
        """Delegate fundamental condition evaluation to utils to keep service slim."""
        return _evaluate_fund_conditions_util(snap, node, FUND_FIELDS)


    def _collect_fields_from_conditions(self, node: Dict[str, Any]) -> List[str]:
        """Delegate field collection to utils."""
        return _collect_fields_from_conditions_util(node, ALLOWED_FIELDS)

    # --- 内部：DSL 评估 ---
    def _evaluate_conditions(self, df: pd.DataFrame, node: Dict[str, Any]) -> bool:
        """Delegate technical/base condition evaluation to utils."""
        return _evaluate_conditions_util(df, node, ALLOWED_FIELDS, ALLOWED_OPS)

    # --- 工具 ---
    def _safe_float(self, v: Any) -> Optional[float]:
        """Delegate numeric coercion to utils."""
        return _safe_float_util(v)

    def _get_universe(self) -> List[str]:
        """获取A股代码集合：从 MongoDB stock_basic_info 集合获取所有A股股票代码"""
        try:
            from app.core.database import get_mongo_db_sync, settings as _db_settings

            # 优先使用同步 MongoDB 客户端查询
            db = get_mongo_db_sync()
            collection = db.stock_basic_info

            # 查询所有A股股票代码（兼容不同的数据结构）
            query = {
                "$or": [
                    {"market_info.market": "CN"},  # 新数据结构
                    {"category": "stock_cn"},      # 旧数据结构
                    {"market": {"$in": ["主板", "创业板", "科创板", "北交所"]}}  # 按市场类型
                ]
            }

            # 优先尝试同步迭代（pymongo 同步游标）
            codes: List[str] = []
            try:
                cursor = collection.find(query, {"code": 1, "_id": 0})
                # 使用 list() 显式转换，检测是否是同步游标
                docs = list(cursor)
                codes = [doc.get("code") for doc in docs if doc.get("code")]
            except (TypeError, AttributeError):
                # 如果是异步游标，改用独立的同步客户端直连查询
                try:
                    from pymongo import MongoClient
                    sync_client = MongoClient(
                        _db_settings.MONGO_URI,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                    )
                    sync_db = sync_client[_db_settings.MONGO_DB]
                    sync_cursor = sync_db.stock_basic_info.find(
                        query, {"code": 1, "_id": 0}
                    )
                    codes = [doc.get("code") for doc in sync_cursor if doc.get("code")]
                    try:
                        sync_client.close()
                    except Exception:
                        pass
                except Exception as inner_e:
                    logger.error(f"❌ 同步直连MongoDB获取股票列表失败: {inner_e}")

            if codes:
                logger.info(f"📊 从 MongoDB 获取到 {len(codes)} 只A股股票")
                return codes
            else:
                logger.warning("⚠️ MongoDB 中未找到股票数据，使用兜底股票列表")
                return ["000001", "000002", "000858", "600519", "600036", "601318", "300750"]

        except Exception as e:
            logger.error(f"❌ 从 MongoDB 获取股票列表失败: {e}")
            return ["000001", "000002", "000858", "600519", "600036", "601318", "300750"]

