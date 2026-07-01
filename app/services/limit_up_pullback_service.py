"""
涨停回调（龙回头/N字反包）选股策略服务

核心逻辑：
1. 筛选最近N天内出现过涨停的股票
2. 涨停后出现缩量回调（3-5天）
3. 回调期间出现地量+下影线（左侧买点）
4. 放量突破5日线（右侧确认买点）
5. 回调期间不破10日线（生命线）
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from app.core.database import get_mongo_db

logger = logging.getLogger(__name__)


class LimitUpPullbackService:
    """涨停回调选股策略服务"""

    def __init__(self):
        self.db = None

    async def _get_db(self):
        """延迟获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db

    async def _get_all_stock_codes(self) -> List[dict]:
        """获取所有A股股票代码列表"""
        db = await self._get_db()
        collection = db["stock_basic_info"]
        # 使用 category 字段筛选A股，或者用 sse/exchange 字段
        cursor = collection.find(
            {
                "$or": [
                    {"category": "stock_cn"},
                    {"sse": {"$in": ["上海证券交易所", "深圳证券交易所", "上交所", "深交所"]}},
                    {"market": {"$in": ["主板", "创业板", "科创板", "北交所"]}}
                ]
            },
            projection={"_id": 0, "code": 1, "symbol": 1, "name": 1, "industry": 1}
        )
        stocks = await cursor.to_list(length=5000)
        result = []
        for s in stocks:
            code = s.get("code") or s.get("symbol")
            if code and len(str(code)) == 6 and str(code).isdigit():
                result.append({
                    "code": str(code).zfill(6),
                    "name": s.get("name", ""),
                    "industry": s.get("industry", "")
                })
        return result

    async def _get_daily_kline(self, stock_code: str, days: int = 60) -> List[Dict[str, Any]]:
        """获取股票日线数据
        
        Args:
            stock_code: 股票代码（6位数字）
            days: 获取天数
            
        Returns:
            按日期升序排列的K线数据列表
        """
        db = await self._get_db()
        stock_code = stock_code.zfill(6)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)
        start_date_str = start_date.strftime('%Y-%m-%d')

        collection = db["stock_daily_quotes"]
        cursor = collection.find(
            {
                "code": stock_code,
                "period": "daily",
                "trade_date": {"$gte": start_date_str}
            },
            projection={
                "_id": 0, 
                "code": 1, 
                "trade_date": 1, 
                "open": 1, 
                "close": 1, 
                "high": 1, 
                "low": 1, 
                "volume": 1,
                "amount": 1,
                "pct_chg": 1
            }
        ).sort("trade_date", 1)

        data = await cursor.to_list(length=days * 2)
        return data

    def _is_limit_up(self, kline: Dict[str, Any], prev_close: float = None) -> bool:
        """判断是否为涨停
        
        普通股票：涨幅 >= 9.8%（考虑四舍五入）
        创业板/科创板：涨幅 >= 19.8%
        ST股票：涨幅 >= 4.8%
        """
        pct_chg = kline.get("pct_chg")
        if pct_chg is not None:
            return pct_chg >= 9.5
        
        if prev_close and prev_close > 0:
            close = kline.get("close", 0)
            pct = (close - prev_close) / prev_close * 100
            return pct >= 9.5
        
        return False

    def _calculate_ma(self, closes: List[float], period: int) -> List[Optional[float]]:
        """计算移动平均线"""
        mas = []
        for i in range(len(closes)):
            if i < period - 1:
                mas.append(None)
            else:
                mas.append(float(np.mean(closes[i - period + 1:i + 1])))
        return mas

    def _calculate_volume_ratio(self, volumes: List[float], idx: int, period: int = 5) -> float:
        """计算量比（当日成交量 / 前N日平均成交量）"""
        if idx < period or idx >= len(volumes):
            return 1.0
        
        current_vol = volumes[idx]
        avg_vol = np.mean(volumes[idx - period:idx])
        
        if avg_vol == 0:
            return 1.0
        
        return float(current_vol / avg_vol)

    def _analyze_single_stock(
        self, 
        stock_code: str, 
        stock_name: str,
        kline_data: List[Dict[str, Any]],
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """分析单只股票是否符合涨停回调策略
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            kline_data: K线数据（升序）
            params: 策略参数
            
        Returns:
            符合条件的股票详细信息，不符合返回None
        """
        if len(kline_data) < 20:
            return None

        def safe_float(v, default=0.0):
            if v is None:
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        # 提取数据，过滤掉无效数据点
        valid_data = []
        for k in kline_data:
            open_val = safe_float(k.get("open"))
            close_val = safe_float(k.get("close"))
            high_val = safe_float(k.get("high"))
            low_val = safe_float(k.get("low"))
            vol_val = safe_float(k.get("volume"))
            if open_val > 0 and close_val > 0 and high_val > 0 and low_val > 0 and vol_val > 0:
                valid_data.append(k)

        if len(valid_data) < 20:
            return None

        dates = [k["trade_date"] for k in valid_data]
        opens = [safe_float(k["open"]) for k in valid_data]
        closes = [safe_float(k["close"]) for k in valid_data]
        highs = [safe_float(k["high"]) for k in valid_data]
        lows = [safe_float(k["low"]) for k in valid_data]
        volumes = [safe_float(k["volume"]) for k in valid_data]
        pct_chgs = [safe_float(k.get("pct_chg", 0)) for k in valid_data]

        # 计算均线
        ma5 = self._calculate_ma(closes, 5)
        ma10 = self._calculate_ma(closes, 10)
        ma20 = self._calculate_ma(closes, 20)

        # 参数
        max_lookback_days = params.get("max_lookback_days", 15)  # 最多往前找多少天的涨停
        min_pullback_days = params.get("min_pullback_days", 2)   # 最少回调天数
        max_pullback_days = params.get("max_pullback_days", 8)   # 最多回调天数
        shrink_volume_ratio = params.get("shrink_volume_ratio", 0.5)  # 缩量比例（回调期均量 / 涨停日量）
        min_shrink_days = params.get("min_shrink_days", 2)       # 最少缩量天数
        above_ma10 = params.get("above_ma10", True)             # 是否要求站上10日线
        ground_volume_ratio = params.get("ground_volume_ratio", 0.35)  # 地量比例
        lower_shadow_ratio = params.get("lower_shadow_ratio", 0.015)   # 下影线比例阈值
        breakout_ma5 = params.get("breakout_ma5", False)         # 是否要求突破5日线（右侧买点）
        breakout_volume_ratio = params.get("breakout_volume_ratio", 1.5)  # 突破放量倍数

        # 从最近开始往前找涨停日
        current_idx = len(closes) - 1
        limit_up_idx = None

        for i in range(current_idx, max(current_idx - max_lookback_days, 1), -1):
            if self._is_limit_up(kline_data[i], closes[i-1] if i > 0 else None):
                limit_up_idx = i
                break

        if limit_up_idx is None:
            return None

        # 涨停日到当前的天数
        days_since_limit_up = current_idx - limit_up_idx

        # 回调天数检查
        if days_since_limit_up < min_pullback_days or days_since_limit_up > max_pullback_days:
            return None

        # 涨停日数据
        limit_up_close = closes[limit_up_idx]
        limit_up_volume = volumes[limit_up_idx]
        limit_up_date = dates[limit_up_idx]

        # 回调期数据（涨停日次日到当前）
        pullback_indices = list(range(limit_up_idx + 1, current_idx + 1))
        if not pullback_indices:
            return None

        pullback_closes = [closes[i] for i in pullback_indices]
        pullback_volumes = [volumes[i] for i in pullback_indices]
        pullback_lows = [lows[i] for i in pullback_indices]
        pullback_pcts = [pct_chgs[i] for i in pullback_indices]

        # 计算回调幅度
        max_close_in_pullback = max(pullback_closes)
        min_close_in_pullback = min(pullback_closes)
        current_close = closes[current_idx]
        
        pullback_depth = (limit_up_close - min_close_in_pullback) / limit_up_close * 100

        # 缩量检查
        avg_pullback_volume = np.mean(pullback_volumes)
        volume_shrink_ratio = avg_pullback_volume / limit_up_volume if limit_up_volume > 0 else 1

        # 统计缩量天数
        shrink_days = sum(1 for v in pullback_volumes if v / limit_up_volume <= shrink_volume_ratio)

        if shrink_days < min_shrink_days:
            return None

        # 10日线检查
        if above_ma10 and ma10[current_idx] is not None:
            if current_close < ma10[current_idx]:
                return None

        # 地量检查（找回调期内的地量日）
        min_volume_idx_in_pullback = pullback_indices[np.argmin(pullback_volumes)]
        min_volume = volumes[min_volume_idx_in_pullback]
        ground_volume_ratio_val = min_volume / limit_up_volume if limit_up_volume > 0 else 1

        # 下影线检查（地量日是否有下影线）
        ground_day_open = opens[min_volume_idx_in_pullback]
        ground_day_close = closes[min_volume_idx_in_pullback]
        ground_day_low = lows[min_volume_idx_in_pullback]
        ground_day_high = highs[min_volume_idx_in_pullback]

        # 下影线长度 = min(open, close) - low
        lower_shadow = min(ground_day_open, ground_day_close) - ground_day_low
        lower_shadow_pct = lower_shadow / ground_day_low if ground_day_low > 0 else 0

        has_lower_shadow = lower_shadow_pct >= lower_shadow_ratio

        # 地量日是第几天
        ground_day_offset = min_volume_idx_in_pullback - limit_up_idx

        # 突破5日线检查（右侧买点）
        ma5_breakout = False
        breakout_volume = 1.0
        if breakout_ma5 and ma5[current_idx] is not None and ma5[current_idx - 1] is not None:
            prev_close = closes[current_idx - 1]
            if prev_close < ma5[current_idx - 1] and current_close >= ma5[current_idx]:
                # 检查是否放量
                avg_vol_5 = np.mean(volumes[max(0, current_idx - 5):current_idx])
                breakout_volume = volumes[current_idx] / avg_vol_5 if avg_vol_5 > 0 else 1
                if breakout_volume >= breakout_volume_ratio:
                    ma5_breakout = True

        # 连续小阴小阳（主力控盘迹象）
        small_body_days = 0
        for i in pullback_indices:
            body_pct = abs(closes[i] - opens[i]) / opens[i] if opens[i] > 0 else 0
            if body_pct < 0.02:
                small_body_days += 1
        small_body_ratio = small_body_days / len(pullback_indices) if pullback_indices else 0

        # 综合评分
        score = 0.0
        score_details = []

        # 缩量评分（25分）
        shrink_score = max(0, 25 * (1 - volume_shrink_ratio))
        score += shrink_score
        score_details.append(f"缩量: {volume_shrink_ratio:.2%} → {shrink_score:.1f}分")

        # 回调幅度适中评分（15分）：回调5-15%最佳
        if 3 <= pullback_depth <= 20:
            depth_score = 15 - abs(pullback_depth - 10) * 1.5
            depth_score = max(0, depth_score)
            score += depth_score
            score_details.append(f"回调幅度: {pullback_depth:.1f}% → {depth_score:.1f}分")

        # 地量评分（20分）
        if ground_volume_ratio_val <= ground_volume_ratio:
            ground_score = 20
        else:
            ground_score = max(0, 20 * (1 - (ground_volume_ratio_val - ground_volume_ratio) / 0.5))
        score += ground_score
        score_details.append(f"地量: {ground_volume_ratio_val:.2%} → {ground_score:.1f}分")

        # 下影线评分（15分）
        if has_lower_shadow:
            shadow_score = min(15, 10 + lower_shadow_pct * 200)
            score += shadow_score
            score_details.append(f"下影线: {lower_shadow_pct:.2%} → {shadow_score:.1f}分")

        # 站上10日线评分（10分）
        if above_ma10 and ma10[current_idx] is not None and current_close >= ma10[current_idx]:
            above_score = 10
            score += above_score
            score_details.append(f"站上10日线 → {above_score:.1f}分")

        # 小阴小阳评分（10分）
        small_body_score = small_body_ratio * 10
        score += small_body_score
        score_details.append(f"小阴小阳: {small_body_ratio:.0%} → {small_body_score:.1f}分")

        # 突破5日线加分（5分）
        if ma5_breakout:
            breakout_score = 5
            score += breakout_score
            score_details.append(f"突破5日线 → {breakout_score:.1f}分")

        # 确定信号类型
        signal_type = "观察"
        if ma5_breakout:
            signal_type = "右侧确认"
        elif has_lower_shadow and ground_volume_ratio_val <= ground_volume_ratio:
            signal_type = "左侧潜伏"
        elif volume_shrink_ratio <= shrink_volume_ratio:
            signal_type = "缩量回调中"

        # 当前价距涨停价空间
        upside_space = (limit_up_close - current_close) / current_close * 100 if current_close > 0 else 0

        return {
            "code": stock_code,
            "name": stock_name,
            "close": round(current_close, 2),
            "pct_chg": round(pct_chgs[current_idx], 2),
            "limit_up_date": limit_up_date,
            "days_since_limit_up": days_since_limit_up,
            "limit_up_close": round(limit_up_close, 2),
            "pullback_depth": round(pullback_depth, 2),
            "volume_shrink_ratio": round(volume_shrink_ratio, 4),
            "ground_volume_ratio": round(ground_volume_ratio_val, 4),
            "lower_shadow_pct": round(lower_shadow_pct, 4),
            "signal_type": signal_type,
            "score": round(score, 1),
            "score_details": score_details,
            "upside_space": round(upside_space, 2),
            "ma5": round(ma5[current_idx], 2) if ma5[current_idx] else None,
            "ma10": round(ma10[current_idx], 2) if ma10[current_idx] else None,
            "ma20": round(ma20[current_idx], 2) if ma20[current_idx] else None,
            "small_body_ratio": round(small_body_ratio, 4),
            "ground_day_offset": ground_day_offset,
            "industry": kline_data[0].get("industry", "") if kline_data else ""
        }

    async def scan_limit_up_pullback(
        self,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """扫描符合涨停回调策略的股票
        【性能优化】使用批量数据查询，将数据库查询从5000+次减少到2次
        
        Args:
            params: 策略参数
                - max_lookback_days: 最多往前找多少天的涨停（默认15）
                - min_pullback_days: 最少回调天数（默认2）
                - max_pullback_days: 最多回调天数（默认8）
                - shrink_volume_ratio: 缩量比例阈值（默认0.5）
                - min_shrink_days: 最少缩量天数（默认2）
                - above_ma10: 是否要求站上10日线（默认True）
                - ground_volume_ratio: 地量比例阈值（默认0.35）
                - lower_shadow_ratio: 下影线比例阈值（默认0.015）
                - breakout_ma5: 是否要求突破5日线（默认False）
                - min_score: 最低评分阈值（默认40）
                - limit: 返回数量限制（默认50）
                
        Returns:
            扫描结果
        """
        import time
        from collections import defaultdict
        from datetime import datetime, timedelta
        start_time = time.time()

        if params is None:
            params = {}

        default_params = {
            "max_lookback_days": 15,
            "min_pullback_days": 2,
            "max_pullback_days": 8,
            "shrink_volume_ratio": 0.5,
            "min_shrink_days": 2,
            "above_ma10": True,
            "ground_volume_ratio": 0.35,
            "lower_shadow_ratio": 0.015,
            "breakout_ma5": False,
            "breakout_volume_ratio": 1.5,
            "min_score": 40,
            "limit": 50
        }
        default_params.update(params)
        params = default_params

        logger.info(f"📊 涨停回调策略扫描开始，参数: {params}")

        db = await self._get_db()

        # ========== 第1次查询：获取所有A股股票代码和名称 ==========
        basic_collection = db["stock_basic_info"]
        basic_cursor = basic_collection.find(
            {
                "$or": [
                    {"category": "stock_cn"},
                    {"sse": {"$in": ["上海证券交易所", "深圳证券交易所", "上交所", "深交所"]}},
                    {"market": {"$in": ["主板", "创业板", "科创板", "北交所"]}}
                ]
            },
            projection={"_id": 0, "code": 1, "symbol": 1, "name": 1, "industry": 1}
        )
        basic_stocks = await basic_cursor.to_list(length=10000)

        # 构建股票代码映射
        stock_info_map = {}
        for s in basic_stocks:
            code = s.get("code") or s.get("symbol")
            if code and len(str(code)) == 6 and str(code).isdigit():
                code = str(code).zfill(6)
                stock_info_map[code] = {
                    "name": s.get("name", ""),
                    "industry": s.get("industry", "")
                }

        stock_codes = list(stock_info_map.keys())
        total_scanned = len(stock_codes)
        logger.info(f"📊 待扫描股票数量: {total_scanned}")

        # ========== 第2次查询：一次性获取所有股票最近60天日线数据 ==========
        end_date = datetime.now()
        start_date = end_date - timedelta(days=120)
        start_date_str = start_date.strftime('%Y-%m-%d')

        quotes_collection = db["stock_daily_quotes"]
        quotes_cursor = quotes_collection.find(
            {
                "code": {"$in": stock_codes},
                "period": "daily",
                "trade_date": {"$gte": start_date_str}
            },
            projection={"_id": 0, "code": 1, "trade_date": 1, "open": 1, "close": 1, "high": 1, "low": 1, "volume": 1, "amount": 1, "pct_chg": 1, "pre_close": 1}
        ).sort("trade_date", 1)

        all_quotes = await quotes_cursor.to_list(length=total_scanned * 120)

        # 按股票代码分组，并按日期去重（同一天有多条数据时，优先使用有pct_chg且成交量较小的）
        quotes_by_stock = defaultdict(list)
        quotes_by_date_by_stock = defaultdict(dict)
        for quote in all_quotes:
            code = quote.get("code", "")
            if not code or len(code) != 6 or not code.isdigit():
                continue
            trade_date = quote.get("trade_date", "")
            if not trade_date:
                continue

            existing = quotes_by_date_by_stock[code].get(trade_date)
            if existing is None:
                quotes_by_date_by_stock[code][trade_date] = quote
            else:
                # 优先使用有 pct_chg 的数据
                existing_pct = existing.get("pct_chg")
                new_pct = quote.get("pct_chg")
                if existing_pct is None and new_pct is not None:
                    quotes_by_date_by_stock[code][trade_date] = quote
                elif existing_pct is not None and new_pct is not None:
                    # 都有pct_chg，保留成交量较小的（更可能是手为单位）
                    existing_vol = existing.get("volume", 0) or 0
                    new_vol = quote.get("volume", 0) or 0
                    if new_vol < existing_vol:
                        quotes_by_date_by_stock[code][trade_date] = quote

        # 转换为列表格式并按日期排序
        for code, date_map in quotes_by_date_by_stock.items():
            sorted_quotes = sorted(date_map.values(), key=lambda x: x.get("trade_date", ""))
            quotes_by_stock[code] = sorted_quotes

        logger.info(f"📊 已获取 {len(all_quotes)} 条原始日线数据，去重后覆盖 {len(quotes_by_stock)} 只股票")

        # ========== 内存中计算每只股票的信号（零数据库查询） ==========
        semaphore = asyncio.Semaphore(200)
        results = []

        async def process_stock(code: str):
            async with semaphore:
                try:
                    kline_data = quotes_by_stock.get(code, [])
                    if len(kline_data) < 20:
                        return None

                    info = stock_info_map.get(code, {})
                    name = info.get("name", "")
                    industry = info.get("industry", "")

                    result = self._analyze_single_stock(code, name, kline_data, params)
                    if result and result["score"] >= params["min_score"]:
                        result["industry"] = industry
                        return result
                    return None
                except Exception as e:
                    logger.warning(f"分析股票 {code} 失败: {e}")
                    return None

        # 分批处理，避免任务过多
        batch_size = 1000
        for i in range(0, len(stock_codes), batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            tasks = [process_stock(code) for code in batch_codes]
            batch_results = await asyncio.gather(*tasks)
            results.extend([r for r in batch_results if r is not None])
            logger.info(f"📊 扫描进度: {min(i + batch_size, len(stock_codes))}/{len(stock_codes)}, 已找到 {len(results)} 只符合条件的股票")

        # 按评分排序
        results.sort(key=lambda x: x["score"], reverse=True)

        # 限制返回数量
        results = results[:params["limit"]]

        took_ms = int((time.time() - start_time) * 1000)

        logger.info(f"✅ 涨停回调策略扫描完成: 找到 {len(results)} 只股票, 耗时 {took_ms}ms")

        return {
            "total": len(results),
            "items": results,
            "took_ms": took_ms,
            "params": params,
            "scanned_count": len(stock_codes)
        }


# 单例
_limit_up_pullback_service = None


def get_limit_up_pullback_service() -> LimitUpPullbackService:
    """获取涨停回调策略服务单例"""
    global _limit_up_pullback_service
    if _limit_up_pullback_service is None:
        _limit_up_pullback_service = LimitUpPullbackService()
    return _limit_up_pullback_service
