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


def _extract_holder_empty_advice(text: str, field_name: str) -> Optional[str]:
    """
    提取持仓者建议或空仓者建议。
    匹配格式如：
      - "1.  **对于当前持仓者（首要任务）：**" + 列表项
      - "持仓者：xxx"
      - "对于空仓者：xxx"
      - "止损价格（建议给现持仓者）：xxx"
      - "理想买入（不建议，仅作空仓者观察参考）：xxx"
    
    收集从标题行之后的所有内容（包括列表项），直到遇到下一个章节标题或文档结束。
    """
    if not text:
        return None
    
    lines = text.split("\n")
    n = len(lines)
    
    # 持仓者关键词（精确匹配）
    holder_patterns = [
        r"^持仓者[：:：]",
        r"^对于.*持仓者[：:：]",
        r"^当前持仓者[：:：]",
        r"^持有者[：:：]",
        r"持仓者建议[：:：]",
        r"建议给现持仓者",
        r"（建议给现持仓者）",
        r"（持仓者.*建议）",
    ]
    # 空仓者关键词（精确匹配）
    empty_patterns = [
        r"^空仓者[：:：]",
        r"^对于.*空仓者[：:：]",
        r"^未持仓者[：:：]",
        r"^观望者[：:：]",
        r"空仓建议[：:：]",
        r"空仓者观察",
        r"空仓者.*参考",
        r"仅作.*空仓者",
        r"空仓者.*观望",
        r"空仓者.*买入",
        r"不建议.*空仓者",
    ]
    
    patterns = holder_patterns if field_name == "持仓者建议" else empty_patterns
    # 排除关键词
    if field_name == "持仓者建议":
        exclude_patterns = [r"^空仓者", r"空仓者[：:：]", r"观望者[：:：]", r"仅作.*空仓者", r"不建议.*空仓者", r"空仓者.*观望", r"空仓者.*买入"]
    else:
        exclude_patterns = [r"^持仓者", r"持仓者[：:：]", r"持有者[：:：]", r"建议给现持仓者", r"（建议给现持仓者）"]
    
    collected = []
    
    # 方法1：找章节标题
    start_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pat in patterns:
            if re.search(pat, stripped):
                start_idx = i
                break
        if start_idx is not None:
            break
    
    if start_idx is not None:
        # 收集从 start_idx+1 开始的内容
        for j in range(start_idx + 1, n):
            line = lines[j]
            stripped = line.strip()
            
            # 遇到任何标题行（# 到 ######）停止
            if re.match(r"^#{1,6}\s+", stripped):
                break
            
            # 持仓者遇到"对于空仓者"或"空仓者"停止
            if field_name == "持仓者建议":
                if re.search(r"(对于空仓者|空仓者[：:：])", stripped):
                    break
            
            # 跳过纯标题行（如 "1. xxx：" 或 "#### xxx"）
            if re.match(r"^\d+[\.、]\s*", stripped) and re.search(r"[：:：]$", stripped):
                continue
            
            if stripped:
                collected.append(stripped)
    else:
        # 方法2：对于结构化列表格式，收集所有包含关键词且不包含排除关键词的行
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查是否包含关键词
            has_keyword = False
            for pat in patterns:
                if re.search(pat, stripped):
                    has_keyword = True
                    break
            
            # 检查是否包含排除关键词
            has_exclude = False
            for pat in exclude_patterns:
                if re.search(pat, stripped):
                    has_exclude = True
                    break
            
            if has_keyword and not has_exclude:
                # 清理并添加
                cleaned = re.sub(r"\*+", "", stripped)
                cleaned = re.sub(r"^[\•\-\*\d\.]+\s*", "", cleaned)
                if cleaned and len(cleaned) > 5:
                    collected.append(cleaned)
    
    if not collected:
        return None
    
    # 清理内容
    content = "\n".join(collected)
    # 移除 markdown 加粗符号
    content = re.sub(r"\*+", "", content)
    # 移除列表标记
    content = re.sub(r"^[\•\-\*\d\.]+\s*", "", content, flags=re.MULTILINE)
    content = content.strip()
    
    if not content:
        return None
    
    # 限制长度
    max_chars = 1000
    if len(content) > max_chars:
        # 在句号处截断
        pos = content.rfind("。", 0, max_chars)
        if pos > max_chars // 2:
            content = content[:pos + 1]
        else:
            content = content[:max_chars] + "…"
    
    return content


