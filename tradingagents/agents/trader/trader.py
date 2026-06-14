"""Trader：将研究经理的投资计划转化为具体交易建议。

**daily_stock_analysis 风格**：输出完全中文，结构化字段包括
「操作建议 / 核心理由 / 理想买入 / 二次买入 / 止损价格 / 止盈目标 / 支撑位 / 阻力位 / 建议仓位 / 持仓周期」。
"""

from __future__ import annotations

import functools

from langchain_core.messages import AIMessage

from tradingagents.agents.schemas import TraderProposal, render_trader_proposal
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_trader(llm):
    structured_llm = bind_structured(llm, TraderProposal, "Trader")

    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        investment_plan = state["investment_plan"]

        # 收集 A 股具体的分析师报告（中文报告名）
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")
        market_report = state.get("market_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")

        # 构建 A 股上下文块
        astock_context_parts = []
        if market_report:
            astock_context_parts.append(f"技术分析报告:\n{market_report}")
        if fundamentals_report:
            astock_context_parts.append(f"基本面分析报告:\n{fundamentals_report}")
        if sentiment_report:
            astock_context_parts.append(f"市场情绪报告:\n{sentiment_report}")
        if news_report:
            astock_context_parts.append(f"新闻公告报告:\n{news_report}")
        if policy_report:
            astock_context_parts.append(f"政策分析报告:\n{policy_report}")
        if hot_money_report:
            astock_context_parts.append(f"资金流向报告:\n{hot_money_report}")
        if lockup_report:
            astock_context_parts.append(f"限售解禁报告:\n{lockup_report}")
        astock_context = "\n\n".join(astock_context_parts)
        lang_instr = get_language_instruction()
        extra_section = ("参考分析师报告:\n" + astock_context + "\n\n") if astock_context else ""

        prompt = f"""你是一位活跃于 A 股市场的交易员（Trader）。
请基于研究经理的投资计划和各分析师报告，制定具体、可执行的交易建议。

**公司**：{company_name}
{instrument_context}

---

**A 股交易特殊规则（必须纳入交易计划考虑）**：
- T+1 交易：当日买入次日才能卖出，短线策略的灵活性受限
- 涨跌停：主板 ±10%，科创 / 创业板 ±20%，ST ±5%。触及涨跌停后流动性可能枯竭
- 最低一手：100 股（主板）或 200 股（科创 / 创业板）
- 交易时段：09:30-11:30，13:00-15:00 北京时间
- 资金规则：非所有标的可融资融券，默认按纯现金考虑

---

**结构化输出要求（严格遵守字段定义，所有内容用中文）**：
1. **操作建议**：交易方向。严格从「买入 / 持有 / 卖出」选一个
2. **核心理由**：2-4 句中文理由，锚定在分析师报告和研究计划中的证据
3. **理想买入**（建议给出）：首次建仓理想价格（标的计价货币，如 CNY）。参考：当前价 × 0.95~1.00
4. **二次买入**（建议给出）：第二档加仓价格。参考：当前价 × 0.90~0.93
5. **止损价格**（建议给出）：无条件止损价格。参考：当前价 × 0.88~0.92 或最近支撑位
6. **止盈目标**（建议给出）：止盈目标价格。参考：当前价 × 1.15~1.25 或最近阻力位
7. **支撑位**（建议给出）：关键支撑位（近期低点 / 均线支撑）
8. **阻力位**（建议给出）：关键阻力位（近期高点 / 均线压力）
9. **建议仓位**（建议给出）：如「轻仓 3%」「半仓参与」
10. **持仓周期**（建议给出）：如「3-6 个月」「1-2 周」

**重要提示**：
- 价格应与标的当前价格合理相关（A 股标的用 CNY）
- 仓位建议需考虑涨跌停风险和 T+1 限制
- 所有文字内容必须使用中文

---

**研究经理的投资计划**：
{investment_plan}

---

{extra_section}请制定明确、具体、可执行的交易建议。
{lang_instr}"""

        trader_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_trader_proposal,
            "Trader",
        )

        return {
            "messages": [AIMessage(content=trader_plan)],
            "trader_investment_plan": trader_plan,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
