"""Portfolio Manager：合成风险分析师辩论为最终投资决策。

**daily_stock_analysis 风格**：输出完全中文，结构化字段包括
「核心洞察 / 趋势预测 / 策略点位 / 理想买入 / 二次买入 / 止损价格 / 止盈目标」。
"""

from __future__ import annotations

from tradingagents.agents.schemas import (
    PortfolioDecision,
    render_pm_decision,
)
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm):
    structured_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- 历史决策复盘与经验教训：\n{past_context}\n"
            if past_context
            else ""
        )
        lang_instr = get_language_instruction()

        prompt = (
            "你是资深的 A 股组合经理（Portfolio Manager）。"
            "请基于风险分析师辩论、研究计划和交易建议，做出最终投资决策。\n\n"
            f"{instrument_context}\n\n"
            "---\n\n"
            "**A 股市场特殊规则（必须作为决策因素考虑）**：\n"
            "- T+1 交易：当天买入的标的次日才能卖出，短线策略受限\n"
            "- 涨跌停限制：主板 ±10%，科创 / 创业板 ±20%，ST ±5%。触及涨跌停后流动性可能枯竭\n"
            "- 最低一手：主板 100 股，科创 / 创业板 200 股\n"
            "- 交易时段：09:30-11:30，13:00-15:00（北京时间）\n"
            "- ST / *ST 风险：监管风险，需降低仓位或回避\n"
            "- 资金准入：非所有 A 股均可融资融券，默认按纯现金考虑\n\n"
            "---\n\n"
            "**5 档评级系统（必须五选一）**：\n"
            "- **强烈买入**：市场与标的一致看多，且有明确催化因素\n"
            "- **买入**：基本面和技术面支持上涨，可逐步建仓\n"
            "- **持有**：多空力量相对平衡，保持现有仓位观望\n"
            "- **减仓**：估值偏高或出现利空信号，建议逐步降低仓位\n"
            "- **卖出**：明确看空信号，建议清仓离场\n\n"
            "---\n\n"
            "**结构化输出要求（必须严格遵守字段定义，所有内容用中文）**：\n"
            "1. **评级**：选「强烈买入 / 买入 / 持有 / 减仓 / 卖出」之一\n"
            "2. **核心洞察**：2-4 句中文行动总结，描述市场主要矛盾、资金态度、关键催化事件\n"
            "3. **投资逻辑**：详细中文投资论证，锚定在风险辩论和研究计划的证据中\n"
            "4. **趋势预测**：未来 1-4 周的趋势判断与催化因素（中文）\n"
            "5. **策略点位**：关键支撑 / 阻力 / 均线价位的中文解释\n"
            "6. **理想买入**（REQUIRED，必填）：首次建仓理想价格。参考：当前价 × 0.95~1.00。如 21.50\n"
            "7. **二次买入**（REQUIRED，必填）：第二档加仓价格。参考：当前价 × 0.90~0.93。如 19.80\n"
            "8. **止损价格**（REQUIRED，必填）：无条件止损价格。参考：当前价 × 0.88~0.92。如 18.20\n"
            "9. **止盈目标**（REQUIRED，必填）：止盈目标价格。参考：当前价 × 1.15~1.25。如 25.80\n"
            "10. **持仓周期**（可选）：如「3-6 个月」「1-2 周」\n"
            "11. **置信度**（可选）：0.0~1.0，两位小数\n"
            "12. **风险等级**（可选）：低 / 中 / 高\n"
            "13. **风险提示**（可选）：为什么给出这个风险等级的中文说明\n"
            "14. **技术面评分** / **基本面评分** / **情绪面评分** / **政策面评分**（可选）：各维度 0.0~1.0\n\n"
            "**重要提示**：\n"
            "- 理想买入、二次买入、止损价格、止盈目标**均必填**，不能省略、不能为 None 或 0\n"
            "- 价格应与标的当前市场价格合理相关（A 股标的使用人民币计价）\n"
            "- 所有评分都必须在 0.0~1.0 之间（保留两位小数，如 0.75）\n"
            "- 所有文字内容必须使用中文\n\n"
            "---\n\n"
            "**输入上下文**：\n"
            f"- 研究经理的投资计划：**{research_plan}**\n"
            f"- 交易员的交易建议：**{trader_plan}**\n"
            f"{lessons_line}"
            "**风险分析师辩论历史**：\n"
            f"{history}\n\n"
            "---\n\n"
            "**请做出明确、具体、基于证据的决策。**\n"
            "价格点位基于当前市场价格、技术分析和基本面估值综合判断。\n"
            f"{lang_instr}"
        )

        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_pm_decision,
            "Portfolio Manager",
        )

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
        }

    return portfolio_manager_node


def get_language_instruction_safe():
    """兼容性垫片：确保模块中同时提供此符号以便其它文件引用。"""
    return get_language_instruction()
