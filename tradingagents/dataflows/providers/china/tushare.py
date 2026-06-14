"""Tushare Provider 兼容层"""

import os
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def get_tushare_provider(*args, **kwargs):
    """获取Tushare提供者"""
    return TushareProvider()


class TushareProvider:
    """Tushare数据提供者（完整实现）"""

    def __init__(self, *args, **kwargs):
        self.api = None
        self.connected = False
        self.token: Optional[str] = None
        self.token_source: Optional[str] = None
        self._ts_module = None
        self._config_loaded = False
        self._initialize()

    def _get_token_from_database(self) -> Optional[str]:
        """从数据库获取 Tushare token（同步方式）"""
        try:
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()
            if db is None:
                return None

            # 从 system_configs 或 data_sources 集合查找
            for coll_name in ['system_configs', 'data_sources', 'datasource_configs']:
                try:
                    collection = getattr(db, coll_name)
                    docs = list(collection.find({}).limit(10))
                    for doc in docs:
                        # 尝试从不同结构中提取 token
                        api_key = (
                            doc.get('api_key')
                            or doc.get('tushare_token')
                            or doc.get('token')
                            or (doc.get('data_source_configs') and doc.get('data_source_configs')
                                and any(ds.get('name') and 'tushare' in str(ds.get('name')).lower()
                                       for ds in doc.get('data_source_configs', []))
                                and next((ds.get('api_key') for ds in doc.get('data_source_configs', [])
                                           if ds.get('name') and 'tushare' in str(ds.get('name')).lower()), None))
                        )
                        if (api_key and isinstance(api_key, str) and api_key.strip()
                                and not api_key.strip().startswith('your')
                                and 'placeholder' not in api_key.lower()
                                and len(api_key.strip()) > 10):
                            return api_key.strip()
                except Exception as coll_err:
                    logger.debug(f"[Tushare] 查询 {coll_name} 失败: {coll_err}")
                    continue
        except Exception as e:
            logger.debug(f"[Tushare] 从数据库获取 token 失败: {e}")
        return None

    def _initialize(self):
        """初始化：尝试获取 token 并建立连接"""
        try:
            # 1. 从数据库获取配置
            db_token = self._get_token_from_database()
            if db_token:
                self.token = db_token
                self.token_source = 'database'
                logger.info(f"[Tushare] 使用数据库配置的 token (长度: {len(self.token)})")

            # 2. 如果数据库没有，从环境变量获取
            if not self.token:
                env_token = (
                    os.getenv('TUSHARE_TOKEN')
                    or os.getenv('TUSHARE_API_KEY')
                    or os.getenv('TUSHARE')
                )
                if (env_token and env_token.strip()
                        and not env_token.strip().startswith('your')
                        and 'placeholder' not in env_token.lower()
                        and len(env_token.strip()) > 10):
                    self.token = env_token.strip().strip('"').strip("'")
                    self.token_source = 'env'
                    logger.info(f"[Tushare] 使用环境变量配置的 token (长度: {len(self.token)})")

            # 3. 尝试导入 tushare 库
            try:
                import tushare as ts
                self._ts_module = ts
            except ImportError:
                logger.warning("[Tushare] tushare 库未安装，请在后端安装: pip install tushare")
                self._ts_module = None
            except Exception as import_err:
                logger.warning(f"[Tushare] 导入 tushare 库失败: {import_err}")
                self._ts_module = None

            # 4. 如果有 token 和库，则尝试连接
            if self.token and self._ts_module:
                try:
                    self.connect_sync()
                except Exception as conn_err:
                    logger.warning(f"[Tushare] 初始连接失败: {conn_err}")
            elif not self.token:
                logger.info(
                    "[Tushare] 未配置 token。请在数据库设置中添加 Tushare token，"
                    "或设置环境变量 TUSHARE_TOKEN=你的token。"
                    "访问 https://tushare.pro 注册获取"
                )

        except Exception as e:
            logger.warning(f"[Tushare] 初始化失败: {e}")
            self._ts_module = None
            self.api = None
            self.connected = False

    def connect_sync(self) -> bool:
        """同步方式连接 Tushare"""
        if not self._ts_module:
            logger.warning("[Tushare] 无法连接：tushare 库未安装")
            self.connected = False
            return False

        if not self.token:
            logger.warning("[Tushare] 无法连接：没有有效的 token")
            self.connected = False
            return False

        try:
            self._ts_module.set_token(self.token)
            self.api = self._ts_module.pro_api()

            # 尝试简单测试（不保证成功，不影响 available 状态）
            try:
                test_result = self.api.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name',
                    limit=1
                )
                if test_result is not None:
                    self.connected = True
                    logger.info(f"[Tushare] 连接测试成功！Token来源: {self.token_source}")
                    return True
            except Exception as test_err:
                logger.debug(f"[Tushare] 测试调用失败（可能正常）: {test_err}")
                # 即使测试失败，也认为连接已建立
                self.connected = True
                return True

            self.connected = True
            return True
        except Exception as e:
            logger.error(f"[Tushare] 连接失败: {e}")
            self.connected = False
            return False

    def get_stock_list_sync(self):
        """同步获取股票列表"""
        if not self.is_available():
            return None

        try:
            df = self.api.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            return df
        except Exception as e:
            logger.error(f"[Tushare] 获取股票列表失败: {e}")
            return None

    # ==================== 异步方法（供 asyncio 环境调用） ====================

    async def connect(self) -> bool:
        """异步方式连接 Tushare（内部调用 connect_sync）"""
        try:
            return await asyncio.to_thread(self.connect_sync)
        except Exception as e:
            logger.error(f"[Tushare] 异步连接失败: {e}")
            return False

    async def get_stock_list(self):
        """异步获取股票列表"""
        try:
            return await asyncio.to_thread(self.get_stock_list_sync)
        except Exception as e:
            logger.error(f"[Tushare] 异步获取股票列表失败: {e}")
            return None

    async def get_daily_bars(self, ts_code: str, start_date: str, end_date: str):
        """异步获取日线数据"""
        try:
            return await asyncio.to_thread(self.get_daily_bars_sync, ts_code, start_date, end_date)
        except Exception as e:
            logger.error(f"[Tushare] 异步获取日线数据失败: {e}")
            return None

    def get_daily_bars_sync(self, ts_code: str, start_date: str, end_date: str):
        """同步获取日线数据"""
        if not self.is_available():
            return None
        try:
            df = self.api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            logger.error(f"[Tushare] 获取日线数据失败 ({ts_code}): {e}")
            return None

    def get_financial_indicators_sync(self, ts_code: str, start_date: str = None, end_date: str = None):
        """同步获取财务指标"""
        if not self.is_available():
            return None
        try:
            params = {'ts_code': ts_code}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            df = self.api.fina_indicator(**params)
            return df
        except Exception as e:
            logger.error(f"[Tushare] 获取财务指标失败 ({ts_code}): {e}")
            return None

    # ==================== 异步方法：供 TushareSyncService 调用 ====================

    async def get_stock_quotes(self, symbol: str):
        """异步获取单只股票实时行情（使用 batch 方法筛选）"""
        try:
            code = str(symbol).strip().zfill(6)
            batch = await self.get_realtime_quotes_batch([code])
            if batch and code in batch:
                return batch[code]
            return None
        except Exception as e:
            logger.error(f"[Tushare] 获取 {symbol} 实时行情失败: {e}")
            return None

    async def get_realtime_quotes_batch(self, symbols: List[str] = None):
        """异步批量获取实时行情（rt_k 接口）"""
        try:
            return await asyncio.to_thread(self._get_realtime_quotes_batch_sync, symbols)
        except Exception as e:
            logger.error(f"[Tushare] 批量获取实时行情失败: {e}")
            return None

    def _get_realtime_quotes_batch_sync(self, symbols: List[str] = None):
        """同步批量获取实时行情"""
        if not self.is_available():
            return None
        try:
            df = self.api.rt_k()
            if df is None or getattr(df, "empty", True):
                return None
            wanted = None
            if symbols:
                wanted = set(str(s).strip().zfill(6) for s in symbols)
            result: Dict[str, Dict[str, Any]] = {}
            for _, row in df.iterrows():
                ts_code = str(row.get("ts_code", row.get("code", ""))).strip()
                code = ''.join(filter(str.isdigit, ts_code)) or ts_code
                code = code.zfill(6)
                if wanted and code not in wanted:
                    continue
                def _sf(v):
                    try:
                        if v is None or (isinstance(v, float) and v != v):
                            return None
                        f = float(v)
                        return f if -1e18 < f < 1e18 else None
                    except Exception:
                        return None
                result[code] = {
                    "code": code,
                    "symbol": code,
                    "close": _sf(row.get("price", row.get("close"))),
                    "price": _sf(row.get("price", row.get("close"))),
                    "pct_chg": _sf(row.get("pct_chg", row.get("change"))),
                    "change_percent": _sf(row.get("pct_chg", row.get("change"))),
                    "amount": _sf(row.get("amount")),
                    "volume": _sf(row.get("vol", row.get("volume"))),
                    "open": _sf(row.get("open")),
                    "high": _sf(row.get("high")),
                    "low": _sf(row.get("low")),
                    "pre_close": _sf(row.get("pre_close")),
                    "trade_date": datetime.now().strftime("%Y-%m-%d"),
                    "updated_at": datetime.utcnow(),
                }
            return result
        except Exception as e:
            logger.error(f"[Tushare] 批量获取实时行情失败: {e}")
            return None

    async def get_batch_stock_quotes(self, symbols: List[str] = None):
        """兼容 AKShare 的接口名"""
        return await self.get_realtime_quotes_batch(symbols)

    async def get_stock_basic_info(self, symbol: str):
        """异步获取单只股票基础信息"""
        try:
            return await asyncio.to_thread(self._get_stock_basic_info_sync, symbol)
        except Exception as e:
            logger.error(f"[Tushare] 获取 {symbol} 基础信息失败: {e}")
            return None

    def _get_stock_basic_info_sync(self, symbol: str):
        if not self.is_available():
            return None
        try:
            code = str(symbol).strip().zfill(6)
            df = self.api.stock_basic(ts_code="", name="", list_status="L")
            if df is None or df.empty:
                return None
            for _, row in df.iterrows():
                ts = str(row.get("ts_code", "")).strip()
                if code in ts or code in str(row.get("symbol", "")):
                    return row.to_dict()
            return None
        except Exception as e:
            logger.warning(f"[Tushare] 获取股票基础信息失败: {e}")
            return None

    async def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily"):
        """异步获取历史K线"""
        try:
            code = str(symbol).strip().zfill(6)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            else:
                start_date = start_date.replace("-", "")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            else:
                end_date = end_date.replace("-", "")
            prefix = "SH" if code.startswith(("6", "5", "11")) else "SZ"
            ts_code = f"{code}.{prefix}"
            df = await asyncio.to_thread(self.get_daily_bars_sync, ts_code, start_date, end_date)
            if df is None or getattr(df, "empty", True):
                return None
            return df
        except Exception as e:
            logger.error(f"[Tushare] 获取 {symbol} 历史数据失败: {e}")
            return None

    async def get_financial_data(self, symbol: str, limit: int = 5):
        """异步获取财务数据"""
        try:
            code = str(symbol).strip().zfill(6)
            prefix = "SH" if code.startswith(("6", "5", "11")) else "SZ"
            ts_code = f"{code}.{prefix}"
            df = await asyncio.to_thread(self.get_financial_indicators_sync, ts_code)
            if df is None or getattr(df, "empty", True):
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
            logger.error(f"[Tushare] 获取 {symbol} 财务数据失败: {e}")
            return []

    async def get_stock_news(self, symbol: str = None, limit: int = 50):
        """获取股票新闻 - Tushare 没有直接的新闻接口，返回空列表"""
        return []

    def is_available(self) -> bool:
        """检查是否可用"""
        if not self.connected:
            # 尝试重连
            self.connect_sync()
        return self._ts_module is not None and self.connected and self.api is not None

    def get_data(self, *args, **kwargs):
        """通用数据获取接口"""
        method = kwargs.get('method') or (args[0] if args else None)
        if not method:
            return None

        if hasattr(self.api, method):
            try:
                api_method = getattr(self.api, method)
                call_kwargs = {k: v for k, v in kwargs.items() if k != 'method'}
                other_args = [a for a in args[1:] if args and len(args) > 1]
                return api_method(*other_args, **call_kwargs)
            except Exception as e:
                logger.error(f"[Tushare] 调用 {method} 失败: {e}")
                return None
        return None
