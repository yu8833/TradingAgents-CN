"""Research Manager：将多空辩论合成结构化投资计划。

**daily_stock_analysis 风格**：输出完全中文，结构化字段包括
「评级 / 核心洞察 / 战略行动 / 置信度 / 风险等级」。
"""

from __future__ import annotations

from tradingagents.agents.schemas import ResearchPlan, render_research_plan
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_research_manager(llm):
    structured_llm = bind_structured(llm, ResearchPlan, "Research Manager")

    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        lang_instr = get_language_instruction()

        investment_debate_state = state["investment_debate_state"]

        prompt = f"""你是一位经验丰富的 A 股研究经理（Research Manager）。
请基于多空辩论和各分析师报告，做出清晰、可执行的投资计划给交易员参考。

{instrument_context}

---

**A 股市场要点（必须纳入分析考虑）**：
- 涨跌停制度：主板 ±10%，科创 / 创业板 ±20%，ST ±5%
- T+1 交易：当天买入次日才能卖
- 资金流向：北向资金（外资流入 / 流出）是重要市场风向标
- 政策影响：国家产业政策、监管政策直接影响板块走势
- 情绪驱动：A 股散户占比高，情绪和题材短期影响力大
- 限售解禁：重要股东的解禁安排会造成阶段性抛压

---

**评级系统（必须严格选一个）**：
- **强烈买入**：市场与标的一致看多，且有明确催化因素
- **买入**：基本面和技术面支持上涨，可逐步建仓
- **持有**：多空力量相对平衡，保持现有仓位观望
- **减仓**：估值偏高或出现利空信号，建议逐步降低仓位
- **卖出**：明确看空信号，建议清仓离场

---

**输出字段（严格遵守，所有内容用中文）**：
1. **rating**：5 档评级之一（强烈买入 / 买入 / 持有 / 减仓 / 卖出）（必填）
2. **核心洞察**：2-4 句中文总结，描述市场主要矛盾、资金态度、关键催化事件
3. **战略行动**：给交易员的具体中文操作步骤和仓位管理建议

**可选增强字段**（如果能评估，请给出）：
- **confidence_score**：0.0-1.0，对建议的信心
- **risk_level**：低 / 中 / 高

**重要提示**：
- 当辩论明显偏向一边时（如多头论据压倒性占优），请给出明确方向（强烈买入 / 买入 / 减仓 / 卖出），不要犹豫选持有
- 只有当两边论据相对平衡、无明显优势时，再选持有
- 建议应与 A 股特殊规则一致（如考虑 T+1 的短线限制）

---

**多空辩论历史**：
{history}

{lang_instr}"""

        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_research_plan,
            "Research Manager",
        )

        new_investment_debate_state = {
            "judge_decision": investment_plan,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": investment_plan,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": investment_plan,
        }

    return research_manager_node