def extract_structured_fields(reports: Dict[str, Any]) -> Dict[str, Any]:
    """
    遍历 reports 中的所有子报告（以及可能存在的 decision 字典），
    抽取可用于前端展示的结构化字段。字段会被合并到报告详情顶层，
    以便前端 `pickField(report, [...])` 工作。

    **统一的评级/操作建议**：`评级`、`操作建议`、`action` 三个字段完全一致，
    优先级为：final_trade_decision 文本 > trader_investment_plan 文本 >
    research_team_decision 文本 > decision 对象字典 > 全文兜底。

    **六张核心洞察卡片**：每张卡片的内容明确来源于对应研究报告章节，
    按以下优先级提取：章节标题精确匹配 → 关键字段匹配 → 对应模块正文精选。

    返回字段（中文命名，便于前端直接展示）：
      - 置信度 / 技术面评分 / 基本面评分 / 情绪面评分 / 政策面评分
      - 风险等级
      - 评级 / 操作建议 / action（三者完全一致）
      - 理想买入 / 二次买入 / 止损价格 / 止盈目标 / 支撑位 / 阻力位
      - 核心洞察 / 投资逻辑 / 情绪分析 / 趋势预测 / 策略点位 / 风险提示
    """
    result: Dict[str, Any] = {}
    if not isinstance(reports, dict) or not reports:
        return result

    # 0) 先从高优先级文本模块提取操作建议（评级），比 decision 字典更权威
    priority_modules = [
        "final_trade_decision", "trader_investment_plan",
        "investment_plan", "research_team_decision",
        "risk_management_decision",
    ]

    def _priority_texts():
        for key in priority_modules:
            v = reports.get(key)
            if isinstance(v, str):
                yield v

    # 统一的评级规范化函数（确保最终输出是 5 档中文评级之一）
    def _normalize_rating(val: str) -> str:
        v = str(val).strip()
        # 先清理可能的前后缀（如"评级：买入"、"建议: 强烈买入"）
        for kw in ["评级", "操作建议", "投资建议", "建议"]:
            if v.startswith(kw):
                v = v[len(kw):].lstrip("：:、•·- ")
                v = v.strip()
                break
        # 去除标点前后缀
        v = v.strip("，。；：:、•·()（） ")
        # 常见英文/缩写翻译
        en_map = {
            "BUY": "买入", "SELL": "卖出", "HOLD": "持有",
            "STRONG_BUY": "强烈买入", "STRONG_SELL": "强烈卖出",
            "STRONG BUY": "强烈买入", "STRONG SELL": "强烈卖出",
            "OVERWEIGHT": "买入", "UNDERWEIGHT": "减仓",
            "NEUTRAL": "持有", "WAIT": "持有", "观望": "持有",
        }
        v_upper = v.upper()
        if v_upper in en_map:
            return en_map[v_upper]
        # 中文关键词识别（从长到短匹配，避免误识别）
        cn_aliases = [
            ("强烈买入", "强烈买入"),
            ("强烈卖出", "强烈卖出"),
            ("买入", "买入"),
            ("卖出", "卖出"),
            ("减仓", "减仓"),
            ("加仓", "买入"),
            ("持有", "持有"),
            ("观望", "持有"),
        ]
        for alias, final in cn_aliases:
            if alias in v:
                return final
        return v

    # 从优先级最高的模块开始提取，找到第一个非空的评级
    text_rating = None
    for module_text in _priority_texts():
        val = _match_rating(module_text, ["操作建议", "评级", "投资建议", "建议"])
        if val:
            text_rating = _normalize_rating(val)
            break

    # 1) 从 decision 字典取值（来自 trading_graph 的结构化输出）
    decision_obj = reports.get("decision")
    if isinstance(decision_obj, dict) and decision_obj:
        conf_val = (
            decision_obj.get("confidence_score")
            or decision_obj.get("confidence")
            or decision_obj.get("score")
        )
        if conf_val is not None and conf_val != "":
            try:
                if isinstance(conf_val, (int, float)) and 0 < conf_val <= 1:
                    result["置信度"] = round(conf_val * 100, 1)
                else:
                    result["置信度"] = round(float(conf_val), 1)
            except (TypeError, ValueError):
                pass
        if "风险等级" not in result:
            rl_val = decision_obj.get("risk_level")
            if rl_val:
                result["风险等级"] = str(rl_val)
        # 仅当文本模块未提取到操作建议时，才使用 decision 字典
        if text_rating is None:
            act = (
                decision_obj.get("action")
                or decision_obj.get("recommendation")
                or decision_obj.get("rating")
            )
            if act:
                text_rating = _normalize_rating(str(act))

    # 统一设置评级 / 操作建议 / action，三者保持完全一致
    if text_rating:
        result["评级"] = text_rating
        result["操作建议"] = text_rating
        result["action"] = text_rating

    # 1b) 从 decision 字典提取价格类字段（与评级无关，独立提取）
    if isinstance(decision_obj, dict) and decision_obj:
        tp = decision_obj.get("target_price") or decision_obj.get("price_target")
        if tp is not None and tp != "":
            try:
                result["止盈目标"] = f"{round(float(tp), 2)} 元"
            except (TypeError, ValueError):
                result["止盈目标"] = str(tp)
        sl = decision_obj.get("stop_loss") or decision_obj.get("stop_loss_price")
        if sl is not None and sl != "":
            try:
                result["止损价格"] = f"{round(float(sl), 2)} 元"
            except (TypeError, ValueError):
                result["止损价格"] = str(sl)
        buy1 = decision_obj.get("ideal_buy") or decision_obj.get("buy_price")
        if buy1 is not None and buy1 != "":
            try:
                result["理想买入"] = f"{round(float(buy1), 2)} 元"
            except (TypeError, ValueError):
                result["理想买入"] = str(buy1)
        buy2 = decision_obj.get("second_buy")
        if buy2 is not None and buy2 != "":
            try:
                result["二次买入"] = f"{round(float(buy2), 2)} 元"
            except (TypeError, ValueError):
                result["二次买入"] = str(buy2)
        sup = decision_obj.get("support_level") or decision_obj.get("support")
        if sup is not None and sup != "":
            try:
                result["支撑位"] = f"{round(float(sup), 2)} 元"
            except (TypeError, ValueError):
                result["支撑位"] = str(sup)
        res_val = decision_obj.get("resistance_level") or decision_obj.get("resistance")
        if res_val is not None and res_val != "":
            try:
                result["阻力位"] = f"{round(float(res_val), 2)} 元"
            except (TypeError, ValueError):
                result["阻力位"] = str(res_val)

    # 2) 再从各子报告 markdown 文本中补充/覆盖（如果 decision 没有）
    #    **六张核心洞察卡片的字段别名定义**：
    #    每个卡片对应的章节标题别名，由长到短匹配，防止误识别
    section_aliases = [
        # 1. 核心洞察：研究经理总结的主要矛盾/关键结论
        (["核心洞察", "核心结论", "核心观点", "核心要点", "核心逻辑", "核心矛盾"], "核心洞察", 300),
        # 2. 投资逻辑：支撑买入/卖出评级的底层理由（基本面+技术面+情绪面综合）
        (["投资逻辑", "投资依据", "投资理由", "投资论证", "分析逻辑", "判断依据"], "投资逻辑", 300),
        # 3. 情绪分析：市场情绪、资金流向、散户/主力态度
        (["情绪分析", "市场情绪", "舆情分析", "情绪面", "情绪面分析", "资金情绪"], "情绪分析", 300),
        # 4. 趋势预测：短期/中期走势判断、趋势方向、技术形态结论
        (["趋势预测", "趋势展望", "走势判断", "走势预测", "方向判断", "中期展望"], "趋势预测", 300),
        # 5. 策略点位：入场/加仓/离场的关键价格位置
        (["策略点位", "关键点位", "交易策略", "操作策略", "关键支撑", "关键阻力", "关键支撑位/阻力位"],
         "策略点位", 300),
        # 6. 风险提示：所有可能影响结论的负面因素
        (["风险提示", "风险因素", "风险分析", "主要风险", "风险预警", "风险说明"], "风险提示", 300),
    ]
    price_aliases = [
        (["理想买入"], "理想买入"),
        (["二次买入"], "二次买入"),
        (["止损价格", "止损位", "止损线"], "止损价格"),
        (["止盈目标", "目标价格", "目标价"], "止盈目标"),
        (["支撑位", "支撑"], "支撑位"),
        (["阻力位", "压力位"], "阻力位"),
    ]
    score_aliases = [
        (["置信度"], "置信度"),
        (["风险等级"], "风险等级"),
        (["技术面评分"], "技术面评分"),
        (["基本面评分"], "基本面评分"),
        (["情绪面评分"], "情绪面评分"),
        (["政策面评分"], "政策面评分"),
    ]

    # 2a) 文本章节：先找精确章节名，再回退到对应模块内容（做内容清洗后截取）
    #    **每类卡片的内容来源严格定义**（按优先级从高到低）：
    #    - 核心洞察：研究经理/最终决策（最具总结性的结论）
    #    - 投资逻辑：研究经理/交易员计划（分析推理过程）
    #    - 趋势预测：市场技术分析/交易员计划（技术面判断）
    #    - 策略点位：交易员投资计划/最终决策（具体操作点位）
    #    - 情绪分析：情绪分析报告/新闻报告/游资追踪（市场情绪相关内容）
    #    - 风险提示：风险管理决策/最终决策（风险警示内容）
    fallback_modules = {
        "核心洞察": ["final_trade_decision", "research_team_decision",
                      "trader_investment_plan", "investment_plan"],
        "投资逻辑": ["research_team_decision", "final_trade_decision",
                    "trader_investment_plan", "bull_researcher", "bear_researcher"],
        "趋势预测": ["market_report", "trader_investment_plan",
                   "final_trade_decision", "investment_plan"],
        "策略点位": ["trader_investment_plan", "investment_plan",
                   "final_trade_decision", "market_report"],
        "情绪分析": ["sentiment_report", "news_report", "hot_money_report",
                   "market_report", "final_trade_decision"],
        "风险提示": ["risk_management_decision", "final_trade_decision",
                   "risky_analyst", "safe_analyst", "neutral_analyst"],
    }

    def _clean_and_extract_content(text: str, limit: int) -> str:
        """
        从模块文本中清洗并提取可直接展示在卡片里的内容。
        - 短限制（< 350）：按句子级挑选，优先结论性/总结性句子
        - 长限制：保留完整结构（段落+小标题）
        """
        if not text:
            return ""

        raw_lines = text.strip().split("\n")
        in_table = False

        # 套话关键词 - 跳过
        skip_patterns = [
            "数据已获取完毕", "下面我将基于", "进行全面的",
            "市场情绪分析报告", "分析时段", "参考日期",
            "分析报告", "报告", "总结如下", "如下分析",
        ]

        # 句子优先级关键词（高价值句子优先保留）
        high_value_keywords = [
            "结论", "核心", "总结", "主要", "建议", "看好",
            "买入", "卖出", "评级", "预测", "趋势", "风险",
            "关键", "重点", "显著", "拐点", "确立", "利好",
            "利空", "正面", "负面", "机会", "信号", "逻辑",
        ]

        # ===== 第一步：逐行清洗 =====
        cleaned_lines: List[str] = []
        for ln in raw_lines:
            stripped = ln.strip()

            # 空行
            if not stripped:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            # 跳过分隔线
            if re.match(r'^[-=_]{2,}$', stripped):
                continue

            # 跳过表格
            if stripped.startswith("|") or stripped.startswith("｜"):
                in_table = True
                continue
            if in_table:
                in_table = False

            # 跳过图片/链接
            if stripped.startswith("![") or (stripped.startswith("http") and " " not in stripped):
                continue

            # 跳过套话行
            skip_line = False
            for pat in skip_patterns:
                if pat in stripped and len(stripped) < 120:
                    skip_line = True
                    break
            if skip_line:
                continue

            # 跳过纯标题行（不管是 ### 还是 **标题**）
            is_pure_header = False
            if re.match(r'^#{1,6}\s+', stripped):
                is_pure_header = True
            # 类似 "**一、核心结论：**" 这种纯标题
            if len(stripped) < 30 and re.match(r'^[*_\s\w一二三四五六七八九十\d\.、]+[:：]?\s*$', stripped):
                is_pure_header = True
            # 以 "：" / ":" 结尾的短行通常也是标题
            if len(stripped) < 25 and (stripped.endswith("：") or stripped.endswith(":")):
                is_pure_header = True

            if is_pure_header:
                continue

            # 移除 ** 加粗符号
            stripped = re.sub(r'\*+', '', stripped)
            # 移除行首 emoji
            stripped = re.sub(r'^[\U0001F000-\U0001FFFF]\s*', '', stripped)

            # 移除行首的列表标记 (1. 2. • - 等)
            stripped = re.sub(r'^(\d+[\.、]\s*|[•\-—·]\s*)', '', stripped)

            # 太短且无句号/冒号的行跳过
            if len(stripped) < 8 and not any(ch in stripped for ch in "。！？："):
                continue

            cleaned_lines.append(stripped)

        # ===== 第二步：合并成段落 =====
        paragraphs: List[str] = []
        current_para: List[str] = []

        for ln in cleaned_lines:
            if ln == "":
                if current_para:
                    joined = " ".join(current_para).strip()
                    joined = re.sub(r'\s{2,}', ' ', joined)
                    if len(joined) >= 10:
                        paragraphs.append(joined)
                    current_para = []
            else:
                current_para.append(ln)

        if current_para:
            joined = " ".join(current_para).strip()
            joined = re.sub(r'\s{2,}', ' ', joined)
            if len(joined) >= 10:
                paragraphs.append(joined)

        while paragraphs and len(paragraphs[0]) < 15:
            paragraphs.pop(0)

        if not paragraphs:
            return ""

        # ===== 第三步：按限制长度处理 =====
        # 短限制：句子级挑选，优先高价值内容
        if limit <= 350:
            # 把所有段落拆成句子（按 。！？；）
            all_sentences: List[str] = []
            for para in paragraphs:
                parts = re.split(r'([。！？；])', para)
                # 重新组合："句子 + 标点"
                for i in range(0, len(parts) - 1, 2):
                    sent = parts[i] + parts[i + 1]
                    sent = sent.strip()
                    if len(sent) >= 10:
                        all_sentences.append(sent)
                # 处理没有结尾标点的最后一句
                if len(parts) % 2 == 1 and parts[-1].strip() and len(parts[-1].strip()) >= 10:
                    all_sentences.append(parts[-1].strip())

            if not all_sentences:
                # 没有句子？直接从段落中截取
                combined = " ".join(paragraphs)
                if len(combined) <= limit:
                    return combined
                pos = combined.rfind("。", 0, limit)
                if pos > limit // 2:
                    return combined[:pos + 1]
                return combined[:limit]

            # 对句子评分：高价值关键词加分
            scored: List[tuple[int, str]] = []
            for idx, sent in enumerate(all_sentences):
                score = 0
                for kw in high_value_keywords:
                    if kw in sent:
                        score += 10
                # 越靠前的句子通常越重要
                score += max(0, 10 - idx)
                # 太短的句子（< 12字）可能不完整，略扣分
                if len(sent) < 12:
                    score -= 5
                scored.append((score, sent))

            # 按评分从高到低排序后取前 N 句能容纳的
            # 但为了保持阅读顺序，我们保留原始顺序
            # 先选出高价值句子的索引
            sorted_by_score = sorted(enumerate(scored), key=lambda x: x[1][0], reverse=True)

            selected_indices: List[int] = []
            total_len = 0
            for original_idx, (score, sent) in sorted_by_score:
                if total_len + len(sent) + 2 <= limit:
                    selected_indices.append(original_idx)
                    total_len += len(sent) + 2
                if total_len >= limit - 20:
                    break

            # 如果选了少于2句，补充前面的句子
            if len(selected_indices) < 2:
                for idx in range(len(all_sentences)):
                    if idx not in selected_indices:
                        sent = all_sentences[idx]
                        if total_len + len(sent) + 2 <= limit:
                            selected_indices.append(idx)
                            total_len += len(sent) + 2
                            if len(selected_indices) >= 3:
                                break

            # 按原始顺序排列
            selected_indices.sort()
            result_sentences = [all_sentences[i] for i in selected_indices]

            if not result_sentences:
                # 兜底：取第一句
                first = all_sentences[0]
                if len(first) > limit:
                    pos = first.rfind("。", 0, limit)
                    if pos > limit // 3:
                        return first[:pos + 1]
                    return first[:limit]
                return first

            final_text = "。".join(result_sentences)
            # 修正：去掉可能重复的句号
            final_text = re.sub(r'。{2,}', '。', final_text)
            if len(final_text) > limit:
                pos = final_text.rfind("。", 0, limit)
                if pos > limit // 2:
                    return final_text[:pos + 1]
                return final_text[:limit]
            return final_text

        # 长限制：保留段落结构
        result_lines: List[str] = []
        current_len = 0
        for p in paragraphs:
            if current_len + len(p) > limit:
                remaining = limit - current_len
                if remaining > 20:
                    truncate_pos = p.rfind("。", 0, remaining)
                    if truncate_pos > remaining // 2:
                        result_lines.append(p[:truncate_pos + 1])
                    else:
                        result_lines.append(p[:remaining])
                break
            result_lines.append(p)
            current_len += len(p) + 2

        final_text = "\n\n".join(result_lines).strip()
        if len(final_text) > limit:
            final_text = final_text[:limit]
        return final_text

    for aliases, field_name, max_chars in section_aliases:
        if result.get(field_name):
            continue
        found = False
        full_content = ""

        # 步骤 A：优先从字段专属的 fallback_modules 中搜索精确章节标题
        # （这是最可靠的内容来源）
        if field_name in fallback_modules:
            for module_key in fallback_modules[field_name]:
                module_text = reports.get(module_key)
                if not (isinstance(module_text, str) and module_text.strip()):
                    continue
                val = _extract_section(module_text, aliases, max_chars)
                if val and not result.get(field_name):
                    result[field_name] = val
                    found = True
                # 尝试提取完整内容（不截断）
                full_val = _extract_section(module_text, aliases, 5000)
                if full_val and len(full_val) > len(val or ""):
                    full_content = full_val
                if found and full_content:
                    break

        # 步骤 B：在全局优先级模块中搜索精确章节标题（补充）
        if not found:
            for module_text in _priority_texts():
                val = _extract_section(module_text, aliases, max_chars)
                if val and not result.get(field_name):
                    result[field_name] = val
                    found = True
                full_val = _extract_section(module_text, aliases, 5000)
                if full_val and len(full_val) > len(val or ""):
                    full_content = full_val
                if found and full_content:
                    break

        # 步骤 C：在全部报告模块中搜索精确章节标题（兜底）
        if not found:
            for v in reports.values():
                if isinstance(v, str):
                    val = _extract_section(v, aliases, max_chars)
                    if val:
                        result[field_name] = val
                        found = True
                        full_val = _extract_section(v, aliases, 5000)
                        if full_val and len(full_val) > len(val):
                            full_content = full_val
                        break

        # 步骤 D：终极回退——从字段专属模块正文清洗并截取（内容仍然来源于研究报告）
        if not found and field_name in fallback_modules:
            for module_key in fallback_modules[field_name]:
                module_text = reports.get(module_key)
                if isinstance(module_text, str) and module_text.strip():
                    extracted = _clean_and_extract_content(module_text, max_chars)
                    if extracted:
                        result[field_name] = extracted
                        full_extracted = _clean_and_extract_content(module_text, 5000)
                        if full_extracted and len(full_extracted) > len(extracted):
                            full_content = full_extracted
                        break
        # 存储完整内容（用于前端悬停显示）
        if full_content and len(full_content) > len(result.get(field_name, "")):
            result[field_name + "_full"] = full_content

    # 2b) 价格字段
    for aliases, field_name in price_aliases:
        if result.get(field_name):
            continue
        for module_text in _priority_texts():
            val = _match_price(module_text, aliases)
            if val and not result.get(field_name):
                result[field_name] = val
                break
        if field_name not in result:
            for v in reports.values():
                if isinstance(v, str):
                    val = _match_price(v, aliases)
                    if val:
                        result[field_name] = val
                        break

    # 2c) 评分/置信度/风险
    for aliases, field_name in score_aliases:
        if result.get(field_name):
            continue
        for module_text in _priority_texts():
            val = _match_score(module_text, aliases)
            if val and not result.get(field_name):
                result[field_name] = val
                break
        if field_name not in result:
            for v in reports.values():
                if isinstance(v, str):
                    val = _match_score(v, aliases)
                    if val:
                        result[field_name] = val
                        break

    # 3) 最后从 combined_text 中尝试提取评级（例如 "1. 操作建议：买入"）
    if not result.get("评级"):
        combined_text = "\n".join(
            v for v in reports.values() if isinstance(v, str)
        )
        val = _match_rating(combined_text, ["操作建议", "评级", "投资建议", "建议"])
        if val:
            final_rating = _normalize_rating(val)
            result["评级"] = final_rating
            result["操作建议"] = final_rating
            result["action"] = final_rating

    # 4) 补充英文字段名兼容（便于前端老代码继续工作）
    if "止盈目标" in result:
        num = re.search(r"(\d+(?:\.\d+)?)", result["止盈目标"])
        if num:
            result["target_price"] = num.group(1)
    if "止损价格" in result:
        num = re.search(r"(\d+(?:\.\d+)?)", result["止损价格"])
        if num:
            result["stop_loss"] = num.group(1)

    # 5) 提取持仓者建议和空仓者建议（使用专门的提取函数）
    holder_modules = ["research_team_decision", "final_trade_decision", "trader_investment_plan", "investment_plan"]
    empty_modules = ["research_team_decision", "final_trade_decision", "trader_investment_plan", "investment_plan"]
    
    if not result.get("持仓者建议"):
        for key in holder_modules:
            module_text = reports.get(key)
            if isinstance(module_text, str):
                extracted = _extract_holder_empty_advice(module_text, "持仓者建议")
                if extracted:
                    result["持仓者建议"] = extracted
                    break
    
    if not result.get("空仓者建议"):
        for key in empty_modules:
            module_text = reports.get(key)
            if isinstance(module_text, str):
                extracted = _extract_holder_empty_advice(module_text, "空仓者建议")
                if extracted:
                    result["空仓者建议"] = extracted
                    break

    return result


