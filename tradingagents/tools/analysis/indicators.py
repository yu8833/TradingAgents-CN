"""技术指标计算。

提供统一的技术指标计算接口，为选股和分析服务提供基础指标。
仅依赖 numpy 和 pandas，无额外第三方包。

支持的指标
----------
- MA   移动平均线
- EMA  指数移动平均线
- MACD 异同移动平均线 (DIF/DEA/MACD)
- RSI  相对强弱指数
- BOLL 布林带 (中轨/上轨/下轨)
- ATR  平均真实范围
- KDJ  随机指标
- 金叉/死叉信号派生
"""

import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ==========================================================================
# 指标规格
# ==========================================================================

class IndicatorSpec:
    """描述一个待计算指标：名称 + 参数。"""

    __slots__ = ("name", "params")

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}

    def __repr__(self) -> str:
        return f"IndicatorSpec(name={self.name!r}, params={self.params!r})"


# ==========================================================================
# 单个指标计算
# ==========================================================================

def compute_ma(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """简单移动平均线 (MA)。"""
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    return close.rolling(window=n, min_periods=1).mean()


def compute_ema(df: pd.DataFrame, n: int = 12) -> pd.Series:
    """指数移动平均线 (EMA)。"""
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    return close.ewm(span=n, adjust=False, min_periods=1).mean()


def compute_macd(
    df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> Dict[str, pd.Series]:
    """MACD (DIF, DEA, MACD-Histogram)。"""
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=1).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=1).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False, min_periods=1).mean()
    macd_hist = (dif - dea) * 2.0
    return {
        "dif": dif,
        "dea": dea,
        "macd_hist": macd_hist,
    }


