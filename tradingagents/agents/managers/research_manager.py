"""Research Manager: turns the bull/bear debate into a structured investment plan for the trader."""

from __future__ import annotations

from tradingagents.agents.schemas import ResearchPlan, render_research_plan
from tradingagents.agents.utils.agent_utils import build_instrument_context, get_language_instruction
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_research_manager(llm):
    structured_llm = bind_structured(llm, ResearchPlan, "Research Manager")

    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")

        investment_debate_state = state["investment_debate_state"]
        
        # 获取速览分析结果（如果有）
        quick_result = state.get("quick_analysis_result", {})
        quick_context_text = ""
        if quick_result and isinstance(quick_result, dict) and quick_result.get("buy_signal"):
            quick_context_text = f"""
---

**Quantitative Quick Scan (Baseline Reference):**
- Trend: {quick_result.get('trend_status', 'N/A')}
- Signal: {quick_result.get('buy_signal', 'N/A')}
- Score: {quick_result.get('signal_score', 'N/A')}/100
- Confidence: {quick_result.get('confidence', 'N/A')}%
- Summary: {quick_result.get('summary', 'N/A')}
- Key Prices: Support {quick_result.get('support_levels', ['N/A'])[0] if quick_result.get('support_levels') else 'N/A'} | Resistance {quick_result.get('resistance_levels', ['N/A'])[0] if quick_result.get('resistance_levels') else 'N/A'} | Stop Loss {quick_result.get('stop_loss', 'N/A')} | Target {quick_result.get('target', 'N/A')}

**Your Responsibility:**
1. Acknowledge the quick scan conclusion explicitly in your analysis
2. State clearly whether you "Agree", "Modify", or "Disagree" with the quick scan
3. If you modify or disagree, you MUST provide strong reasons supported by the debate evidence
4. Your final decision should generally align with the quick scan direction unless there is significant new evidence from the debate that changes the picture
"""

        prompt = f"""As the Research Manager and debate facilitator, your role is to critically evaluate this round of debate and deliver a clear, actionable investment plan for the trader.

{instrument_context}

Note: This is an A-share (China mainland) stock. Factor in regulatory policy impact, hot money / capital flow dynamics, and lockup expiry / insider reduction risks when synthesising the debate.
{quick_context_text}
---

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction in the bull thesis; recommend taking or growing the position
- **Overweight**: Constructive view; recommend gradually increasing exposure
- **Hold**: Balanced view; recommend maintaining the current position
- **Underweight**: Cautious view; recommend trimming exposure
- **Sell**: Strong conviction in the bear thesis; recommend exiting or avoiding the position

Commit to a clear stance whenever the debate's strongest arguments warrant one; reserve Hold for situations where the evidence on both sides is genuinely balanced.

---

**Debate History:**
{history}""" + get_language_instruction()

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
