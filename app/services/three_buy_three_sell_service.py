"""
三买三卖信号计算服务
复用 wind-trading-system 的指标计算逻辑
"""
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.core.database import get_mongo_db
from app.models.three_buy_three_sell import SignalDetectionResult, SignalAlert, ScanResult, ScanResultCategory
import logging

logger = logging.getLogger(__name__)


class ThreeBuyThreeSellService:
    """
    三买三卖信号计算服务
    
    三买信号:
    - B1: 左侧买点 - BIAS60 在 [-30%, -20%]
    - B2: 突破买点 - 放量突破 MA55/MA60
    - B3: 回踩买点 - 回踩确认后再次放量
    
    三卖信号:
    - S1: 加速卖点 - BIAS60 超过阈值
    - S2: 跌破卖点 - 连续跌破短期均线
    - S3: 清仓卖点 - 跌破长期均线且趋势向下
    """
    
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        """延迟获取数据库连接"""
        if self.db is None:
            self.db = get_mongo_db()
        return self.db
    
    async def _get_price_data(self, stock_code: str, days: int = 120) -> List[dict]:
        """获取股票历史价格数据
        
        从 stock_daily_quotes 集合获取日线历史数据
        """
        db = await self._get_db()
        
        # 统一股票代码格式为6位数字
        stock_code = stock_code.zfill(6)
        
        # 计算开始日期（120天前）
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)  # 多取一些数据以确保有足够数据计算均线
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # 从 stock_daily_quotes 读取日线历史数据
        collection = db["stock_daily_quotes"]
        cursor = collection.find(
            {
                "code": stock_code,
                "period": "daily",
                "trade_date": {"$gte": start_date_str}
            },
            projection={"_id": 0, "code": 1, "trade_date": 1, "open": 1, "close": 1, "high": 1, "low": 1, "volume": 1}
        ).sort("trade_date", 1)  # 按日期升序排序
        
        data = await cursor.to_list(length=days * 2)
        
        # 获取股票名称（从 stock_basic_info）
        name = ""
        try:
            basic_collection = db["stock_basic_info"]
            basic_doc = await basic_collection.find_one(
                {"code": stock_code},
                projection={"_id": 0, "name": 1}
            )
            if basic_doc:
                name = basic_doc.get("name", "")
        except Exception:
            pass
        
        # 为每条记录添加 name 字段
        for item in data:
            item["name"] = name
        
        return data
    
    async def _get_financial_data(self, stock_code: str) -> dict:
        """获取股票财务数据"""
        db = await self._get_db()
        stock_code = stock_code.zfill(6)
        collection = db["stock_screening_view"]
        doc = await collection.find_one(
            {"code": stock_code},
            projection={"_id": 0}
        )
        return doc if doc else {}
    
    def _calculate_moving_average(self, data: List[float], window: int) -> Optional[float]:
        """计算移动平均线"""
        if len(data) < window:
            return None
        return float(np.mean(data[-window:]))
    
    def _calculate_bias(self, price: float, ma_60: float) -> float:
        """计算BIAS60指标"""
        if ma_60 is None or ma_60 == 0:
            return 0
        return ((price - ma_60) / ma_60) * 100
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """计算MACD指标"""
        prices = np.array(prices)
        if len(prices) < 26:
            return None, None, None
        
        ema_fast = pd.Series(prices).ewm(span=12, adjust=False).mean().values
        ema_slow = pd.Series(prices).ewm(span=26, adjust=False).mean().values
        dif = ema_fast - ema_slow
        dea = pd.Series(dif).ewm(span=9, adjust=False).mean().values
        macd_bar = 2 * (dif - dea)
        
        return dif, dea, macd_bar
    
    def _detect_buy_signal_1(self, bias: float) -> bool:
        """检测B1 - 左侧买点"""
        return -40 <= bias <= -10
    
    def _detect_buy_signal_2(self, opens: List[float], closes: List[float], volumes: List[int], 
                            ma_55: float, ma_60: float) -> bool:
        """检测B2 - 突破买点"""
        if len(closes) < 2:
            return False
        
        current_close = closes[-1]
        prev_close = closes[-2]
        current_open = opens[-1] if len(opens) >= len(closes) else closes[-1]
        current_volume = volumes[-1] if volumes else 0
        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
        
        volume_condition = current_volume >= avg_volume * 1.2
        price_condition = current_close >= ma_55 and current_close >= ma_60
        prev_price_condition = prev_close < ma_55 or prev_close < ma_60
        
        mid_yang = (current_close - current_open) / current_open >= 0.03
        
        return volume_condition and price_condition and prev_price_condition and mid_yang
    
    def _detect_buy_signal_3(self, closes: List[float], opens: List[float], volumes: List[int],
                            ma_13: float, ma_55: float, ma_60: float, bias: float, biases_30d: List[float]) -> bool:
        """检测B3 - 回踩买点"""
        if ma_13 is None or ma_55 is None or ma_60 is None:
            return False
        
        ma_13_condition = ma_13 > ma_55 * 0.95
        bias_condition = -10 <= bias <= 10
        
        has_positive_bias = any(b >= 5 for b in biases_30d) if biases_30d else False
        
        if not has_positive_bias:
            return False
        
        if len(closes) < 2:
            return False
        
        current_close = closes[-1]
        
        return ma_13_condition and bias_condition and current_close >= ma_60 * 0.98
    
    def _detect_sell_signal_1(self, bias: float, stock_type: str = "normal") -> bool:
        """检测S1 - 加速卖点"""
        thresholds = {"normal": 25, "tech_leader": 50, "high_recognition": 80}
        return bias >= thresholds.get(stock_type, 25)
    
    def _detect_sell_signal_2(self, closes: List[float], ma_5: float, ma_8: float, ma_13: float) -> bool:
        """检测S2 - 跌破卖点"""
        if len(closes) < 2:
            return False
        
        below_ma5 = closes[-1] < ma_5 if ma_5 else False
        below_ma8 = closes[-1] < ma_8 if ma_8 else False
        below_ma13 = closes[-1] < ma_13 if ma_13 else False
        
        below_ma5_prev = closes[-2] < ma_5 if ma_5 else False
        below_ma8_prev = closes[-2] < ma_8 if ma_8 else False
        below_ma13_prev = closes[-2] < ma_13 if ma_13 else False
        
        return (below_ma5 and below_ma8 and below_ma13) and (below_ma5_prev and below_ma8_prev and below_ma13_prev)
    
    def _detect_sell_signal_3(self, closes: List[float], ma_55: float, ma_60: float, ma_60_history: List[float]) -> bool:
        """检测S3 - 清仓卖点"""
        if len(closes) < 2 or ma_60_history is None or len(ma_60_history) < 5:
            return False
        
        below_ma55 = closes[-1] < ma_55 if ma_55 else False
        below_ma60 = closes[-1] < ma_60 if ma_60 else False
        
        ma60_slope = np.polyfit(range(len(ma_60_history[-5:])), ma_60_history[-5:], 1)[0]
        ma60_trend_down = ma60_slope < 0
        
        return below_ma55 and below_ma60 and ma60_trend_down
    
    def _calculate_signal_score(self, volume_ratio: float, price_change: float, 
                               ma_shape: str, market_condition: str, macd_status: str) -> int:
        """计算信号评分"""
        score = 0
        
        if volume_ratio >= 2.0:
            score += 2
        elif volume_ratio >= 1.5:
            score += 1
        
        if price_change >= 7:
            score += 2
        elif price_change >= 5:
            score += 1
        
        if ma_shape == "converge_diverge":
            score += 2
        elif ma_shape == "bullish":
            score += 1
        
        if market_condition == "rising":
            score += 2
        elif market_condition == "sideways":
            score += 1
        
        if macd_status == "golden_cross" or macd_status == "positive":
            score += 2
        elif macd_status == "above_zero":
            score += 1
        
        return score
    
    async def calculate_signals(self, stock_code: str) -> SignalDetectionResult:
        """
        计算个股的三买三卖信号
        
        返回: SignalDetectionResult
        """
        try:
            # 获取价格数据
            price_data = await self._get_price_data(stock_code, 120)
            
            if not price_data:
                logger.warning(f"未找到股票 {stock_code} 的价格数据")
                return SignalDetectionResult(
                    stock_code=stock_code,
                    stock_name="",
                    current_price=0.0,
                    position_advice="hold"
                )
            
            # 提取数据
            prices = [p["close"] for p in price_data]
            opens = [p.get("open", p["close"]) for p in price_data]
            volumes = [p.get("volume", 0) for p in price_data]
            
            stock_name = price_data[-1].get("name", "") if price_data else ""
            current_price = prices[-1] if prices else 0.0
            
            # 计算均线
            ma_5 = self._calculate_moving_average(prices, 5)
            ma_8 = self._calculate_moving_average(prices, 8)
            ma_13 = self._calculate_moving_average(prices, 13)
            ma_55 = self._calculate_moving_average(prices, 55)
            ma_60 = self._calculate_moving_average(prices, 60)
            ma_65 = self._calculate_moving_average(prices, 65)
            
            # 计算BIAS60
            bias_60 = self._calculate_bias(current_price, ma_60) if ma_60 else 0
            
            # 计算30天BIAS历史
            biases_30d = []
            for i in range(max(0, len(prices)-30), len(prices)):
                ma_60_i = self._calculate_moving_average(prices[:i+1], 60) if i >= 59 else 0
                if ma_60_i:
                    biases_30d.append(self._calculate_bias(prices[i], ma_60_i))
            
            # 计算MACD
            dif, dea, macd_bar = self._calculate_macd(prices)
            dif_val = dif[-1] if dif is not None and len(dif) > 0 else 0
            dea_val = dea[-1] if dea is not None and len(dea) > 0 else 0
            macd_bar_val = macd_bar[-1] if macd_bar is not None and len(macd_bar) > 0 else 0
            
            # MACD状态
            macd_status = "golden_cross" if dif_val > dea_val else "death_cross" if dif_val < dea_val else "neutral"
            
            # 计算MA60历史用于S3检测
            ma_60_history = []
            for i in range(len(prices)-60+1):
                ma_60_history.append(self._calculate_moving_average(prices[i:i+60], 60))
            
            # 检测信号
            signals = []
            recommendations = []
            
            # 调试日志：打印关键指标
            if stock_code in ['600000', '000001', '000002']:
                logger.info(f"调试 {stock_code}: bias={bias_60:.2f}, ma5={ma_5}, ma13={ma_13}, ma55={ma_55}, ma60={ma_60}, 数据天数={len(prices)}")
            
            # 🎯 策略互斥：先检测S3（清仓卖点）
            s3_active = ma_55 and ma_60 and self._detect_sell_signal_3(prices, ma_55, ma_60, ma_60_history)
            
            # 如果S3成立（趋势还在下跌通道），屏蔽所有买入信号
            if s3_active:
                signals.append("S3")
                recommendations.append("S3 - 清仓卖点：全部清仓")
                # 屏蔽B1/B2/B3（左侧交易在趋势向下时风险极高）
            else:
                # 只有当S3不成立时，才检测买入信号
                if self._detect_buy_signal_1(bias_60):
                    signals.append("B1")
                    recommendations.append("B1 - 左侧买点：小仓位试探 (目标仓位1/3)")
                
                if ma_55 and ma_60 and self._detect_buy_signal_2(opens, prices, volumes, ma_55, ma_60):
                    signals.append("B2")
                    recommendations.append("B2 - 突破买点：标准建仓 (目标仓位2/3)")
                
                if ma_13 and ma_55 and ma_60 and self._detect_buy_signal_3(prices, opens, volumes, ma_13, ma_55, ma_60, bias_60, biases_30d):
                    signals.append("B3")
                    recommendations.append("B3 - 回踩买点：加仓至满仓")
            
            # 其他卖出信号（S1/S2可以独立检测，因为可能与买入信号互斥）
            if not s3_active:
                if self._detect_sell_signal_1(bias_60):
                    signals.append("S1")
                    recommendations.append("S1 - 加速卖点：部分止盈 (卖出1/3)")
                
                if ma_5 and ma_8 and ma_13 and self._detect_sell_signal_2(prices, ma_5, ma_8, ma_13):
                    signals.append("S2")
                    recommendations.append("S2 - 跌破卖点：加大止盈 (仅留1/3)")
            
            # 确定仓位建议
            position_advice = "hold"
            if "S3" in signals:
                position_advice = "exit"
            elif "S2" in signals:
                position_advice = "reduce"
            elif "S1" in signals:
                position_advice = "reduce"
            elif "B3" in signals:
                position_advice = "add"
            elif "B2" in signals:
                position_advice = "add"
            elif "B1" in signals:
                position_advice = "add"
            
            # 计算量比和涨跌幅用于评分
            volume_ratio = volumes[-1] / (sum(volumes[-20:])/20) if len(volumes) >= 20 and volumes[-1] > 0 else 1
            price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0
            
            # MA形态判断
            ma_shape = "bullish" if ma_5 and ma_8 and ma_13 and ma_5 > ma_8 > ma_13 else "other"
            
            # 计算信号评分
            signal_score = self._calculate_signal_score(
                volume_ratio=volume_ratio,
                price_change=price_change,
                ma_shape=ma_shape,
                market_condition="rising",
                macd_status=macd_status
            )
            
            # 构建返回结果
            return SignalDetectionResult(
                stock_code=stock_code,
                stock_name=stock_name,
                current_price=current_price,
                indicators={
                    "ma_5": ma_5,
                    "ma_8": ma_8,
                    "ma_13": ma_13,
                    "ma_55": ma_55,
                    "ma_60": ma_60,
                    "ma_65": ma_65,
                    "bias_60": bias_60,
                    "dif": dif_val,
                    "dea": dea_val,
                    "macd_bar": macd_bar_val,
                    "signal_score": signal_score,
                    "volume_ratio": volume_ratio,
                    "price_change": price_change
                },
                signals=signals,
                recommendations=recommendations,
                position_advice=position_advice
            )
            
        except Exception as e:
            logger.error(f"计算股票 {stock_code} 信号失败: {e}", exc_info=True)
            return SignalDetectionResult(
                stock_code=stock_code,
                stock_name="",
                current_price=0.0,
                position_advice="hold"
            )
    
    async def scan_candidate_stocks(self, min_score: int = 5, limit: int = 50) -> List[SignalDetectionResult]:
        """
        扫描全市场，识别具备三买条件的股票
        """
        try:
            db = await self._get_db()
            collection = db["stock_screening_view"]
            cursor = collection.find(
                {},
                projection={"_id": 0, "code": 1, "name": 1}
            ).limit(limit * 2)
            
            stock_list = await cursor.to_list(length=limit * 2)
            
            # 并发处理
            semaphore = asyncio.Semaphore(50)
            
            async def process_stock(stock):
                async with semaphore:
                    result = await self.calculate_signals(stock["code"])
                    if result.signals and result.indicators.get("signal_score", 0) >= min_score:
                        return result
                    return None
            
            tasks = [process_stock(stock) for stock in stock_list]
            results = await asyncio.gather(*tasks)
            
            # 过滤 None 结果并排序
            results = [r for r in results if r is not None]
            results.sort(key=lambda x: x.indicators.get("signal_score", 0), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"扫描候选股票失败: {e}", exc_info=True)
            return []

    async def scan_all_stocks_classified(self, limit_per_category: int = 50) -> ScanResult:
        """
        扫描全市场所有股票，按B1/B2/B3和S1/S2/S3分类返回
        【性能优化】使用批量数据查询，将数据库查询从11000+次减少到2次
        
        Args:
            limit_per_category: 每个分类最多返回的股票数量
        
        Returns:
            ScanResult: 分类后的扫描结果
        """
        try:
            db = await self._get_db()
            
            # ========== 第1次查询：获取所有A股股票代码和名称 ==========
            basic_collection = db["stock_basic_info"]
            basic_cursor = basic_collection.find(
                {
                    "$or": [
                        {"market_info.market": "CN"},
                        {"category": "stock_cn"},
                        {"market": {"$in": ["主板", "创业板", "科创板", "北交所"]}}
                    ]
                },
                projection={"_id": 0, "code": 1, "name": 1}
            )
            basic_stocks = await basic_cursor.to_list(length=10000)
            
            # 构建股票代码到名称的映射
            stock_name_map = {s["code"]: s.get("name", "") for s in basic_stocks}
            stock_codes = list(stock_name_map.keys())
            
            total_scanned = len(stock_codes)
            logger.info(f"开始扫描全市场 {total_scanned} 只股票...")
            
            # ========== 第2次查询：一次性获取所有股票最近240天日线数据 ==========
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=240)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            quotes_collection = db["stock_daily_quotes"]
            quotes_cursor = quotes_collection.find(
                {
                    "code": {"$in": stock_codes},
                    "period": "daily",
                    "trade_date": {"$gte": start_date_str}
                },
                projection={"_id": 0, "code": 1, "trade_date": 1, "open": 1, "close": 1, "high": 1, "low": 1, "volume": 1}
            ).sort("trade_date", 1)
            
            all_quotes = await quotes_cursor.to_list(length=total_scanned * 240)
            
            # 按股票代码分组
            from collections import defaultdict
            quotes_by_stock = defaultdict(list)
            for quote in all_quotes:
                code = quote.get("code", "")
                if code:
                    quotes_by_stock[code].append(quote)
            
            logger.info(f"已获取 {len(all_quotes)} 条日线数据，覆盖 {len(quotes_by_stock)} 只股票")
            
            # ========== 内存中计算每只股票的信号（零数据库查询） ==========
            # 并发处理信号计算
            semaphore = asyncio.Semaphore(100)
            
            async def process_stock_signals(code: str):
                async with semaphore:
                    try:
                        price_data = quotes_by_stock.get(code, [])
                        if len(price_data) < 60:  # 需要至少60天数据计算MA60
                            return None
                        
                        # 提取数据
                        prices = [p["close"] for p in price_data]
                        opens = [p.get("open", p["close"]) for p in price_data]
                        volumes = [p.get("volume", 0) or 0 for p in price_data]
                        volumes = [int(v) if isinstance(v, (int, float)) else 0 for v in volumes]
                        stock_name = stock_name_map.get(code, "")
                        current_price = prices[-1] if prices else 0.0
                        
                        # 计算均线
                        ma_5 = self._calculate_moving_average(prices, 5)
                        ma_8 = self._calculate_moving_average(prices, 8)
                        ma_13 = self._calculate_moving_average(prices, 13)
                        ma_55 = self._calculate_moving_average(prices, 55)
                        ma_60 = self._calculate_moving_average(prices, 60)
                        ma_65 = self._calculate_moving_average(prices, 65)
                        
                        # 计算BIAS60
                        bias_60 = self._calculate_bias(current_price, ma_60) if ma_60 else 0
                        
                        # 计算30天BIAS历史
                        biases_30d = []
                        for i in range(max(0, len(prices)-30), len(prices)):
                            ma_60_i = self._calculate_moving_average(prices[:i+1], 60) if i >= 59 else 0
                            if ma_60_i:
                                biases_30d.append(self._calculate_bias(prices[i], ma_60_i))
                        
                        # 计算MACD
                        dif, dea, macd_bar = self._calculate_macd(prices)
                        dif_val = dif[-1] if dif is not None and len(dif) > 0 else 0
                        dea_val = dea[-1] if dea is not None and len(dea) > 0 else 0
                        macd_bar_val = macd_bar[-1] if macd_bar is not None and len(macd_bar) > 0 else 0
                        macd_status = "golden_cross" if dif_val > dea_val else "death_cross" if dif_val < dea_val else "neutral"
                        
                        # 计算MA60历史用于S3检测
                        ma_60_history = []
                        for i in range(len(prices)-60+1):
                            ma_60_history.append(self._calculate_moving_average(prices[i:i+60], 60))
                        
                        # 检测信号
                        signals = []
                        recommendations = []
                        
                        # 🎯 策略互斥：先检测S3（清仓卖点）
                        s3_active = ma_55 and ma_60 and self._detect_sell_signal_3(prices, ma_55, ma_60, ma_60_history)
                        
                        # 如果S3成立（趋势还在下跌通道），屏蔽所有买入信号
                        if s3_active:
                            signals.append("S3")
                            recommendations.append("S3 - 清仓卖点")
                            # 屏蔽B1/B2/B3（左侧交易在趋势向下时风险极高）
                        else:
                            # 只有当S3不成立时，才检测买入信号
                            if self._detect_buy_signal_1(bias_60):
                                signals.append("B1")
                                recommendations.append("B1 - 左侧买点")
                            
                            if ma_55 and ma_60 and self._detect_buy_signal_2(opens, prices, volumes, ma_55, ma_60):
                                signals.append("B2")
                                recommendations.append("B2 - 突破买点")
                            
                            if ma_13 and ma_55 and ma_60 and self._detect_buy_signal_3(prices, opens, volumes, ma_13, ma_55, ma_60, bias_60, biases_30d):
                                signals.append("B3")
                                recommendations.append("B3 - 回踩买点")
                        
                        # 其他卖出信号（S1/S2只在S3不成立时检测）
                        if not s3_active:
                            if self._detect_sell_signal_1(bias_60):
                                signals.append("S1")
                                recommendations.append("S1 - 加速卖点")
                            
                            if ma_5 and ma_8 and ma_13 and self._detect_sell_signal_2(prices, ma_5, ma_8, ma_13):
                                signals.append("S2")
                                recommendations.append("S2 - 跌破卖点")
                        
                        # 计算评分
                        volume_ratio = volumes[-1] / (sum(volumes[-20:])/20) if len(volumes) >= 20 and volumes[-1] > 0 and sum(volumes[-20:]) > 0 else 1
                        price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 and prices[-2] > 0 else 0
                        ma_shape = "bullish" if ma_5 and ma_8 and ma_13 and ma_5 > ma_8 > ma_13 else "other"
                        signal_score = self._calculate_signal_score(
                            volume_ratio=volume_ratio,
                            price_change=price_change,
                            ma_shape=ma_shape,
                            market_condition="rising",
                            macd_status=macd_status
                        )
                        
                        return SignalDetectionResult(
                            stock_code=code,
                            stock_name=stock_name,
                            current_price=current_price,
                            indicators={
                                "ma_5": ma_5, "ma_8": ma_8, "ma_13": ma_13,
                                "ma_55": ma_55, "ma_60": ma_60, "ma_65": ma_65,
                                "bias_60": bias_60, "dif": dif_val, "dea": dea_val,
                                "macd_bar": macd_bar_val, "signal_score": signal_score,
                                "volume_ratio": volume_ratio, "price_change": price_change
                            },
                            signals=signals,
                            recommendations=recommendations,
                            position_advice="add" if any(s in signals for s in ["B1", "B2", "B3"]) else "reduce" if any(s in signals for s in ["S1", "S2", "S3"]) else "hold"
                        )
                    except Exception as e:
                        logger.warning(f"计算股票 {code} 信号失败: {e}")
                        return None
            
            # 分批处理，避免内存问题
            batch_size = 500
            all_results = []
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i+batch_size]
                tasks = [process_stock_signals(code) for code in batch_codes]
                batch_results = await asyncio.gather(*tasks)
                all_results.extend([r for r in batch_results if r is not None])
                logger.info(f"已处理 {min(i+batch_size, len(stock_codes))}/{len(stock_codes)} 只股票，有效信号 {len(all_results)} 只")
            
            # 分类结果
            classified_results = {
                "B1": [], "B2": [], "B3": [],
                "S1": [], "S2": [], "S3": []
            }
            
            total_with_signals = 0
            
            for result in all_results:
                if result.signals:
                    total_with_signals += 1
                    for signal in result.signals:
                        if signal in classified_results:
                            classified_results[signal].append(result)
            
            # 排序并限制每个分类的数量
            for signal in classified_results:
                classified_results[signal].sort(
                    key=lambda x: x.indicators.get("signal_score", 0),
                    reverse=True
                )
                classified_results[signal] = classified_results[signal][:limit_per_category]
            
            # 信号分类信息
            signal_info = {
                "B1": ("B1 - 左侧买点", "BIAS60在[-40%,-10%]区间，可小仓位试探"),
                "B2": ("B2 - 突破买点", "放量突破MA55/MA60，可标准建仓"),
                "B3": ("B3 - 回踩买点", "回踩确认后再次放量，可加仓至满仓"),
                "S1": ("S1 - 加速卖点", "BIAS60超过阈值，建议部分止盈"),
                "S2": ("S2 - 跌破卖点", "连续跌破MA5/MA8/MA13，加大止盈"),
                "S3": ("S3 - 清仓卖点", "跌破MA55/MA60且趋势向下，建议清仓")
            }
            
            # 构建返回结果
            buy_categories = []
            for signal in ["B1", "B2", "B3"]:
                info = signal_info[signal]
                buy_categories.append(ScanResultCategory(
                    category=signal,
                    category_name=info[0],
                    category_description=info[1],
                    stocks=classified_results[signal],
                    count=len(classified_results[signal])
                ))
            
            sell_categories = []
            for signal in ["S1", "S2", "S3"]:
                info = signal_info[signal]
                sell_categories.append(ScanResultCategory(
                    category=signal,
                    category_name=info[0],
                    category_description=info[1],
                    stocks=classified_results[signal],
                    count=len(classified_results[signal])
                ))
            
            logger.info(f"扫描完成：共扫描 {total_scanned} 只，{total_with_signals} 只出现信号")
            
            return ScanResult(
                total_scanned=total_scanned,
                total_with_signals=total_with_signals,
                scan_time=datetime.now(),
                buy_signals=buy_categories,
                sell_signals=sell_categories
            )
            
        except Exception as e:
            logger.error(f"扫描全市场股票失败: {e}", exc_info=True)
            return ScanResult(
                total_scanned=0,
                total_with_signals=0,
                scan_time=datetime.now(),
                buy_signals=[],
                sell_signals=[]
            )
    
    # ==================== 可配置参数的信号筛选（用于 screening 页面集成） ====================
    
    async def screen_by_signal_params(self, signal_type: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据可配置的参数筛选满足某类信号的股票
        
        Args:
            signal_type: 信号类型 ('B1', 'B2', 'B3', 'S1', 'S2', 'S3')
            params: 参数字典，包含各信号的可调参数
            
        Returns:
            List[Dict]: 满足条件的股票列表（含代码、名称、价格、各指标值）
        """
        try:
            db = await self._get_db()
            
            # 获取所有股票基本信息
            basic_collection = db["stock_basic_info"]
            basic_cursor = basic_collection.find(
                {
                    "$or": [
                        {"category": "stock_cn"},
                        {"market": {"$in": ["主板", "创业板", "科创板", "北交所", "中小板"]}}
                    ]
                },
                projection={"_id": 0, "code": 1, "name": 1}
            )
            basic_stocks = await basic_cursor.to_list(length=10000)
            
            stock_name_map = {s["code"]: s.get("name", "") for s in basic_stocks}
            stock_codes = list(stock_name_map.keys())
            
            # 批量获取日线数据
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=240)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            quotes_collection = db["stock_daily_quotes"]
            quotes_cursor = quotes_collection.find(
                {
                    "code": {"$in": stock_codes},
                    "period": "daily",
                    "trade_date": {"$gte": start_date_str}
                },
                projection={"_id": 0, "code": 1, "trade_date": 1, "open": 1, "close": 1, "high": 1, "low": 1, "volume": 1}
            ).sort("trade_date", 1)
            
            all_quotes = await quotes_cursor.to_list(length=len(stock_codes) * 240)
            
            from collections import defaultdict
            quotes_by_stock = defaultdict(list)
            for quote in all_quotes:
                code = quote.get("code", "")
                if code:
                    quotes_by_stock[code].append(quote)
            
            # 提取各信号的可调参数（带默认值）
            # B1参数: BIAS60区间
            b1_bias_min = float(params.get("b1_bias_min", -40))
            b1_bias_max = float(params.get("b1_bias_max", -10))
            
            # B2参数: 放量倍数、突破均线选择、阳线涨幅
            b2_volume_ratio = float(params.get("b2_volume_ratio", 1.2))
            b2_price_change = float(params.get("b2_price_change", 0.03))
            b2_use_ma55 = params.get("b2_use_ma55", True)
            b2_use_ma60 = params.get("b2_use_ma60", True)
            
            # B3参数: BIAS60区间、MA13/MA55/MA60关系阈值
            b3_bias_min = float(params.get("b3_bias_min", -10))
            b3_bias_max = float(params.get("b3_bias_max", 10))
            b3_ma13_threshold = float(params.get("b3_ma13_threshold", 0.95))
            b3_price_vs_ma60 = float(params.get("b3_price_vs_ma60", 0.98))
            
            # S1参数: BIAS60上限
            s1_bias_min = float(params.get("s1_bias_min", 25))
            
            # S2参数: 跌破短期均线（MA5/MA8/MA13）
            s2_use_ma5 = params.get("s2_use_ma5", True)
            s2_use_ma8 = params.get("s2_use_ma8", True)
            s2_use_ma13 = params.get("s2_use_ma13", True)
            
            # S3参数: 跌破长期均线（MA55/MA60）、MA60趋势向下
            s3_use_ma55 = params.get("s3_use_ma55", True)
            s3_use_ma60 = params.get("s3_use_ma60", True)
            s3_trend_days = int(params.get("s3_trend_days", 5))
            
            results = []
            
            for code in stock_codes:
                price_data = quotes_by_stock.get(code, [])
                if len(price_data) < 60:
                    continue
                
                prices = [p["close"] for p in price_data]
                opens = [p.get("open", p["close"]) for p in price_data]
                volumes = [p.get("volume", 0) or 0 for p in price_data]
                volumes = [int(v) if isinstance(v, (int, float)) else 0 for v in volumes]
                stock_name = stock_name_map.get(code, "")
                current_price = prices[-1] if prices else 0.0
                
                # 计算所有均线
                ma_5 = self._calculate_moving_average(prices, 5)
                ma_8 = self._calculate_moving_average(prices, 8)
                ma_13 = self._calculate_moving_average(prices, 13)
                ma_55 = self._calculate_moving_average(prices, 55)
                ma_60 = self._calculate_moving_average(prices, 60)
                
                # 计算BIAS60
                bias_60 = self._calculate_bias(current_price, ma_60) if ma_60 else 0
                
                # 计算30天BIAS历史（用于B3）
                biases_30d = []
                for i in range(max(0, len(prices)-30), len(prices)):
                    ma_60_i = self._calculate_moving_average(prices[:i+1], 60) if i >= 59 else 0
                    if ma_60_i:
                        biases_30d.append(self._calculate_bias(prices[i], ma_60_i))
                
                # 计算MA60历史（用于S3趋势判断）
                ma_60_history = []
                for i in range(len(prices) - 60 + 1):
                    ma_60_history.append(self._calculate_moving_average(prices[i:i+60], 60))
                
                # ========== S3 互斥检测（与 scan_all_stocks_classified 逻辑一致）==========
                # 先检测 S3，若 S3 成立则屏蔽所有买入信号（B1/B2/B3）及 S1/S2
                s3_active = False
                if ma_55 and ma_60 and len(ma_60_history) >= s3_trend_days:
                    below_ma55_s3 = prices[-1] < ma_55 if s3_use_ma55 else True
                    below_ma60_s3 = prices[-1] < ma_60 if s3_use_ma60 else True
                    recent_ma60_s3 = ma_60_history[-s3_trend_days:]
                    ma60_slope_s3 = np.polyfit(range(len(recent_ma60_s3)), recent_ma60_s3, 1)[0] if len(recent_ma60_s3) >= 2 else 0
                    trend_down_s3 = ma60_slope_s3 < 0
                    s3_active = below_ma55_s3 and below_ma60_s3 and trend_down_s3

                # 信号检测（使用可配置参数 + S3 互斥）
                detected = False

                # 当 S3 成立时，B1/B2/B3/S1/S2 全部被屏蔽，只有当目标为 S3 时才继续
                if s3_active and signal_type != "S3":
                    continue

                if signal_type == "B1":
                    detected = b1_bias_min <= bias_60 <= b1_bias_max

                elif signal_type == "B2":
                    if len(prices) >= 2 and ma_55 and ma_60:
                        current_close = prices[-1]
                        prev_close = prices[-2]
                        current_open = opens[-1] if len(opens) >= len(prices) else prices[-1]
                        current_volume = volumes[-1] if volumes else 0
                        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
                        
                        volume_ok = current_volume >= avg_volume * b2_volume_ratio if avg_volume > 0 else False
                        prev_break = prev_close < ma_55 if b2_use_ma55 else True
                        if b2_use_ma55 and b2_use_ma60:
                            prev_break = prev_close < ma_55 or prev_close < ma_60
                        elif b2_use_ma60:
                            prev_break = prev_close < ma_60
                        
                        current_above = True
                        if b2_use_ma55 and b2_use_ma60:
                            current_above = current_close >= ma_55 and current_close >= ma_60
                        elif b2_use_ma55:
                            current_above = current_close >= ma_55
                        elif b2_use_ma60:
                            current_above = current_close >= ma_60
                        
                        yang = (current_close - current_open) / current_open >= b2_price_change if current_open > 0 else False
                        detected = volume_ok and current_above and prev_break and yang
                
                elif signal_type == "B3":
                    if ma_13 and ma_55 and ma_60:
                        ma13_ok = ma_13 > ma_55 * b3_ma13_threshold
                        bias_ok = b3_bias_min <= bias_60 <= b3_bias_max
                        has_positive = any(b >= 5 for b in biases_30d) if biases_30d else False
                        price_ok = len(prices) >= 2 and prices[-1] >= ma_60 * b3_price_vs_ma60
                        detected = ma13_ok and bias_ok and has_positive and price_ok
                
                elif signal_type == "S1":
                    detected = bias_60 >= s1_bias_min
                
                elif signal_type == "S2":
                    if len(prices) >= 2:
                        below_conditions_current = []
                        below_conditions_prev = []
                        if s2_use_ma5 and ma_5:
                            below_conditions_current.append(prices[-1] < ma_5)
                            below_conditions_prev.append(prices[-2] < ma_5)
                        if s2_use_ma8 and ma_8:
                            below_conditions_current.append(prices[-1] < ma_8)
                            below_conditions_prev.append(prices[-2] < ma_8)
                        if s2_use_ma13 and ma_13:
                            below_conditions_current.append(prices[-1] < ma_13)
                            below_conditions_prev.append(prices[-2] < ma_13)
                        if below_conditions_current:
                            detected = all(below_conditions_current) and all(below_conditions_prev)
                
                elif signal_type == "S3":
                    if len(prices) >= 2 and ma_55 and ma_60 and len(ma_60_history) >= s3_trend_days:
                        below_ma55 = prices[-1] < ma_55 if s3_use_ma55 else True
                        below_ma60 = prices[-1] < ma_60 if s3_use_ma60 else True
                        
                        recent_ma60 = ma_60_history[-s3_trend_days:]
                        ma60_slope = np.polyfit(range(len(recent_ma60)), recent_ma60, 1)[0] if len(recent_ma60) >= 2 else 0
                        trend_down = ma60_slope < 0
                        
                        detected = below_ma55 and below_ma60 and trend_down
                
                if detected:
                    results.append({
                        "code": code,
                        "name": stock_name,
                        "close": round(current_price, 2),
                        "ma_5": round(ma_5, 2) if ma_5 else None,
                        "ma_8": round(ma_8, 2) if ma_8 else None,
                        "ma_13": round(ma_13, 2) if ma_13 else None,
                        "ma_55": round(ma_55, 2) if ma_55 else None,
                        "ma_60": round(ma_60, 2) if ma_60 else None,
                        "bias_60": round(bias_60, 2),
                        "signal": signal_type,
                    })
            
            # 按BIAS60排序（最极端的排前面）
            if signal_type in ["B1", "B2", "B3"]:
                results.sort(key=lambda x: x["bias_60"])
            else:
                results.sort(key=lambda x: -x["bias_60"])
            
            logger.info(f"[{signal_type}] 参数筛选完成，找到 {len(results)} 只股票")
            return results[:500]
            
        except Exception as e:
            logger.error(f"按参数筛选股票失败 [{signal_type}]: {e}", exc_info=True)
            return []
    
    async def check_signal_alert(self, stock_code: str, last_checked_signals: List[str] = None) -> Optional[SignalAlert]:
        """
        检查股票是否有新的信号触发（用于监控）
        
        Args:
            stock_code: 股票代码
            last_checked_signals: 上次检查时的信号列表
        
        Returns:
            SignalAlert: 新信号告警，如果没有新信号则返回None
        """
        result = await self.calculate_signals(stock_code)
        
        if not last_checked_signals:
            last_checked_signals = []
        
        # 找出新出现的信号
        new_signals = [s for s in result.signals if s not in last_checked_signals]
        
        if not new_signals:
            return None
        
        # 判断信号强度
        signal_strength = "mild"
        if "S3" in new_signals:
            signal_strength = "critical"
        elif "S2" in new_signals or "B3" in new_signals:
            signal_strength = "strong"
        elif "S1" in new_signals or "B2" in new_signals:
            signal_strength = "strong"
        
        # 构建告警消息
        signal_names = {
            "B1": "左侧买点",
            "B2": "突破买点",
            "B3": "回踩买点",
            "S1": "加速卖点",
            "S2": "跌破卖点",
            "S3": "清仓卖点"
        }
        
        signal_descriptions = {
            "B1": "BIAS60进入[-30%,-20%]区间",
            "B2": "放量突破MA55/MA60",
            "B3": "回踩确认后放量上涨",
            "S1": "BIAS60超过阈值",
            "S2": "连续跌破MA5/MA8/MA13",
            "S3": "跌破MA55/MA60且趋势向下"
        }
        
        messages = []
        actions = []
        
        for signal in new_signals:
            messages.append(f"【{signal_names[signal]}】{signal_descriptions[signal]}")
            
            if signal.startswith("S"):
                if signal == "S3":
                    actions.append("全部清仓")
                elif signal == "S2":
                    actions.append("加大止盈")
                elif signal == "S1":
                    actions.append("部分止盈")
            else:
                if signal == "B3":
                    actions.append("加仓至满仓")
                elif signal == "B2":
                    actions.append("标准建仓")
                elif signal == "B1":
                    actions.append("小仓位试探")
        
        message = "、".join(messages)
        action = " / ".join(actions)
        
        return SignalAlert(
            stock_code=stock_code,
            stock_name=result.stock_name,
            new_signals=new_signals,
            signal_strength=signal_strength,
            message=message,
            action=action,
            timestamp=datetime.now()
        )