def _match_rating(text: str, aliases: List[str]) -> Optional[str]:
    """
    从文本中抽取"操作建议/评级"的关键字（买入/持有/卖出等）。
    优先级：精确匹配标题行（含下一行内容）> 标题行带冒号 > 研究经理结论搜索 > 关键词搜索
    """
    if not text:
        return None

    # 0) 最可靠的格式：**数字. 操作建议** 后面跟换行后的内容
    #    例：**7. 操作建议**\n买入  或  **操作建议**\n强烈卖出
    for alias in aliases:
        patterns = [
            # 格式1：**7. 操作建议** 后换行跟评级词
            r"(?:^|\n)\s*\*\*\s*(?:\d+[\.、]\s*)?" + re.escape(alias) + r"\s*\*\*\s*[\r\n]+\s*([^\s，。；,;（(【【\*\#]{1,30})",
            # 格式2：**操作建议：**买入 （星号内带冒号）
            r"(?:^|\n)\s*\*\*\s*(?:\d+[\.、]\s*)?" + re.escape(alias) + r"\s*[:：]\s*\*\*\s*([^\s，。；,;（(]{1,30})",
            # 格式3：**7. 操作建议：** 强烈买入
            r"(?:^|\n)\s*\*\*\s*(?:\d+[\.、]\s*)?" + re.escape(alias) + r"[:：]\s*\*\*\s*([^\s，。；,;（(]{1,30})",
        ]
        for pattern in patterns:
            try:
                m = re.search(pattern, text)
                if m:
                    val = m.group(1).strip()
                    val = re.sub(r'[\*_#\s]+', '', val).strip()
                    if val and 0 < len(val) <= 20:
                        return val
            except re.error:
                continue

    # 1) 标题行带冒号的格式
    for alias in aliases:
        patterns = [
            r"(?:^|\n)\s*\*?\s*(?:\d+[\.、]\s*)?\*?\s*" + re.escape(alias) +
            r"\s*\*?\s*[:：]\s*([^\n，。；,;（(]{0,60})",
            r"(?:^|\n)\s*【" + re.escape(alias) + r"】\s*([^\n，。；,;（(]{0,60})",
            r"(?:^|\n)\s*\*\*" + re.escape(alias) + r"\*\*\s*[:：]\s*([^\n，。；,;（(]{0,60})",
        ]
        for pattern in patterns:
            try:
                m = re.search(pattern, text)
                if m:
                    val = m.group(1).strip()
                    if val:
                        val = re.sub(r'[\*_#]+', '', val).strip()
                        if len(val) <= 20:
                            return val
                        # 如果内容太长，提取其中的评级关键词
                        for kw in ["强烈买入", "强烈卖出", "买入", "卖出", "持有", "观望", "减仓", "加仓"]:
                            if kw in val:
                                return kw
            except re.error:
                continue

    # 2) 搜索研究经理/最终决策中的结论
    manager_patterns = [
        r"研究经理.*结论[\s\S]{0,200}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
        r"最终决策[\s\S]{0,200}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
        r"最终投资决策[\s\S]{0,200}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
        r"综合判断[\s\S]{0,100}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
        r"综合评估[\s\S]{0,100}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
        r"投资建议[\s\S]{0,100}?(强烈买入|强烈卖出|买入|卖出|持有|观望|减仓|加仓)",
    ]

    for pattern in manager_patterns:
        try:
            m = re.search(pattern, text)
            if m:
                return m.group(1)
        except re.error:
            continue

    # 3) 搜索明确的结论行
    conclusion_patterns = [
        r"(?:^|\n)\s*\*?结论\s*\*?[:：]\s*([^\n]{0,80})",
        r"(?:^|\n)\s*\*?总结\s*\*?[:：]\s*([^\n]{0,80})",
    ]

    for pattern in conclusion_patterns:
        try:
            m = re.search(pattern, text)
            if m:
                val = m.group(1).strip()
                if val:
                    for keyword in ["强烈买入", "强烈卖出", "买入", "卖出", "持有", "观望", "减仓", "加仓"]:
                        if keyword in val:
                            return keyword
        except re.error:
            continue

    # 4) 兜底：从文本中搜索中文评级词（优先匹配完整词）
    keywords = ["强烈买入", "强烈卖出", "买入", "卖出", "持有", "观望", "减仓", "加仓"]
    for keyword in keywords:
        pattern = r'(?:^|\s|[，。；！？\n])' + re.escape(keyword) + r'(?:$|\s|[，。；！？\n])'
        try:
            if re.search(pattern, text):
                return keyword
        except re.error:
            continue

    return None


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
            # 🔥 合并顶层的 decision/detailed_analysis 到 reports，便于统一抽取
            _decision = r.get("decision") or r.get("detailed_analysis") or r.get("final_decision")
            _combined_for_extract = dict(report["reports"])
            if isinstance(_decision, dict) and _decision:
                _combined_for_extract["decision"] = _decision
            # 🔥 从 markdown 子报告中抽取结构化字段（核心洞察、策略点位等）
            _extracted = extract_structured_fields(_combined_for_extract)
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
            # 🔥 合并顶层的 decision/detailed_analysis 到 reports，便于统一抽取
            _decision = doc.get("decision") or doc.get("detailed_analysis") or doc.get("final_decision")
            _combined_for_extract = dict(report["reports"])
            if isinstance(_decision, dict) and _decision:
                _combined_for_extract["decision"] = _decision
            # 🔥 从 markdown 子报告中抽取结构化字段（核心洞察、策略点位、止盈止损等）
            _extracted = extract_structured_fields(_combined_for_extract)
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
    - markdown: Markdown 格式（默认，全中文标题）
    - json: JSON 格式（包含完整数据，中文字段友好）
    - docx: Word 文档格式（全中文）
    - pdf: PDF 格式（全中文）
    """
    try:
        logger.info(f"📥 下载报告: {report_id}, 格式: {format}")

        db = get_mongo_db()

        # 查询报告（支持多种ID）
        query = _build_report_query(report_id)
        doc = await db.analysis_reports.find_one(query)

        if not doc:
            raise HTTPException(status_code=404, detail="报告不存在")

        stock_symbol = doc.get("stock_symbol", "未知")
        analysis_date = doc.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))

        # 统一的英文 -> 中文报告字段映射（同步 report_exporter.py 中的定义）
        FIELD_MAP = {
            "analysis_id": "分析编号",
            "stock_symbol": "股票代码",
            "stock_name": "股票名称",
            "market_type": "市场类型",
            "analysis_date": "分析日期",
            "created_at": "创建时间",
            "updated_at": "更新时间",
            "analysts": "分析师团队",
            "research_depth": "研究深度",
            "status": "状态",
            "summary": "执行摘要",
            "executive_summary": "执行摘要",
            "recommendation": "投资建议",
            "confidence_score": "置信度",
            "confidence": "置信度",
            "risk_level": "风险等级",
            "key_points": "核心要点",
            "action": "操作建议",
            "target_price": "目标价",
            "stop_loss": "止损价",
            "execution_time": "执行耗时(秒)",
            "tokens_used": "Token消耗",
            "source": "数据来源",
            "task_id": "任务编号",
            "decision": "决策详情",
            "state": "分析状态",
            "detailed_analysis": "详细分析",
            "model_info": "模型信息",
            "reports": "各模块报告",
        }

        def translate_key(key: str) -> str:
            if key in FIELD_MAP:
                return FIELD_MAP[key]
            cleaned = key.replace("_report", "").replace("_analysis", "").replace("_state", "")
            if cleaned in FIELD_MAP:
                return FIELD_MAP[cleaned]
            return key

        if format == "json":
            # JSON格式下载：使用中文字段，保持易读性
            from urllib.parse import quote
            try:
                from app.utils.report_exporter import report_exporter
                title_map = report_exporter.MODULE_TITLE_MAP
            except Exception:
                title_map = {}

            def recursive_zh(obj: Any) -> Any:
                if isinstance(obj, dict):
                    return {
                        translate_key(str(k)) if not isinstance(k, str) else
                        (title_map.get(str(k), translate_key(str(k)))
                         if str(k) in title_map else translate_key(str(k))):
                            recursive_zh(v)
                        for k, v in obj.items()
                    }
                if isinstance(obj, list):
                    return [recursive_zh(x) for x in obj]
                return obj

            translated = recursive_zh(dict(doc))
            content = json.dumps(translated, ensure_ascii=False, indent=2, default=str)
            filename = f"{stock_symbol}_{analysis_date}_报告.json"
            media_type = "application/json"

            # 对中文文件名进行URL编码
            filename_encoded = quote(filename)

            # 返回文件流
            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"}
            )

        elif format == "markdown":
            # Markdown格式下载 — 使用统一的报告导出器（全中文标题）
            from urllib.parse import quote
            from app.utils.report_exporter import report_exporter
            content = report_exporter.generate_markdown_report(doc)
            filename = f"{stock_symbol}_{analysis_date}_报告.md"
            media_type = "text/markdown"

            # 对中文文件名进行URL编码
            filename_encoded = quote(filename)

            def generate():
                yield content.encode('utf-8')

            return StreamingResponse(
                generate(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"}
            )

        elif format == "docx":
            # Word 文档格式下载
            from urllib.parse import quote
            from app.utils.report_exporter import report_exporter

            try:
                # 生成 Word 文档（Markdown -> Docx，全中文）
                docx_content = report_exporter.generate_docx_report(doc)
                filename = f"{stock_symbol}_{analysis_date}_报告.docx"

                # 对中文文件名进行URL编码
                filename_encoded = quote(filename)

                # 返回文件流
                def generate():
                    yield docx_content

                return StreamingResponse(
                    generate(),
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"}
                )
            except Exception as e:
                logger.error(f"❌ Word 文档生成失败: {e}")
                raise HTTPException(status_code=500, detail=f"Word 文档生成失败: {str(e)}")

        elif format == "pdf":
            # PDF 格式下载
            from app.utils.report_exporter import report_exporter
            from urllib.parse import quote

            try:
                # 生成 PDF 文档（基于中文 Markdown -> HTML -> PDF）
                pdf_content = report_exporter.generate_pdf_report(doc)
                # 清理文件名中的非ASCII字符
                safe_symbol = ''.join(c if ord(c) < 128 else 'stock' for c in str(stock_symbol))
                filename = f"{safe_symbol}_{analysis_date}_report.pdf"
                # 对中文文件名进行URL编码（用于 Content-Disposition）
                filename_zh = f"{stock_symbol}_{analysis_date}_报告.pdf"
                filename_zh_encoded = quote(filename_zh)

                # 返回文件流
                def generate():
                    yield pdf_content

                return StreamingResponse(
                    generate(),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}; filename*=UTF-8''{filename_zh_encoded}"
                    }
                )
            except FileNotFoundError:
                logger.error("❌ wkhtmltopdf 命令未找到")
                raise HTTPException(
                    status_code=400,
                    detail="PDF 导出功能不可用：缺少 wkhtmltopdf。请先安装后再试。"
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
