"""
A股交易规则约束模块
实现A股市场的交易规则限制检查，包括涨跌停、T+1、最小买卖单位等
"""
import logging
import math
from datetime import datetime, time
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# 最小买卖单位（A股1手=100股）
LOT_SIZE = 100

# 涨跌停幅度配置
LIMIT_UP_CONFIG = {
    "main": 0.10,      # 主板（60开头）：±10%
    "star": 0.20,      # 科创板（688开头）：±20%
    "chinext": 0.20,   # 创业板（300开头）：±20%
    "st": 0.05,        # ST股：±5%
    "bse": 0.30,       # 北交所（8开头）：±30%
}

# 交易时段配置
TRADING_SESSIONS = [
    {"name": "上午竞价", "start": time(9, 15), "end": time(9, 25)},
    {"name": "上午交易", "start": time(9, 30), "end": time(11, 30)},
    {"name": "下午竞价", "start": time(13, 0), "end": time(13, 5)},
    {"name": "下午交易", "start": time(13, 0), "end": time(15, 0)},
]


def get_stock_type(ticker: str) -> str:
    """
    根据股票代码判断股票类型

    Args:
        ticker: 股票代码（6位）

    Returns:
        股票类型: main/star/chinext/st/bse/unknown
    """
    if not ticker:
        return "unknown"

    ticker = str(ticker).strip()

    # 科创板（688开头）
    if ticker.startswith("688"):
        return "star"
    # 创业板（300开头）
    elif ticker.startswith("300"):
        return "chinext"
    # 北交所（8开头）
    elif ticker.startswith("8"):
        return "bse"
    # 主板（60开头）
    elif ticker.startswith("60"):
        return "main"
    # 未知
    else:
        return "unknown"


def get_limit_percent(ticker: str, is_st: bool = False) -> float:
    """
    获取股票涨跌停幅度

    Args:
        ticker: 股票代码
        is_st: 是否为ST股（会被特殊处理）

    Returns:
        涨跌停幅度（小数，如0.10表示10%）
    """
    if is_st:
        return LIMIT_UP_CONFIG["st"]

    stock_type = get_stock_type(ticker)

    type_to_config = {
        "main": "main",
        "star": "star",
        "chinext": "chinext",
        "bse": "bse",
    }

    return LIMIT_UP_CONFIG.get(type_to_config.get(stock_type, "unknown"), 0.10)


def is_limit_up(ticker: str, current_price: float, trade_date: str) -> bool:
    """
    检查股票是否触及涨停板

    Args:
        ticker: 股票代码
        current_price: 当前价格
        trade_date: 交易日期（YYYY-MM-DD格式）

    Returns:
        是否触及涨停
    """
    try:
        pre_close = get_pre_close_price(ticker, trade_date)
        if pre_close is None or pre_close <= 0:
            logger.warning(f"⚠️ 无法获取{ticker}前一日收盘价")
            return False

        limit_percent = get_limit_percent(ticker)
        limit_up_price = round(pre_close * (1 + limit_percent), 2)

        # 价格达到涨停价（考虑浮点数精度）
        is_at_limit = abs(current_price - limit_up_price) < 0.01

        logger.info(
            f"📊 {ticker}涨停检查: 前收={pre_close}, 涨停价={limit_up_price}, "
            f"当前价={current_price}, 幅度={limit_percent*100:.1f}%, 触及涨停={is_at_limit}"
        )

        return is_at_limit

    except Exception as e:
        logger.error(f"❌ {ticker}涨停检查失败: {e}")
        return False


def is_limit_down(ticker: str, current_price: float, trade_date: str) -> bool:
    """
    检查股票是否触及跌停板

    Args:
        ticker: 股票代码
        current_price: 当前价格
        trade_date: 交易日期（YYYY-MM-DD格式）

    Returns:
        是否触及跌停
    """
    try:
        pre_close = get_pre_close_price(ticker, trade_date)
        if pre_close is None or pre_close <= 0:
            logger.warning(f"⚠️ 无法获取{ticker}前一日收盘价")
            return False

        limit_percent = get_limit_percent(ticker)
        limit_down_price = round(pre_close * (1 - limit_percent), 2)

        # 价格达到跌停价（考虑浮点数精度）
        is_at_limit = abs(current_price - limit_down_price) < 0.01

        logger.info(
            f"📊 {ticker}跌停检查: 前收={pre_close}, 跌停价={limit_down_price}, "
            f"当前价={current_price}, 幅度={limit_percent*100:.1f}%, 触及跌停={is_at_limit}"
        )

        return is_at_limit

    except Exception as e:
        logger.error(f"❌ {ticker}跌停检查失败: {e}")
        return False


