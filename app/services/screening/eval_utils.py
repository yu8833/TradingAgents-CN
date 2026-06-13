"""
Utility functions for screening evaluation and DSL parsing.
Extracted from ScreeningService to separate concerns while keeping API unchanged.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Iterable
import pandas as pd
import numpy as np


# 标志字段集（技术信号类筛选）
FLAG_FIELDS = frozenset({
    "macd_golden_fork", "kdj_golden_fork",
    "ma5_cross", "ma10_cross", "ma20_cross", "ma60_cross",
})


def _normalize_op(op: Any) -> str:
    """归一化操作符：把 'eq'/'ne' 等常见别名统一成规范形式。"""
    if not isinstance(op, str):
        return ""
    o = op.strip().lower()
    if o in {"eq", "="}:
        return "=="
    if o in {"ne", "<>", "neq"}:
        return "!="
    if o in {"gte", "ge"}:
        return ">="
    if o in {"lte", "le"}:
        return "<="
    if o in {"gt"}:
        return ">"
    if o in {"lt"}:
        return "<"
    return o


def _is_group(node: Dict[str, Any]) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("op") == "group":
        return True
    if "children" in node and isinstance(node.get("children"), (list, tuple)):
        return True
    return False


def collect_fields_from_conditions(node: Dict[str, Any], allowed_fields: Iterable[str]) -> List[str]:
    if not node:
        return []

    allowed = set(allowed_fields)

    # group 节点：递归收集
    if _is_group(node):
        fields: List[str] = []
        for c in node.get("children", []) or []:
            fields.extend(collect_fields_from_conditions(c, allowed))
        return list(dict.fromkeys(fields))

    # 叶子节点：支持两种格式
    # (a) {"field": "macd_golden_fork", "op": "eq", "value": True
    # (b) {"macd_golden_fork": True, "total_mv": ...}
    if isinstance(node, dict) and "field" in node:
        f = node.get("field")
        out: List[str] = []
        if isinstance(f, str):
            if f in allowed or f in FLAG_FIELDS:
                out.append(f)
        rf = node.get("right_field")
        if isinstance(rf, str) and (rf in allowed or rf in FLAG_FIELDS):
            out.append(rf)
        return out

    # 扁平字典
    if isinstance(node, dict):
        out2: List[str] = []
        for f in node.keys():
            if not isinstance(f, str):
                continue
            if f in allowed or f in FLAG_FIELDS:
                out2.append(f)
        return out2

    return []


def evaluate_fund_conditions(snap: Dict[str, Any], node: Dict[str, Any], fund_fields: Iterable[str]) -> bool:
    if not node:
        return True
    # group
    if _is_group(node):
        logic = (node.get("logic") or "AND").upper()
        children = node.get("children", []) or []
        flags = [evaluate_fund_conditions(snap, c, fund_fields) for c in children]
        if logic == "OR":
            return any(flags)
        return all(flags)
    # leaf: {"field": ..., "op": ..., "value": ...}
    field = node.get("field") if isinstance(node, dict) and "field" in node else None
    if field is not None:
        op = _normalize_op(node.get("op"))
        if field not in set(fund_fields):
            return True  # 非基本面字段在纯基本面路径中跳过
        left = snap.get(field) if isinstance(snap, dict) else None
        if left is None or (isinstance(left, float) and np.isnan(left)):
            return False
        right = node.get("value")
        return _compare_values(left, op, right)

    # 扁平字典格式：键是字段名
    if isinstance(node, dict):
        for f, v in node.items():
            if f == "logic":
                continue
            if f not in set(fund_fields):
                    continue
            left = snap.get(f) if isinstance(snap, dict) else None
            if left is None or (isinstance(left, float) and np.isnan(left)):
                return False
            if not _compare_values(left, "==", v):
                return False
        return True
    return True


def _compare_values(left: Any, op: str, right: Any) -> bool:
    """统一的值比较（支持 between / == 等）。"""
    try:
        if op == "between":
            if not isinstance(right, (list, tuple)) or len(right) != 2:
                return False
            lo, hi = right
            if lo is None or hi is None:
                return False
            v = float(left)
            return float(lo) <= v <= float(hi)
        if op == "in":
            try:
                return left in right
            except Exception:
                return False
        if op == "not_in":
            try:
                return left not in right
            except Exception:
                return False
        if op == "contains":
            try:
                return str(right).lower() in str(left).lower()
            except Exception:
                return False
        # 数值比较
        if left is None or right is None:
            return False
        if isinstance(right, bool) or isinstance(left, bool):
            if op == "==":
                return bool(left) == bool(right)
            if op == "!=":
                return bool(left) != bool(right)
        lv = float(left)
        rv = float(right)
        if op == ">":
            return lv > rv
        if op == "<":
            return lv < rv
        if op == ">=":
            return lv >= rv
        if op == "<=":
            return lv <= rv
        if op == "==":
            return lv == rv
        if op == "!=":
            return lv != rv
    except Exception:
        return False
    return False


def evaluate_conditions(
    df: pd.DataFrame,
    node: Dict[str, Any],
    allowed_fields: Iterable[str],
    allowed_ops: Iterable[str],
) -> bool:
    if df is None or (hasattr(df, "empty") and df.empty):
        return False
    if not node:
        return True

    allowed = set(allowed_fields)
    allowed_opset = set(allowed_ops) | {"eq", "ne", "==", "!=", ">", "<", ">=", "<=", "between", "in", "not_in", "contains", "cross_up", "cross_down"}

    # group 节点
    if _is_group(node):
        logic = (node.get("logic") or "AND").upper()
        children = node.get("children", []) or []
        flags = [evaluate_conditions(df, c, allowed, allowed_opset) for c in children]
        if logic == "OR":
            return any(flags)
        return all(flags)

    # 叶子：字段比较（{"field":..., "op":..., "value": ...}
    if isinstance(node, dict) and "field" in node:
        field = node.get("field")
        op = _normalize_op(node.get("op"))
        right = node.get("value")

        # 标志字段（macd_golden_fork 等）：独立处理
        if isinstance(field, str) and field in FLAG_FIELDS:
            return _evaluate_flag(df, field, op, right)

        # 普通字段：检查字段/操作符
        if field not in allowed:
            return False
        if op not in allowed_opset:
            return False

        # 最近一行用于普通数值比较
        if df is None or (hasattr(df, "empty") and df.empty):
            return False

        # 交叉（需要两行情）
        if op in {"cross_up", "cross_down"}:
            right_field = node.get("right_field")
            if right_field not in allowed:
                return False
            if len(df) < 2:
                return False
            t0 = df.iloc[-1]
            t1 = df.iloc[-2]
            a0 = t0.get(field)
            a1 = t1.get(field)
            b0 = t0.get(right_field)
            b1 = t1.get(right_field)
            try:
                a0, a1, b0, b1 = float(a0), float(a1), float(b0), float(b1)
            except Exception:
                return False
            if op == "cross_up":
                return (a1 <= b1) and (a0 > b0)
            return (a1 >= b1) and (a0 < b0)

        # 普通比较（最近一根）
        t0 = df.iloc[-1]
        left = t0.get(field)
        if left is None or (isinstance(left, float) and np.isnan(left)):
            return False
        if node.get("right_field"):
            rf = node.get("right_field")
            if rf not in allowed:
                return False
            right = t0.get(rf)
        else:
            right = node.get("value")
        return _compare_values(left, op, right)

    # 扁平字典格式（旧/传统格式）
    if isinstance(node, dict):
        for f, v in node.items():
            if f == "logic":
                continue
            if isinstance(f, str) and f in FLAG_FIELDS:
                if not _evaluate_flag(df, f, "==", v):
                    return False
            elif isinstance(f, str) and f in allowed:
                if not _evaluate_simple_field(df, f, v):
                    return False
            # 未知字段：不通过
            else:
                return False
        return True

    return True


def _evaluate_flag(df: pd.DataFrame, field: str, op: str, right: Any) -> bool:
    """评估标志字段（macd_golden_fork / kdj_golden_fork / maXX_cross）"""
    if df is None or (hasattr(df, "empty") and df.empty) or len(df) < 2:
        # 站上均线仅需 1 根 K 线；金叉至少 2 根
        if field in {"ma5_cross", "ma10_cross", "ma20_cross", "ma60_cross"}:
            if df is None or (hasattr(df, "empty") and df.empty):
                return False
        else:
            return False

    want_true = (right is True or right == "true" or right == "True" or right == 1)

    # MACD 金叉：DIF 从下往上穿越 DEA
    if field == "macd_golden_fork":
        t0 = df.iloc[-1]
        t1 = df.iloc[-2] if len(df) >= 2 else t0
        try:
            dif0 = float(t0.get("dif")) if t0.get("dif") is not None else None
            dif1 = float(t1.get("dif")) if t1.get("dif") is not None else None
            dea0 = float(t0.get("dea")) if t0.get("dea") is not None else None
            dea1 = float(t1.get("dea")) if t1.get("dea") is not None else None
        except Exception:
            return False
        vals = (dif0, dif1, dea0, dea1)
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in vals):
            return False
        golden = (dif1 <= dea1) and (dif0 > dea0)
        return golden if want_true else not golden

    # KDJ 金叉：K 从下往上穿越 D
    if field == "kdj_golden_fork":
        t0 = df.iloc[-1]
        t1 = df.iloc[-2] if len(df) >= 2 else t0
        try:
            k0 = float(t0.get("kdj_k")) if t0.get("kdj_k") is not None else None
            k1 = float(t1.get("kdj_k")) if t1.get("kdj_k") is not None else None
            d0 = float(t0.get("kdj_d")) if t0.get("kdj_d") is not None else None
            d1 = float(t1.get("kdj_d")) if t1.get("kdj_d") is not None else None
        except Exception:
            return False
        vals_kdj = (k0, k1, d0, d1)
        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in vals_kdj):
            return False
        golden = (k1 <= d1) and (k0 > d0)
        return golden if want_true else not golden

    # 站上/跌破 N 日均线
    if field in {"ma5_cross", "ma10_cross", "ma20_cross", "ma60_cross"}:
        t0 = df.iloc[-1]
        try:
            close = float(t0.get("close")) if t0.get("close") is not None else None
            ma_key = field.replace("_cross", "")
            ma = float(t0.get(ma_key)) if t0.get(ma_key) is not None else None
        except Exception:
            return False
        if close is None or ma is None or (isinstance(close, float) and np.isnan(close)) or (isinstance(ma, float) and np.isnan(ma)):
            return False
        above = close > ma
        return above if want_true else not above

    return False


def _evaluate_simple_field(df: pd.DataFrame, field: str, value: Any) -> bool:
    """评估简单字段条件（扁平字典格式）：支持 {">": x / 直接数值相等"""
    if df is None or (hasattr(df, "empty") and df.empty):
        return False
    t0 = df.iloc[-1]
    left = t0.get(field)
    if left is None or (isinstance(left, float) and np.isnan(left)):
        return False
    try:
        if isinstance(value, dict):
            if "$gt" in value:
                return float(left) > float(value["$gt"])
            if "$lt" in value:
                return float(left) < float(value["$lt"])
            if "$gte" in value:
                return float(left) >= float(value["$gte"])
            if "$lte" in value:
                return float(left) <= float(value["$lte"])
            if "$eq" in value:
                return float(left) == float(value["$eq"])
            if "$ne" in value:
                return float(left) != float(value["$ne"])
            return False
        return float(left) == float(value)
    except (ValueError, TypeError):
        return False


def safe_float(v: Any) -> Optional[float]:
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return float(v)
    except Exception:
        return None

