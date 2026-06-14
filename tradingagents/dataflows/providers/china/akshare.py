"""AKShare Provider 兼容层"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_akshare_provider(*args, **kwargs):
    """获取AKShare提供者"""
    return AKShareProvider()


class AKShareProvider:
    """AKShare数据提供者（轻量级 - 不依赖 tushare 的 token 机制）"""

    def __init__(self, *args, **kwargs):
        self.connected = False
        self._akshare_module = None
        try:
            import akshare as ak
            self._akshare_module = ak
            self.connected = True
        except ImportError:
            logger.warning("[AKShare] akshare 库未安装，请在后端安装: pip install akshare")
        except Exception as e:
            logger.warning(f"[AKShare] 初始化失败: {e}")

    # ==================== 连接相关 ====================

    def connect_sync(self) -> bool:
        """同步连接测试"""
        try:
            import akshare as ak
            self._akshare_module = ak
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"[AKShare] 连接失败: {e}")
            self.connected = False
            return False

    async def connect(self) -> bool:
        """异步连接"""
        try:
            return await asyncio.to_thread(self.connect_sync)
        except Exception as e:
            logger.error(f"[AKShare] 异步连接失败: {e}")
            return False

    async def test_connection(self) -> bool:
        """测试连接 - 轻量测试，不发起网络请求"""
        try:
            # AKShare 不需要登录/token，只要模块能导入就算已连接
            if self._akshare_module is not None:
                self.connected = True
                return True
            return await self.connect()
        except Exception as e:
            logger.warning(f"[AKShare] 测试连接失败: {e}")
            return False

    def is_available(self) -> bool:
        return self._akshare_module is not None and self.connected

    def get_data(self, *args, **kwargs):
        return None

    # ==================== 数据获取方法（异步包裹同步调用） ====================

    async def get_stock_list(self, market: str = "CN"):
        """获取股票列表"""
        try:
            return await asyncio.to_thread(self._get_stock_list_sync)
        except Exception as e:
            logger.error(f"[AKShare] 获取股票列表失败: {e}")
            return None

    def _get_stock_list_sync(self):
        try:
            if not self.is_available():
                return []
            ak = self._akshare_module
            df = ak.stock_info_a_code_name()
            if df is None or df.empty:
                return []
            stocks = []
            for _, row in df.iterrows():
                code = str(row.get("code", row.get("symbol", ""))).strip().zfill(6)
                name = str(row.get("name", row.get("股票简称", ""))).strip()
                if code and name:
                    stocks.append({"code": code, "symbol": code, "name": name})
            return stocks
        except Exception as e:
            logger.error(f"[AKShare] 同步获取股票列表失败: {e}")
            return []

    async def get_stock_quotes(self, symbol: str):
        """获取单只股票实时行情"""
        try:
            symbol6 = str(symbol).strip().zfill(6)
            # 使用全市场快照然后筛选（比单股接口更稳定）
            quotes_map = await self.get_batch_stock_quotes([symbol6])
            if quotes_map and symbol6 in quotes_map:
                return quotes_map[symbol6]
            return None
        except Exception as e:
            logger.error(f"[AKShare] 获取 {symbol} 实时行情失败: {e}")
            return None

    async def get_batch_stock_quotes(self, symbols: List[str] = None):
        """获取批量股票的实时行情（通过全市场快照 + 筛选）"""
        try:
            return await asyncio.to_thread(self._get_batch_stock_quotes_sync, symbols)
        except Exception as e:
            logger.error(f"[AKShare] 批量获取实时行情失败: {e}")
            return None

    def _get_batch_stock_quotes_sync(self, symbols: List[str] = None):
        try:
            if not self.is_available():
                return {}
            ak = self._akshare_module
            try:
                df = ak.stock_zh_a_spot_em()
            except Exception as e1:
                logger.warning(f"[AKShare] 东方财富接口失败，尝试新浪接口: {e1}")
                df = ak.stock_zh_a_spot()
            if df is None or getattr(df, "empty", True):
                return {}

            code_col = next((c for c in ["代码", "code", "symbol", "股票代码"] if c in df.columns), None)
            price_col = next((c for c in ["最新价", "现价", "最新价(元)", "price", "最新", "trade"] if c in df.columns), None)
            pct_col = next((c for c in ["涨跌幅", "涨跌幅(%)", "涨幅", "pct_chg", "changepercent"] if c in df.columns), None)
            amount_col = next((c for c in ["成交额", "成交额(元)", "amount", "成交额(万元)"] if c in df.columns), None)
            open_col = next((c for c in ["今开", "开盘", "open", "今开(元)"] if c in df.columns), None)
            high_col = next((c for c in ["最高", "high"] if c in df.columns), None)
            low_col = next((c for c in ["最低", "low"] if c in df.columns), None)
            pre_close_col = next((c for c in ["昨收", "昨收(元)", "pre_close", "settlement"] if c in df.columns), None)
            volume_col = next((c for c in ["成交量", "成交量(手)", "volume", "成交量(股)"] if c in df.columns), None)

            if not code_col or not price_col:
                logger.error(f"[AKShare] 缺少必要列: code={code_col}, price={price_col}")
                return {}

            wanted = None
            if symbols:
                wanted = set(str(s).strip().zfill(6) for s in symbols)

            result: Dict[str, Dict[str, Any]] = {}
            for _, row in df.iterrows():
                code_raw = row.get(code_col)
                if not code_raw:
                    continue
                code_str = str(code_raw).strip()
                code_clean = ''.join(filter(str.isdigit, code_str)) or code_str
                code = code_clean.zfill(6)

                if wanted and code not in wanted:
                    continue

                def _sf(v):
                    try:
                        if v is None or (isinstance(v, float) and v != v):  # NaN
                            return None
                        f = float(v)
                        return f if -1e18 < f < 1e18 else None
                    except Exception:
                        return None

                close = _sf(row.get(price_col))
                pct = _sf(row.get(pct_col)) if pct_col else None
                amt = _sf(row.get(amount_col)) if amount_col else None
                op = _sf(row.get(open_col)) if open_col else None
                hi = _sf(row.get(high_col)) if high_col else None
                lo = _sf(row.get(low_col)) if low_col else None
                pre = _sf(row.get(pre_close_col)) if pre_close_col else None
                vol = _sf(row.get(volume_col)) if volume_col else None

                if vol is not None:
                    vol = vol * 100
                if amt is not None:
                    amt = amt / 10000.0

                result[code] = {
                    "code": code,
                    "symbol": code,
                    "close": close,
                    "pct_chg": pct,
                    "change_percent": pct,
                    "amount": amt,
                    "volume": vol,
                    "open": op,
                    "high": hi,
                    "low": lo,
                    "pre_close": pre,
                    "price": close,
                    "trade_date": datetime.now().strftime("%Y-%m-%d"),
                    "updated_at": datetime.utcnow(),
                }
            return result
        except Exception as e:
            logger.error(f"[AKShare] 批量获取实时行情(同步)失败: {e}")
            return {}

    async def get_stock_basic_info(self, symbol: str):
        """获取单只股票的基础信息"""
        try:
            return await asyncio.to_thread(self._get_stock_basic_info_sync, symbol)
        except Exception as e:
            logger.error(f"[AKShare] 获取 {symbol} 基础信息失败: {e}")
            return None

    def _get_stock_basic_info_sync(self, symbol: str):
        try:
            if not self.is_available():
                return None
            ak = self._akshare_module
            code = str(symbol).strip().zfill(6)
            try:
                df = ak.stock_individual_info_em(symbol=code)
                if df is not None and not df.empty:
                    info = {}
                    for _, row in df.iterrows():
                        k = str(row.iloc[0]) if hasattr(row, 'iloc') else str(row.get('item', ''))
                        v = row.iloc[1] if hasattr(row, 'iloc') else row.get('value', '')
                        info[k] = str(v)
                    return info
            except Exception:
                pass
            # 兜底：从股票列表中找
            stocks = self._get_stock_list_sync()
            for s in stocks:
                if s.get("code") == code:
                    return s
            return None
        except Exception as e:
            logger.warning(f"[AKShare] 获取基础信息失败: {e}")
            return None

    async def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily"):
        """获取历史K线数据"""
        try:
            return await asyncio.to_thread(self._get_historical_data_sync, symbol, start_date, end_date, period)
        except Exception as e:
            logger.error(f"[AKShare] 获取 {symbol} 历史数据失败: {e}")
            return None

    def _get_historical_data_sync(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily"):
        try:
            if not self.is_available():
                return None
            ak = self._akshare_module
            code = str(symbol).strip().zfill(6)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            else:
                start_date = start_date.replace("-", "")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            else:
                end_date = end_date.replace("-", "")

            try:
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            except Exception:
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
            if df is None or getattr(df, "empty", True):
                return None
            # 规范化列名以便 save_historical_data 统一处理
            col_map = {}
            for c in list(df.columns):
                col_map[c] = c
            # 确保常用列名存在：ts_code, trade_date, open, high, low, close, volume, amount
            if "ts_code" not in df.columns:
                df["ts_code"] = code
            return df
        except Exception as e:
            logger.warning(f"[AKShare] 获取历史K线失败: {e}")
            return None

    async def get_financial_data(self, symbol: str, limit: int = 5):
        """获取财务数据"""
        try:
            return await asyncio.to_thread(self._get_financial_data_sync, symbol, limit)
        except Exception as e:
            logger.error(f"[AKShare] 获取 {symbol} 财务数据失败: {e}")
            return None

    def _get_financial_data_sync(self, symbol: str, limit: int = 5):
        try:
            if not self.is_available():
                return []
            ak = self._akshare_module
            code = str(symbol).strip().zfill(6)
            try:
                df = ak.stock_financial_analysis_indicator(symbol=code)
            except Exception:
                return []
            if df is None or df.empty:
                return []
            records = []
            for i, (_, row) in enumerate(df.iterrows()):
                if i >= limit:
                    break
                r = {}
                for c in df.columns:
                    r[str(c)] = row[c]
                r["code"] = code
                records.append(r)
            return records
        except Exception as e:
            logger.warning(f"[AKShare] 获取财务数据失败: {e}")
            return []

    async def get_stock_news(self, symbol: str = None, limit: int = 50):
        """获取股票新闻"""
        try:
            return await asyncio.to_thread(self._get_stock_news_sync, symbol, limit)
        except Exception as e:
            logger.error(f"[AKShare] 获取 {symbol} 新闻失败: {e}")
            return []

    def _get_stock_news_sync(self, symbol: str = None, limit: int = 50):
        try:
            if not self.is_available():
                return []
            ak = self._akshare_module
            try:
                df = ak.stock_news_em()
            except Exception:
                return []
            if df is None or df.empty:
                return []
            records = []
            for _, row in df.iterrows():
                if len(records) >= limit:
                    break
                records.append({str(k): str(v) for k, v in row.to_dict().items()})
            return records
        except Exception as e:
            logger.warning(f"[AKShare] 获取新闻失败: {e}")
            return []