def get_pre_close_price(ticker: str, trade_date: str) -> Optional[float]:
    """
    获取股票前一日收盘价

    Args:
        ticker: 股票代码
        trade_date: 交易日期（YYYY-MM-DD格式）

    Returns:
        前一日收盘价，如果获取失败返回None
    """
    try:
        # 优先使用akshare获取实时行情
        pre_close = _get_pre_close_akshare(ticker)
        if pre_close is not None:
            return pre_close

        # 回退到baostock获取历史数据
        pre_close = _get_pre_close_baostock(ticker, trade_date)
        if pre_close is not None:
            return pre_close

        logger.warning(f"⚠️ 无法获取{ticker}前一日收盘价")
        return None

    except Exception as e:
        logger.error(f"❌ 获取{ticker}前一日收盘价失败: {e}")
        return None


def _get_pre_close_akshare(ticker: str) -> Optional[float]:
    """使用akshare获取前一日收盘价"""
    try:
        import akshare as ak
        import pandas as pd

        # 获取实时行情快照
        spot_df = ak.stock_zh_a_spot_em()
        if spot_df is not None and not spot_df.empty:
            stock_data = spot_df[spot_df['代码'] == ticker]
            if not stock_data.empty:
                pre_close = float(stock_data.iloc[0]['昨收'])
                if pre_close > 0:
                    return pre_close

        # 回退：获取历史日线数据
        today = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now().replace(day=1) - pd.Timedelta(days=30)).strftime('%Y%m%d')

        hist_df = ak.stock_zh_a_hist(symbol=ticker, period="daily", start_date=start_date, end_date=today, adjust="")
        if hist_df is not None and not hist_df.empty:
            # 取最近一条历史数据的收盘价
            return float(hist_df.iloc[-2]['收盘'] if len(hist_df) >= 2 else hist_df.iloc[-1]['收盘'])

        return None

    except Exception as e:
        logger.debug(f"akshare获取{ticker}前收价失败: {e}")
        return None


