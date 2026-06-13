"""
Utility helpers for EnhancedScreeningService to separate analysis and conversion logic.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.screening import FieldType, BASIC_FIELDS_INFO


def analyze_conditions(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    analysis = {
        "total_conditions": len(conditions),
        "database_supported_conditions": 0,
        "technical_conditions": 0,
        "fundamental_conditions": 0,
        "basic_conditions": 0,
        "can_use_database": True,
        "needs_technical_indicators": False,
        "unsupported_fields": [],
        "condition_types": [],
    }

    supported_fields = set(BASIC_FIELDS_INFO.keys())

    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        field = condition.get("field")

        if field in supported_fields:
            field_info = BASIC_FIELDS_INFO[field]
            field_type = field_info.field_type

            if field_type == FieldType.BASIC:
                analysis["basic_conditions"] += 1
            elif field_type == FieldType.FUNDAMENTAL:
                analysis["fundamental_conditions"] += 1
            elif field_type == FieldType.TECHNICAL:
                analysis["technical_conditions"] += 1

            analysis["condition_types"].append(field_type.value)
            analysis["database_supported_conditions"] += 1
        else:
            analysis["can_use_database"] = False
            analysis["needs_technical_indicators"] = True
            analysis["unsupported_fields"].append(field)

    return analysis


def convert_conditions_to_traditional_format(conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    把 [{field, operator, value}, ...] 列表转为后端可统一评估的
    {logic, children} 树结构。每个叶子是 {'field':..., 'op':..., 'value':...}。
    这样 eval_utils.evaluate_conditions 能一致地走"叶子节点"分支，正确处理
    'between'/'eq' 等运算符以及 macd_golden_fork/ma20_cross 等标志字段。
    """
    if not conditions:
        return {"logic": "AND", "children": []}

    children: List[Dict[str, Any]] = []
    for c in conditions:
        if not isinstance(c, dict):
            continue
        # 规范化操作符
        op_raw = c.get("operator", "==")
        if isinstance(op_raw, str):
            op = op_raw.strip()
            if op in {"eq", "="}:
                op = "=="
            elif op in {"ne", "<>", "neq"}:
                op = "!="
            elif op in {"gte", "ge"}:
                op = ">="
            elif op in {"lte", "le"}:
                op = "<="
            elif op in {"gt"}:
                op = ">"
            elif op in {"lt"}:
                op = "<"
        else:
            op = str(op_raw) if op_raw is not None else "=="

        children.append({
            "field": c.get("field"),
            "op": op,
            "value": c.get("value"),
        })

    return {"logic": "AND", "children": children}

