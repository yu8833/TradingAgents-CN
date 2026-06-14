"""
分析报告管理API路由
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .auth_db import get_current_user
from ..core.database import get_mongo_db
from ..utils.timezone import to_config_tz
import logging
import re

logger = logging.getLogger("webapi")

# ============================================================
# 报告结构化字段抽取：从多份子报告 markdown 中解析核心字段
# ============================================================

# 用于从一段文本中抽取指定“章节”后的内容（支持多种标题格式）
# 格式匹配： `**N. 标题**`, `N. **标题**`, `**标题**`，或纯中文如 `核心洞察`
_SECTION_HEADERS = [
    # (优先级从高到低；(name_aliases, 输出字段名, 最大保留字符数))
    (["核心洞察"], "核心洞察", 1200),
    (["投资逻辑"], "投资逻辑", 1200),
    (["趋势预测"], "趋势预测", 1200),
    (["策略点位"], "策略点位", 1500),
    (["风险提示"], "风险提示", 800),
    (["核心理由", "操作建议理由"], "操作建议理由", 800),
]

# 数值 / 价格类字段的别名
_PRICE_FIELDS = [
    (["理想买入"], "理想买入"),
    (["二次买入"], "二次买入"),
    (["止损价格", "止损位", "止损线"], "止损价格"),
    (["止盈目标", "目标价格", "目标价"], "止盈目标"),
    (["支撑位", "支撑"], "支撑位"),
    (["阻力位", "压力位"], "阻力位"),
]

_SCORE_FIELDS = [
    (["置信度"], "置信度"),
    (["风险等级"], "风险等级"),
    (["技术面评分"], "技术面评分"),
    (["基本面评分"], "基本面评分"),
    (["情绪面评分"], "情绪面评分"),
    (["政策面评分"], "政策面评分"),
]


def _iter_text(reports: Dict[str, Any]):
    """依次取出 reports 中所有字符串子报告，按优先级排序"""
    order = [
        "final_trade_decision", "trader_investment_plan",
        "investment_plan", "research_team_decision",
        "risk_management_decision",
    ]
    for key in order:
        v = reports.get(key)
        if isinstance(v, str):
            yield v
    for k, v in reports.items():
        if k not in order and isinstance(v, str):
            yield v


def _match_price(text: str, aliases: List[str]) -> Optional[str]:
    """
    在文本中查找诸如 `理想买入\n10.70 元` 或 `7. 支撑位：10.88元` 的价格。
    返回价格字符串（如 "10.70 元"），找不到返回 None。
    """
    if not text:
        return None

    for alias in aliases:
        # 尝试 "N. 名称：价格 元（注释）"
        pattern1 = re.compile(
            r"(?:^|\n)\s*\*?\s*(?:\d+[\.、]\s*)?\*?\s*" + re.escape(alias) +
            r"\s*\*?\s*[:：]\s*([^\n，。；,;（(]{0,80})",
        )
        m = pattern1.search(text)
        if m:
            val = m.group(1).strip()
            if "不适用" in val:
                continue
            num = re.search(r"(\d+(?:\.\d+)?)", val)
            if num:
                return f"{num.group(1)} 元"
            if val and len(val) < 40:
                return val

        # 尝试单独行：`**8. 止盈目标**` / `**6. 理想买入**` 之后跟着一行价格
        pattern2 = re.compile(
            r"(?:^|\n)\s*\*+\s*(?:\d+[\.、]\s*)?" + re.escape(alias) +
            r"\s*\*+\s*\n\s*([^\n，。；,;（(]{0,80})",
        )
        m = pattern2.search(text)
        if m:
            val = m.group(1).strip(" *\n")
            if "不适用" in val:
                continue
            num = re.search(r"(\d+(?:\.\d+)?)", val)
            if num:
                return f"{num.group(1)} 元"
            if val and len(val) < 40:
                return val

        # 简化版：在一段内出现 `名称：数值元`
        pattern3 = re.compile(
            re.escape(alias) + r"\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:元|块)?",
        )
        m = pattern3.search(text)
        if m:
            return f"{m.group(1)} 元"

    return None


def _match_score(text: str, aliases: List[str]) -> Optional[str]:
    """从文本中抽取类似 `置信度：0.75` 或 `**11. 置信度**`\n0.75 的数值"""
    if not text:
        return None
    lines = text.split("\n")
    n = len(lines)

    for alias in aliases:
        # 方式 A：在一行内出现 "名称：数值"（支持列表项前缀 `-`/`*`）
        for line in lines:
            stripped = line.strip().strip("* \t-*•")
            # "置信度：0.75" / "置信度 0.75" / "- 技术面评分：0.55（注释）"
            m = re.match(
                r"(?:\d+[\.、]\s*)?" + re.escape(alias) +
                r"\s*[:：]\s*(-?\d+(?:\.\d+)?|高|中|低|中等|较高|较低)\b",
                stripped,
            )
            if m:
                return m.group(1)

        # 方式 B：标题行 + 下一行是数字
        for i, line in enumerate(lines):
            stripped = line.strip().strip("*")
            if alias in stripped:
                # 只允许标题形式
                normalized = stripped.strip("* \t")
                if re.match(r"^\d*[\.、]?\s*" + re.escape(alias) + r"\s*$", normalized):
                    for j in range(i + 1, min(i + 3, n)):
                        next_line = lines[j].strip().strip("* \t-•")
                        if not next_line:
                            continue
                        m = re.match(
                            r"(-?\d+(?:\.\d+)?|高|中|低|中等|较高|较低)\b",
                            next_line,
                        )
                        if m:
                            return m.group(1)
                        break
                    break

    return None


def _extract_section(text: str, aliases: List[str], max_chars: int) -> Optional[str]:
    """从文本中抽取 "**N. 核心洞察**" 或 "2. 核心洞察" 之后，到下一个同级别标题前的段落"""
    if not text:
        return None

    def is_heading_line(line: str) -> bool:
        """判断是否为类似 `**N. 标题**` 或 `N. 标题` 的行"""
        s = line.strip()
        s = s.strip("* \t")
        return bool(re.match(r"^\d+[\.、]\s*.{1,30}$", s))

    lines = text.split("\n")
    n = len(lines)
    # 寻找包含任意 alias 的标题行
    start_idx = None
    matched_alias = None
    for i, line in enumerate(lines):
        stripped = line.strip().strip("* \t")
        if not stripped:
            continue
        for alias in aliases:
            if alias in stripped:
                # 检查是否在一个标题行内
                # 格式 1：`**2. 核心洞察**` 或 `**核心洞察**`
                # 格式 2：`2. 核心洞察`
                if (re.match(r"^\*+\s*\d*[\.、]?\s*" + re.escape(alias) + r"\s*\*+", line.strip())
                        or re.match(r"^\d+[\.、]\s*" + re.escape(alias) + r"$", stripped)
                        or stripped == alias):
                    start_idx = i
                    matched_alias = alias
                    break
        if start_idx is not None:
            break

    if start_idx is None:
        return None

    # 从 start_idx 的下一行开始收集，直到遇到下一个同级别标题或文本结尾
    collected = []
    for j in range(start_idx + 1, n):
        line = lines[j]
        if is_heading_line(line):
            break
        # 标题之后的第一个空行可以忽略
        if not collected and not line.strip():
            continue
        collected.append(line)

    content = "\n".join(collected).strip()
    # 清理 markdown 加粗符号
    content = re.sub(r"\*+", "", content).strip()
    # 去除开头多余的冒号/破折号
    content = content.lstrip("：:-— ").strip()
    if not content:
        return None
    if len(content) > max_chars:
        content = content[:max_chars] + "…"
    return content


def extract_structured_fields(reports: Dict[str, Any]) -> Dict[str, Any]:
    """
    遍历 reports 中的所有子报告，抽取可用于前端展示的结构化字段。
    字段会被合并到报告详情顶层，以便前端 `pickField(report, [...])` 工作。
    """
    result: Dict[str, Any] = {}
    if not isinstance(reports, dict) or not reports:
        return result

    combined_text = "\n".join(t for t in _iter_text(reports))

    # 1) 文本型章节（核心洞察/投资逻辑/趋势预测/策略点位/风险提示）
    for aliases, field_name, max_chars in _SECTION_HEADERS:
        for sub in _iter_text(reports):
            val = _extract_section(sub, aliases, max_chars)
            if val and not result.get(field_name):
                result[field_name] = val
                break

    # 2) 价格型字段
    for aliases, field_name in _PRICE_FIELDS:
        for sub in _iter_text(reports):
            val = _match_price(sub, aliases)
            if val:
                result[field_name] = val
                # 同时写入便于前端 pickField 回退的字段名
                result[field_name + "_raw"] = val
                break

    # 2a) target_price / stop_loss 英文字段兼容（方便 trading_graph 侧使用）
    if "止盈目标" in result:
        num = re.search(r"(\d+(?:\.\d+)?)", result["止盈目标"])
        if num:
            result["target_price"] = num.group(1)
    if "止损价格" in result:
        num = re.search(r"(\d+(?:\.\d+)?)", result["止损价格"])
        if num:
            result["stop_loss"] = num.group(1)

    # 3) 评分型字段（置信度/风险等级/技术面评分 等）
    for aliases, field_name in _SCORE_FIELDS:
        for sub in _iter_text(reports):
            val = _match_score(sub, aliases)
            if val:
                result[field_name] = val
                break

    # 4) 评级/操作建议：从文本中找 "1. 评级：减仓" 或 "操作建议：卖出"
    for sub in _iter_text(reports):
        for head in ["操作建议", "评级", "rating", "Rating", "RATING"]:
            # 尝试冒号型
            m = re.search(re.escape(head) + r"\s*[：:]\s*([^\n，。；,;]{0,40})", sub)
            if m:
                val = m.group(1).strip(" *\n")
                if val and "result" not in val.lower():
                    result["评级"] = val
                    if "操作建议" not in result:
                        result["操作建议"] = val
                    break
            # 或单独行型： **1. 评级**\n减仓
            sect = _extract_section(sub, [head], 80)
            if sect and not result.get("评级"):
                result["评级"] = sect
                result["操作建议"] = sect
                break
        if result.get("评级"):
            break

    return result


# 股票名称缓存
_stock_name_cache = {}

def get_stock_name(stock_code: str) -> str:
    """
    获取股票名称
    优先级：缓存 -> MongoDB（按数据源优先级） -> 默认返回股票代码
    """
    global _stock_name_cache

    # 检查缓存
    if stock_code in _stock_name_cache:
        return _stock_name_cache[stock_code]

    try:
        # 从 MongoDB 获取股票名称
        from ..core.database import get_mongo_db_sync
        from ..core.unified_config import UnifiedConfigManager

        db = get_mongo_db_sync()
        code6 = str(stock_code).zfill(6)

        # 🔥 按数据源优先级查询
        config = UnifiedConfigManager()
        data_source_configs = config.get_data_source_configs()

        # 提取启用的数据源，按优先级排序
        enabled_sources = [
            ds.type.lower() for ds in data_source_configs
            if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
        ]

        if not enabled_sources:
            enabled_sources = ['tushare', 'akshare', 'baostock']

        # 按数据源优先级查询
        stock_info = None
        for data_source in enabled_sources:
            stock_info = db.stock_basic_info.find_one(
                {"$or": [{"symbol": code6}, {"code": code6}], "source": data_source}
            )
            if stock_info:
                logger.debug(f"✅ 使用数据源 {data_source} 获取股票名称 {code6}")
                break

        # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
        if not stock_info:
            stock_info = db.stock_basic_info.find_one(
                {"$or": [{"symbol": code6}, {"code": code6}]}
            )
            if stock_info:
                logger.warning(f"⚠️ 使用旧数据（无 source 字段）获取股票名称 {code6}")

        if stock_info and stock_info.get("name"):
            stock_name = stock_info["name"]
            _stock_name_cache[stock_code] = stock_name
            return stock_name

        # 如果没有找到，返回股票代码
        _stock_name_cache[stock_code] = stock_code
        return stock_code

    except Exception as e:
        logger.warning(f"⚠️ 获取股票名称失败 {stock_code}: {e}")
        return stock_code


# 统一构建报告查询：支持 _id(ObjectId) / analysis_id / task_id 三种
def _build_report_query(report_id: str) -> Dict[str, Any]:
    ors = [
        {"analysis_id": report_id},
        {"task_id": report_id},
    ]
    try:
        from bson import ObjectId
        ors.append({"_id": ObjectId(report_id)})
    except Exception:
        pass
    return {"$or": ors}

router = APIRouter(prefix="/api/reports", tags=["reports"])

class ReportFilter(BaseModel):
    """报告筛选参数"""
    search_keyword: Optional[str] = None
    market_filter: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    stock_code: Optional[str] = None
    report_type: Optional[str] = None

class ReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int

@router.get("/list", response_model=Dict[str, Any])
async def get_reports_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search_keyword: Optional[str] = Query(None, description="搜索关键词"),
    market_filter: Optional[str] = Query(None, description="市场筛选（A股/港股/美股）"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    user: dict = Depends(get_current_user)
):
    """获取分析报告列表"""
    try:
        logger.info(f"🔍 获取报告列表: 用户={user['id']}, 页码={page}, 每页={page_size}, 市场={market_filter}")

        db = get_mongo_db()

        # 构建查询条件
        query = {}

        # 搜索关键词
        if search_keyword:
            query["$or"] = [
                {"stock_symbol": {"$regex": search_keyword, "$options": "i"}},
                {"analysis_id": {"$regex": search_keyword, "$options": "i"}},
                {"summary": {"$regex": search_keyword, "$options": "i"}}
            ]

        # 市场筛选
        if market_filter:
            query["market_type"] = market_filter

        # 股票代码筛选
        if stock_code:
            query["stock_symbol"] = stock_code

        # 日期范围筛选
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["analysis_date"] = date_query

        logger.info(f"📊 查询条件: {query}")

        # 计算总数
        total = await db.analysis_reports.count_documents(query)

        # 分页查询
        skip = (page - 1) * page_size
        cursor = db.analysis_reports.find(query).sort("created_at", -1).skip(skip).limit(page_size)

        reports = []
        async for doc in cursor:
            # 转换为前端需要的格式
            stock_code = doc.get("stock_symbol", "")
            # 🔥 优先使用MongoDB中保存的股票名称，如果没有则查询
            stock_name = doc.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_code)

            # 🔥 获取市场类型，如果没有则根据股票代码推断
            market_type = doc.get("market_type")
            if not market_type:
                try:
                    from tradingagents.utils.stock_utils import StockUtils
                    market_info = StockUtils.get_market_info(stock_code)
                except ImportError:
                    import logging as _fallback_logging
                    _fallback_logging.getLogger(__name__).warning(
                        "tradingagents.utils.stock_utils.StockUtils 不可用，使用 fallback 推断市场类型"
                    )
                    code_str = str(stock_code).strip()
                    if code_str.isdigit() or code_str.endswith(".SH") or code_str.endswith(".SZ"):
                        market_info = {"market": "china_a"}
                    elif "." in code_str and not code_str.startswith(tuple("0123456789")):
                        market_info = {"market": "us"}
                    else:
                        market_info = {"market": "unknown"}
                market_type_map = {
                    "china_a": "A股",
                    "hong_kong": "港股",
                    "us": "美股",
                    "unknown": "A股"
                }
                market_type = market_type_map.get(market_info.get("market", "unknown"), "A股")

            # 获取创建时间（数据库中是 UTC 时间，需要转换为 UTC+8）
            created_at = doc.get("created_at", datetime.utcnow())
            created_at_tz = to_config_tz(created_at)  # 转换为 UTC+8 并添加时区信息

            # 🔥 从 decision 或 state 中提取决策信息
            decision = doc.get("decision", {}) or doc.get("state", {}) or {}
            if not isinstance(decision, dict):
                decision = {}

            # 决策建议
            action = decision.get("action", "")
            if action and isinstance(action, str):
                action = action.upper()
                action_map = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有", "STRONG_BUY": "强烈买入", "STRONG_SELL": "强烈卖出"}
                action = action_map.get(action, action)

            # 置信度
            confidence = decision.get("confidence", 0)
            try:
                if isinstance(confidence, (int, float)) and 0 < confidence <= 1:
                    confidence = round(confidence * 100, 1)
                elif isinstance(confidence, (int, float)) and confidence > 1:
                    confidence = round(float(confidence), 1)
                else:
                    confidence = 0
            except (TypeError, ValueError):
                confidence = 0

            # 目标价 / 止损价
            target_price = decision.get("target_price", "")
            stop_loss = decision.get("stop_loss", "")
            if target_price is None:
                target_price = ""
            if stop_loss is None:
                stop_loss = ""

            report = {
                "id": str(doc["_id"]),
                "analysis_id": doc.get("analysis_id", ""),
                "title": f"{stock_name}({stock_code}) 分析报告",
                "stock_code": stock_code,
                "stock_name": stock_name,
                "market_type": market_type,  # 🔥 添加市场类型字段
                # 🔥 决策信息
                "action": action,
                "confidence": confidence,
                "target_price": target_price,
                "stop_loss": stop_loss,
                # 基础信息
                "created_at": created_at_tz.isoformat() if created_at_tz else str(created_at),
                "analysis_date": doc.get("analysis_date", ""),
                "analysts": doc.get("analysts", []),
                "research_depth": doc.get("research_depth", 1),
                "summary": doc.get("summary", ""),
                "file_size": len(str(doc.get("reports", {}))),  # 估算大小
                "source": doc.get("source", "unknown"),
                "task_id": doc.get("task_id", "")
            }
            reports.append(report)

        logger.info(f"✅ 查询完成: 总数={total}, 返回={len(reports)}")

        return {
            "success": True,
            "data": {
                "reports": reports,
                "total": total,
                "page": page,
                "page_size": page_size
            },
            "message": "报告列表获取成功"
        }

    except Exception as e:
        logger.error(f"❌ 获取报告列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/detail")
async def get_report_detail(
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """获取报告详情"""
    try:
        logger.info(f"🔍 获取报告详情: {report_id}")

        db = get_mongo_db()

        # 支持 ObjectId / analysis_id / task_id
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            # 兜底：从 analysis_tasks.result 中还原报告详情
            logger.info(f"⚠️ 未在analysis_reports找到，尝试从analysis_tasks还原: {report_id}")
            tasks_doc = await db.analysis_tasks.find_one(
                {"$or": [{"task_id": report_id}, {"result.analysis_id": report_id}]},
                {"result": 1, "task_id": 1, "stock_code": 1, "created_at": 1, "completed_at": 1}
            )
            if not tasks_doc or not tasks_doc.get("result"):
                raise HTTPException(status_code=404, detail="报告不存在")

            r = tasks_doc["result"] or {}
            created_at = tasks_doc.get("created_at")
            updated_at = tasks_doc.get("completed_at") or created_at

            # 转换时区：数据库中是 UTC 时间，转换为 UTC+8
            created_at_tz = to_config_tz(created_at)
            updated_at_tz = to_config_tz(updated_at)

            def to_iso(x):
                if hasattr(x, "isoformat"):
                    return x.isoformat()
                return x or ""

            stock_symbol = r.get("stock_symbol", r.get("stock_code", tasks_doc.get("stock_code", "")))
            stock_name = r.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_symbol)

            report = {
                "id": tasks_doc.get("task_id", report_id),
                "analysis_id": r.get("analysis_id", ""),
                "stock_symbol": stock_symbol,
                "stock_name": stock_name,  # 🔥 添加股票名称字段
                "model_info": r.get("model_info", "Unknown"),  # 🔥 添加模型信息字段
                "analysis_date": r.get("analysis_date", ""),
                "status": r.get("status", "completed"),
                "created_at": to_iso(created_at_tz),
                "updated_at": to_iso(updated_at_tz),
                "analysts": r.get("analysts", []),
                "research_depth": r.get("research_depth", 1),
                "summary": r.get("summary", ""),
                "reports": r.get("reports", {}),
                "source": "analysis_tasks",
                "task_id": tasks_doc.get("task_id", report_id),
                "recommendation": r.get("recommendation", ""),
                "confidence_score": r.get("confidence_score", 0.0),
                "risk_level": r.get("risk_level", "中等"),
                "key_points": r.get("key_points", []),
                "execution_time": r.get("execution_time", 0),
                "tokens_used": r.get("tokens_used", 0)
            }
            # 🔥 从 markdown 子报告中抽取结构化字段（核心洞察、策略点位等）
            _extracted = extract_structured_fields(report["reports"])
            # 已有字段保留优先级，仅在缺失时覆盖
            for _k, _v in _extracted.items():
                if _v is not None and (not report.get(_k)):
                    report[_k] = _v
        else:
            # 转换为详细格式（analysis_reports 命中）
            stock_symbol = doc.get("stock_symbol", "")
            stock_name = doc.get("stock_name")
            if not stock_name:
                stock_name = get_stock_name(stock_symbol)

            # 获取时间（数据库中是 UTC 时间，需要转换为 UTC+8）
            created_at = doc.get("created_at", datetime.utcnow())
            updated_at = doc.get("updated_at", datetime.utcnow())

            # 转换时区：数据库中是 UTC 时间，转换为 UTC+8
            created_at_tz = to_config_tz(created_at)
            updated_at_tz = to_config_tz(updated_at)

            report = {
                "id": str(doc["_id"]),
                "analysis_id": doc.get("analysis_id", ""),
                "stock_symbol": stock_symbol,
                "stock_name": stock_name,  # 🔥 添加股票名称字段
                "model_info": doc.get("model_info", "Unknown"),  # 🔥 添加模型信息字段
                "analysis_date": doc.get("analysis_date", ""),
                "status": doc.get("status", "completed"),
                "created_at": created_at_tz.isoformat() if created_at_tz else str(created_at),
                "updated_at": updated_at_tz.isoformat() if updated_at_tz else str(updated_at),
                "analysts": doc.get("analysts", []),
                "research_depth": doc.get("research_depth", 1),
                "summary": doc.get("summary", ""),
                "reports": doc.get("reports", {}),
                "source": doc.get("source", "unknown"),
                "task_id": doc.get("task_id", ""),
                "recommendation": doc.get("recommendation", ""),
                "confidence_score": doc.get("confidence_score", 0.0),
                "risk_level": doc.get("risk_level", "中等"),
                "key_points": doc.get("key_points", []),
                "execution_time": doc.get("execution_time", 0),
                "tokens_used": doc.get("tokens_used", 0)
            }
            # 🔥 从 markdown 子报告中抽取结构化字段（核心洞察、策略点位、止盈止损等）
            _extracted = extract_structured_fields(report["reports"])
            for _k, _v in _extracted.items():
                if _v is not None and (not report.get(_k)):
                    report[_k] = _v

        return {
            "success": True,
            "data": report,
            "message": "报告详情获取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取报告详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/content/{module}")
async def get_report_module_content(
    report_id: str,
    module: str,
    user: dict = Depends(get_current_user)
):
    """获取报告特定模块的内容"""
    try:
        logger.info(f"🔍 获取报告模块内容: {report_id}/{module}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="报告不存在")

        reports = doc.get("reports", {})

        if module not in reports:
            raise HTTPException(status_code=404, detail=f"模块 {module} 不存在")

        content = reports[module]

        return {
            "success": True,
            "data": {
                "module": module,
                "content": content,
                "content_type": "markdown" if isinstance(content, str) else "json"
            },
            "message": "模块内容获取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取报告模块内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user: dict = Depends(get_current_user)
):
    """删除报告"""
    try:
        logger.info(f"🗑️ 删除报告: {report_id}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        result = await db.analysis_reports.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="报告不存在")

        logger.info(f"✅ 报告删除成功: {report_id}")

        return {
            "success": True,
            "message": "报告删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("markdown", description="下载格式: markdown, json, pdf, docx"),
    user: dict = Depends(get_current_user)
):
    """下载报告

    支持的格式:
    - markdown: Markdown 格式（默认）
    - json: JSON 格式（包含完整数据）
    - docx: Word 文档格式（需要 pandoc）
    - pdf: PDF 格式（需要 pandoc 和 PDF 引擎）
    """
    try:
        logger.info(f"📥 下载报告: {report_id}, 格式: {format}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="报告不存在")

        stock_symbol = doc.get("stock_symbol", "unknown")
        analysis_date = doc.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))

        if format == "json":
            # JSON格式下载
            content = json.dumps(doc, ensure_ascii=False, indent=2, default=str)
            filename = f"{stock_symbol}_{analysis_date}_report.json"
            media_type = "application/json"

            # 返回文件流
            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format == "markdown":
            # Markdown格式下载
            reports = doc.get("reports", {})
            content_parts = []

            # 添加标题
            content_parts.append(f"# {stock_symbol} 分析报告")
            content_parts.append(f"**分析日期**: {analysis_date}")
            content_parts.append(f"**分析师**: {', '.join(doc.get('analysts', []))}")
            content_parts.append(f"**研究深度**: {doc.get('research_depth', 1)}")
            content_parts.append("")

            # 添加摘要
            if doc.get("summary"):
                content_parts.append("## 执行摘要")
                content_parts.append(doc["summary"])
                content_parts.append("")

            # 添加各模块内容
            for module_name, module_content in reports.items():
                if isinstance(module_content, str) and module_content.strip():
                    content_parts.append(f"## {module_name}")
                    content_parts.append(module_content)
                    content_parts.append("")

            content = "\n".join(content_parts)
            filename = f"{stock_symbol}_{analysis_date}_report.md"
            media_type = "text/markdown"

            # 返回文件流
            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format == "docx":
            # Word 文档格式下载
            from app.utils.report_exporter import report_exporter

            if not report_exporter.pandoc_available:
                raise HTTPException(
                    status_code=400,
                    detail="Word 导出功能不可用。请安装 pandoc: pip install pypandoc"
                )

            try:
                # 生成 Word 文档
                docx_content = report_exporter.generate_docx_report(doc)
                filename = f"{stock_symbol}_{analysis_date}_report.docx"

                # 返回文件流
                def generate():
                    yield docx_content

                return StreamingResponse(
                    generate(),
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            except Exception as e:
                logger.error(f"❌ Word 文档生成失败: {e}")
                raise HTTPException(status_code=500, detail=f"Word 文档生成失败: {str(e)}")

        elif format == "pdf":
            # PDF 格式下载
            from app.utils.report_exporter import report_exporter

            if not report_exporter.pandoc_available:
                raise HTTPException(
                    status_code=400,
                    detail="PDF 导出功能不可用。请安装 pandoc 和 PDF 引擎（wkhtmltopdf 或 LaTeX）"
                )

            try:
                # 生成 PDF 文档
                pdf_content = report_exporter.generate_pdf_report(doc)
                filename = f"{stock_symbol}_{analysis_date}_report.pdf"

                # 返回文件流
                def generate():
                    yield pdf_content

                return StreamingResponse(
                    generate(),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            except Exception as e:
                logger.error(f"❌ PDF 文档生成失败: {e}")
                raise HTTPException(status_code=500, detail=f"PDF 文档生成失败: {str(e)}")

        else:
            raise HTTPException(status_code=400, detail=f"不支持的下载格式: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 下载报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