def _get_pre_close_baostock(ticker: str, trade_date: str) -> Optional[float]:
    """使用baostock获取前一日收盘价"""
    try:
        import baostock as bs

        # 计算前一个交易日
        target_date = datetime.strptime(trade_date, '%Y-%m-%d')
        start_date = (target_date - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = trade_date

        # 转换股票代码格式
        bs_code = _to_baostock_code(ticker)

        lg = bs.login()
        if lg.error_code != '0':
            return None

        try:
            rs = bs.query_history_k_data_plus(
                code=bs_code,
                fields="date,close,preclose",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"
            )

            if rs.error_code != '0':
                return None

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return None

            # 取最后一条数据（最近交易日）的前收价
            latest = data_list[-1]
            if len(latest) >= 3 and latest[2] and float(latest[2]) > 0:
                return float(latest[2])

            return None

        finally:
            bs.logout()

    except Exception as e:
        logger.debug(f"baostock获取{ticker}前收价失败: {e}")
        return None


def _to_baostock_code(ticker: str) -> str:
    """转换为BaoStock代码格式"""
    ticker = str(ticker).strip()
    if ticker.startswith('6'):
        return f"sh.{ticker}"
    else:
        return f"sz.{ticker}"


def can_sell_today(ticker: str, buy_date: str, trade_date: str) -> Tuple[bool, str]:
    """
    检查T+1交易限制：今日买入的股票是否可卖出

    Args:
        ticker: 股票代码
        buy_date: 买入日期（YYYY-MM-DD格式）
        trade_date: 交易日期（YYYY-MM-DD格式）

    Returns:
        (是否可卖出, 原因说明)
    """
    try:
        # 解析日期
        buy_dt = datetime.strptime(buy_date, '%Y-%m-%d')
        trade_dt = datetime.strptime(trade_date, '%Y-%m-%d')

        # 计算日期差异
        days_diff = (trade_dt - buy_dt).days

        if days_diff == 0:
            # 今日买入
            reason = f"股票{ticker}为今日买入，T+1规则限制，当日不可卖出"
            logger.info(f"📋 {ticker} T+1检查: 买入日期={buy_date}, 交易日期={trade_date}, 不可卖出")
            return False, reason
        elif days_diff < 0:
            reason = f"股票{ticker}买入日期{buy_date}晚于交易日期{trade_date}，日期异常"
            logger.warning(f"⚠️ {ticker} T+1检查: {reason}")
            return False, reason
        else:
            # 持有一天以上，可以卖出
            reason = f"股票{ticker}已持有{days_diff}个交易日，T+1规则允许卖出"
            logger.info(f"📋 {ticker} T+1检查: 持有{days_diff}天，可卖出")
            return True, reason

    except ValueError as e:
        reason = f"日期格式错误: {e}"
        logger.error(f"❌ {ticker} T+1检查日期解析失败: {e}")
        return False, reason
    except Exception as e:
        reason = f"T+1检查异常: {str(e)}"
        logger.error(f"❌ {ticker} T+1检查失败: {e}")
        return False, reason


def adjust_to_lot_size(quantity: int, is_buy: bool = True) -> int:
    """
    调整交易数量到最小买卖单位

    A股最小买卖单位为100股（1手），买入必须整手，卖出可以零股

    Args:
        quantity: 原始交易数量
        is_buy: 是否为买入操作（买入时必须整手）

    Returns:
        调整后的交易数量
    """
    try:
        if quantity <= 0:
            logger.warning(f"⚠️ 数量{quantity}无效，返回0")
            return 0

        if is_buy:
            # 买入：向下取整到整手
            adjusted = (quantity // LOT_SIZE) * LOT_SIZE
            if adjusted == 0 and quantity > 0:
                logger.warning(f"⚠️ 买入数量{quantity}不足1手({LOT_SIZE}股)，调整为0")
                return 0
            if adjusted != quantity:
                logger.info(f"📊 买入数量调整: {quantity} -> {adjusted}（整手）")
            return adjusted
        else:
            # 卖出：保持原数量（可零股）
            logger.info(f"📊 卖出数量保持: {quantity}（可零股）")
            return quantity

    except Exception as e:
        logger.error(f"❌ 调整买卖单位失败: {e}")
        return 0


def is_trading_time() -> Tuple[bool, str]:
    """
    检查当前是否在A股交易时段

    A股交易时段：
    - 开盘前竞价：9:15-9:25
    - 上午交易：9:30-11:30
    - 下午竞价：13:00-13:05（仅深交所）
    - 下午交易：13:00-15:00

    Returns:
        (是否在交易时段, 当前可执行的操作说明)
    """
    try:
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()

        # 检查是否为工作日（周一到周五）
        if current_weekday >= 5:
            return False, "当前为周末，非交易日"

        # 9:15-9:25 开盘前竞价
        if time(9, 15) <= current_time <= time(9, 25):
            return True, "当前为开盘前竞价时段（9:15-9:25），可下单、撤单"

        # 9:30-11:30 上午交易
        if time(9, 30) <= current_time <= time(11, 30):
            return True, "当前为上午交易时段（9:30-11:30），可买卖"

        # 13:00-15:00 下午交易
        if time(13, 0) <= current_time <= time(15, 0):
            return True, "当前为下午交易时段（13:00-15:00），可买卖"

        # 其他时间
        if current_time < time(9, 15):
            return False, "当前为开盘前，非交易时段"
        elif time(9, 25) < current_time < time(9, 30):
            return False, "当前为集合竞价撮合时段（9:25-9:30），不可下单"
        elif time(11, 30) < current_time < time(13, 0):
            return False, "当前为午间休市（11:30-13:00）"
        else:
            return False, "当前为收盘后，非交易时段"

    except Exception as e:
        logger.error(f"❌ 交易时段检查失败: {e}")
        return False, f"交易时段检查异常: {str(e)}"


def can_buy_at_limit(ticker: str, current_price: float) -> Tuple[bool, str]:
    """
    检查涨停板时买入限制

    涨停板时买入会排队且成交概率极低，不建议追涨

    Args:
        ticker: 股票代码
        current_price: 当前价格

    Returns:
        (是否建议买入, 原因说明)
    """
    try:
        # 通过价格变动判断是否涨停
        pre_close = get_pre_close_price(ticker, datetime.now().strftime('%Y-%m-%d'))
        if pre_close is None or pre_close <= 0:
            return False, f"无法获取{ticker}前收盘价，无法判断"

        limit_percent = get_limit_percent(ticker)
        limit_up_price = round(pre_close * (1 + limit_percent), 2)

        # 判断是否涨停
        if abs(current_price - limit_up_price) < 0.01:
            reason = (
                f"{ticker}已涨停（价格={current_price}），"
                f"涨停板买入会挂单排队，成交概率极低，"
                f"建议等待打开涨停后再考虑买入"
            )
            logger.info(f"📋 {ticker}涨停买入建议: 不建议买入 - {reason}")
            return False, reason

        # 未涨停，检查涨幅
        change_percent = (current_price - pre_close) / pre_close * 100

        if change_percent >= 8:
            reason = (
                f"{ticker}涨幅已达{change_percent:.1f}%，处于高位，"
                f"追涨风险较大，建议谨慎"
            )
            logger.info(f"📋 {ticker}高位买入建议: 谨慎 - {reason}")
            return False, reason

        reason = f"{ticker}当前价格{current_price}，未触及涨停，可正常买入"
        logger.info(f"📋 {ticker}买入建议: 可买入 - {reason}")
        return True, reason

    except Exception as e:
        logger.error(f"❌ {ticker}涨停买入检查失败: {e}")
        return False, f"检查异常: {str(e)}"


def can_sell_at_limit(ticker: str, current_price: float) -> Tuple[bool, str]:
    """
    检查跌停板时卖出限制

    跌停板时卖出无法成交，应等待打开跌停

    Args:
        ticker: 股票代码
        current_price: 当前价格

    Returns:
        (是否建议卖出, 原因说明)
    """
    try:
        # 通过价格变动判断是否跌停
        pre_close = get_pre_close_price(ticker, datetime.now().strftime('%Y-%m-%d'))
        if pre_close is None or pre_close <= 0:
            return False, f"无法获取{ticker}前收盘价，无法判断"

        limit_percent = get_limit_percent(ticker)
        limit_down_price = round(pre_close * (1 - limit_percent), 2)

        # 判断是否跌停
        if abs(current_price - limit_down_price) < 0.01:
            reason = (
                f"{ticker}已跌停（价格={current_price}），"
                f"跌停板卖出无法成交，"
                f"建议等待打开跌停后再考虑卖出"
            )
            logger.info(f"📋 {ticker}跌停卖出建议: 不建议卖出 - {reason}")
            return False, reason

        # 未跌停，检查跌幅
        change_percent = (current_price - pre_close) / pre_close * 100

        if change_percent <= -8:
            reason = (
                f"{ticker}跌幅已达{change_percent:.1f}%，处于低位，"
                f"杀跌风险较大，建议谨慎"
            )
            logger.info(f"📋 {ticker}低位卖出建议: 谨慎 - {reason}")
            return False, reason

        reason = f"{ticker}当前价格{current_price}，未触及跌停，可正常卖出"
        logger.info(f"📋 {ticker}卖出建议: 可卖出 - {reason}")
        return True, reason

    except Exception as e:
        logger.error(f"❌ {ticker}跌停卖出检查失败: {e}")
        return False, f"检查异常: {str(e)}"


def get_trading_suggestion(
    ticker: str,
    action: str,
    quantity: int,
    current_price: float,
    trade_date: str,
    buy_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    综合交易约束检查，返回交易建议

    Args:
        ticker: 股票代码
        action: 交易动作（"buy" 或 "sell"）
        quantity: 交易数量
        current_price: 当前价格
        trade_date: 交易日期（YYYY-MM-DD格式）
        buy_date: 买入日期（YYYY-MM-DD格式），仅卖出时需要

    Returns:
        交易建议字典，包含：
        - can_trade: 是否可执行交易
        - adjusted_quantity: 调整后的交易数量
        - warnings: 风险提示列表
        - suggestions: 建议列表
        - limit_info: 涨跌停信息
        - trading_time_info: 交易时段信息
    """
    result = {
        "can_trade": True,
        "adjusted_quantity": quantity,
        "warnings": [],
        "suggestions": [],
        "limit_info": {},
        "trading_time_info": {},
        "ticker": ticker,
        "action": action,
        "original_quantity": quantity,
        "current_price": current_price,
        "trade_date": trade_date,
    }

    try:
        # 1. 涨跌停检查
        limit_percent = get_limit_percent(ticker)
        pre_close = get_pre_close_price(ticker, trade_date)

        if pre_close is not None and pre_close > 0:
            limit_up_price = round(pre_close * (1 + limit_percent), 2)
            limit_down_price = round(pre_close * (1 - limit_percent), 2)

            result["limit_info"] = {
                "pre_close": pre_close,
                "limit_up_price": limit_up_price,
                "limit_down_price": limit_down_price,
                "limit_percent": limit_percent * 100,
                "is_limit_up": abs(current_price - limit_up_price) < 0.01,
                "is_limit_down": abs(current_price - limit_down_price) < 0.01,
            }

        # 2. 交易时段检查
        in_trading_time, time_msg = is_trading_time()
        result["trading_time_info"] = {
            "in_trading_time": in_trading_time,
            "message": time_msg,
        }

        if not in_trading_time:
            result["can_trade"] = False
            result["warnings"].append(f"非交易时段: {time_msg}")

        # 3. 数量调整
        if action.lower() == "buy":
            adjusted_qty = adjust_to_lot_size(quantity, is_buy=True)
        else:
            adjusted_qty = adjust_to_lot_size(quantity, is_buy=False)

        result["adjusted_quantity"] = adjusted_qty

        if adjusted_qty == 0 and quantity > 0:
            result["can_trade"] = False
            result["warnings"].append(f"调整后数量为0，无法{action}")

        # 4. 涨跌停相关限制
        if action.lower() == "buy":
            can_buy, buy_msg = can_buy_at_limit(ticker, current_price)
            if not can_buy:
                result["warnings"].append(buy_msg)
                # 涨停买入不直接阻止，但给出警告
                result["suggestions"].append("如需买入，建议等待打开涨停")

        elif action.lower() == "sell":
            # T+1检查
            if buy_date:
                can_sell, sell_msg = can_sell_today(ticker, buy_date, trade_date)
                if not can_sell:
                    result["can_trade"] = False
                    result["warnings"].append(sell_msg)
                    result["suggestions"].append(f"如需卖出，需等到{buy_date}之后的交易日")

            can_sell, sell_msg = can_sell_at_limit(ticker, current_price)
            if not can_sell:
                result["warnings"].append(sell_msg)
                # 跌停卖出不直接阻止，但给出警告
                result["suggestions"].append("如需卖出，建议等待打开跌停")

        # 5. 涨跌停状态提示
        if result["limit_info"].get("is_limit_up"):
            result["suggestions"].append(
                f"股票{ticker}已涨停，{'不建议追涨买入' if action.lower() == 'buy' else '卖出需排队等待'}"
            )
        elif result["limit_info"].get("is_limit_down"):
            result["suggestions"].append(
                f"股票{ticker}已跌停，{'买入需排队等待' if action.lower() == 'buy' else '不建议杀跌卖出'}"
            )

        # 6. 生成最终建议
        if result["can_trade"] and result["adjusted_quantity"] > 0:
            result["final_suggestion"] = f"可执行{action}交易，调整后数量={result['adjusted_quantity']}"
        else:
            result["final_suggestion"] = f"不建议执行{action}交易"

        logger.info(
            f"📋 {ticker} {action}交易建议: can_trade={result['can_trade']}, "
            f"quantity={result['adjusted_quantity']}, warnings={result['warnings']}"
        )

        return result

    except Exception as e:
        logger.error(f"❌ {ticker}综合交易建议生成失败: {e}")
        result["can_trade"] = False
        result["warnings"].append(f"交易建议生成异常: {str(e)}")
        result["final_suggestion"] = "交易建议生成失败，请手动确认"
        return result


def check_stock_is_st(ticker: str) -> bool:
    """
    检查股票是否为ST股（特别处理股）

    Args:
        ticker: 股票代码

    Returns:
        是否为ST股
    """
    try:
        # 尝试获取股票名称判断是否ST
        stock_name = get_stock_name(ticker)
        if stock_name and ("ST" in stock_name or "*ST" in stock_name):
            return True
        return False
    except Exception as e:
        logger.debug(f"检查{ticker}是否为ST股失败: {e}")
        return False


def get_stock_name(ticker: str) -> Optional[str]:
    """
    获取股票名称

    Args:
        ticker: 股票代码

    Returns:
        股票名称
    """
    try:
        import akshare as ak

        spot_df = ak.stock_zh_a_spot_em()
        if spot_df is not None and not spot_df.empty:
            stock_data = spot_df[spot_df['代码'] == ticker]
            if not stock_data.empty:
                return str(stock_data.iloc[0]['名称'])

        return None
    except Exception as e:
        logger.debug(f"获取{ticker}名称失败: {e}")
        return None