def compute_rsi(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """相对强弱指数 (RSI)。"""
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=n, adjust=False, min_periods=1).mean()
    avg_loss = loss.ewm(span=n, adjust=False, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_vals = 100.0 - (100.0 / (1.0 + rs))
    # 第一行可能是 NaN，替换成 50 做中性处理
    return rsi_vals.fillna(50.0)


def compute_boll(df: pd.DataFrame, n: int = 20, k: float = 2.0) -> Dict[str, pd.Series]:
    """布林带 (中轨/上轨/下轨)。"""
    close = df["close"] if "close" in df.columns else df.iloc[:, 3]
    mid = close.rolling(window=n, min_periods=1).mean()
    std = close.rolling(window=n, min_periods=1).std().fillna(0.0)
    upper = mid + k * std
    lower = mid - k * std
    return {
        "boll_mid": mid,
        "boll_upper": upper,
        "boll_lower": lower,
    }


def compute_atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """平均真实范围 (ATR)。"""
    if "high" in df.columns and "low" in df.columns and "close" in df.columns:
        high = df["high"]
        low = df["low"]
        close = df["close"]
    else:
        high = df.iloc[:, 1]
        low = df.iloc[:, 2]
        close = df.iloc[:, 3]

    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(span=n, adjust=False, min_periods=1).mean()


def compute_kdj(
    df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3
) -> Dict[str, pd.Series]:
    """KDJ 指标 (K/D/J)。"""
    if "high" in df.columns and "low" in df.columns and "close" in df.columns:
        high = df["high"]
        low = df["low"]
        close = df["close"]
    else:
        high = df.iloc[:, 1]
        low = df.iloc[:, 2]
        close = df.iloc[:, 3]

    lowest_low = low.rolling(window=n, min_periods=1).min()
    highest_high = high.rolling(window=n, min_periods=1).max()

    rsv = ((close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)) * 100.0
    rsv = rsv.fillna(50.0)

    k = rsv.ewm(alpha=1.0 / m1, adjust=False, min_periods=1).mean()
    d = k.ewm(alpha=1.0 / m2, adjust=False, min_periods=1).mean()
    j = 3.0 * k - 2.0 * d

    return {"kdj_k": k, "kdj_d": d, "kdj_j": j}


def compute_cross_signals(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """根据已有列派生交叉信号 (MA 交叉 / MACD 金叉 / KDJ 金叉)。"""
    out: Dict[str, pd.Series] = {}

    idx = df.index if isinstance(df, pd.DataFrame) else pd.RangeIndex(len(df))

    def _make(values) -> pd.Series:
        if len(values) == len(idx):
            return pd.Series(values, index=idx)
        return pd.Series(values)

    # MA 金叉信号
    for ma_col in ("ma5", "ma10", "ma20", "ma60"):
        if ma_col in df.columns and "close" in df.columns:
            prev_ma = df[ma_col].shift(1).values
            prev_close = df["close"].shift(1).values
            curr = (df["close"].values >= df[ma_col].values) & (prev_close < prev_ma)
            out[f"{ma_col}_cross"] = _make(curr.astype(float))

    # MACD 金叉
    if "dif" in df.columns and "dea" in df.columns:
        prev_dif = df["dif"].shift(1).values
        prev_dea = df["dea"].shift(1).values
        golden = ((df["dif"].values >= df["dea"].values) & (prev_dif < prev_dea))
        out["macd_golden_fork"] = _make(golden.astype(float))

    # KDJ 金叉
    if "kdj_k" in df.columns and "kdj_d" in df.columns:
        prev_k = df["kdj_k"].shift(1).values
        prev_d = df["kdj_d"].shift(1).values
        kdj_golden = ((df["kdj_k"].values >= df["kdj_d"].values) & (prev_k < prev_d))
        out["kdj_golden_fork"] = _make(kdj_golden.astype(float))

    return out


# ==========================================================================
# 统一接口：一次性计算多个指标并合并到 DataFrame
# ==========================================================================

def compute_many(df: pd.DataFrame, specs: List[IndicatorSpec]) -> pd.DataFrame:
    """一次计算多个指标并返回新的 DataFrame (不修改输入)。

    参数
    ----
    df:   输入数据 (需要包含 open/high/low/close 或至少 close 列)。
    specs: 指标规格列表。

    返回
    ----
    新的 DataFrame，原数据列保持不变，新增各指标列。
    """
    if df is None:
        return pd.DataFrame()
    if len(df) == 0:
        return df.copy()

    result = df.copy()

    for spec in specs:
        name = str(spec.name).lower()
        params = spec.params or {}

        try:
            if name == "ma":
                n = int(params.get("n", 5))
                col = f"ma{n}"
                if col not in result.columns:
                    result[col] = compute_ma(result, n).values

            elif name == "ema":
                n = int(params.get("n", 12))
                col = f"ema{n}"
                if col not in result.columns:
                    result[col] = compute_ema(result, n).values

            elif name == "macd":
                fast = int(params.get("fast", 12))
                slow = int(params.get("slow", 26))
                signal = int(params.get("signal", 9))
                macd_res = compute_macd(result, fast, slow, signal)
                for k, v in macd_res.items():
                    if k not in result.columns:
                        result[k] = v.values

            elif name == "rsi":
                n = int(params.get("n", 14))
                col = f"rsi{n}"
                if col not in result.columns:
                    result[col] = compute_rsi(result, n).values

            elif name in ("boll", "bollinger"):
                n = int(params.get("n", 20))
                k = float(params.get("k", 2.0))
                boll_res = compute_boll(result, n, k)
                for k_name, v in boll_res.items():
                    if k_name not in result.columns:
                        result[k_name] = v.values

            elif name == "atr":
                n = int(params.get("n", 14))
                col = f"atr{n}"
                if col not in result.columns:
                    result[col] = compute_atr(result, n).values

            elif name == "kdj":
                n = int(params.get("n", 9))
                m1 = int(params.get("m1", 3))
                m2 = int(params.get("m2", 3))
                kdj_res = compute_kdj(result, n, m1, m2)
                for k_name, v in kdj_res.items():
                    if k_name not in result.columns:
                        result[k_name] = v.values

            # 未知指标类型：静默跳过

        except Exception:
            # 单个指标计算失败不影响整体流程
            continue

    # 基于已有指标列派生交叉信号
    for sig_col, vals in compute_cross_signals(result).items():
        if sig_col not in result.columns:
            result[sig_col] = vals.values

    return result


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """一次性添加全套常用指标。

    计算: MA5/10/20/60, EMA12/26, MACD, RSI14, BOLL, ATR14, KDJ,
         以及派生的交叉信号。
    """
    if df is None or len(df) == 0:
        return df.copy() if df is not None else pd.DataFrame()

    specs = [
        IndicatorSpec("ma", {"n": 5}),
        IndicatorSpec("ma", {"n": 10}),
        IndicatorSpec("ma", {"n": 20}),
        IndicatorSpec("ma", {"n": 60}),
        IndicatorSpec("ema", {"n": 12}),
        IndicatorSpec("ema", {"n": 26}),
        IndicatorSpec("macd"),
        IndicatorSpec("rsi", {"n": 14}),
        IndicatorSpec("boll", {"n": 20, "k": 2.0}),
        IndicatorSpec("atr", {"n": 14}),
        IndicatorSpec("kdj", {"n": 9, "m1": 3, "m2": 3}),
    ]
    return compute_many(df, specs)


# ==========================================================================
# 简化交互接口
# ==========================================================================

def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    """接受 pandas Series 的 RSI 快捷接口。"""
    df = pd.DataFrame({"close": pd.Series(series).reset_index(drop=True)})
    return compute_rsi(df, n)


__all__ = [
    "IndicatorSpec",
    "compute_many",
    "compute_ma",
    "compute_ema",
    "compute_macd",
    "compute_rsi",
    "compute_boll",
    "compute_atr",
    "compute_kdj",
    "add_all_indicators",
    "rsi",
]
