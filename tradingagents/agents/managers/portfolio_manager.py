"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Two-phase process:
1. Risk Manager phase: produces a structured RiskControlDecision with position
   sizing limits and stop-loss levels.
2. Portfolio Manager phase: makes the final trading decision, respecting the
   risk constraints set by phase 1.

Uses LangChain's ``with_structured_output`` so the LLM produces typed schemas
directly, in two calls. The results are rendered back to markdown for storage
in ``risk_control_decision`` and ``final_trade_decision``. When a provider does
not expose structured output, the agent falls back gracefully to free-text.
"""

from __future__ import annotations

from tradingagents.agents.schemas import (
    PortfolioDecision,
    RiskControlDecision,
    render_pm_decision,
    render_risk_control_decision,
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
    # Phase 1: Risk Manager uses RiskControlDecision schema
    risk_llm = bind_structured(llm, RiskControlDecision, "Risk Manager")
    # Phase 2: Portfolio Manager uses PortfolioDecision schema
    portfolio_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lessons from prior decisions and outcomes:\n{past_context}\n"
            if past_context
            else ""
        )

        # ============================================================
        # Phase 1: Risk Manager - Set Risk Constraints (NOT final decision)
        # ============================================================
        risk_judge_prompt = f"""As the Risk Manager, your job is to set **risk constraints**, NOT to make the final trading decision.

Your role is pure risk control:
- Set maximum position size limits (hard constraint)
- Recommend position size based on risk/reward (soft guidance)
- Define stop-loss level (protection against catastrophic losses)
- Calculate max acceptable loss as % of portfolio
- Identify worst-case scenarios and estimate loss magnitude
- Provide risk mitigation strategies

⚠️ You are NOT deciding whether to buy/sell — that's the Portfolio Manager's job.
⚠️ You are NOT analyzing upside potential — that's the researchers' job.
⚠️ You ONLY set risk parameters that the Portfolio Manager must respect.

{instrument_context}

---

**A-Stock Trading Constraints** (must factor into your risk assessment):
- T+1 settlement: shares bought today cannot be sold until the next trading day
- Daily price limits: main board ±10%, STAR/ChiNext ±20%, ST stocks ±5%
- Minimum lot size: 100 shares (1 手) for main board; 200 shares for STAR/ChiNext
- Trading hours: 09:30-11:30, 13:00-15:00 (Beijing time)
- ST/delisting risk: ST or *ST status signals regulatory warning; factor into position sizing
- Margin eligibility: not all A-shares are margin-eligible; assume cash-only unless stated

---

**Risk Rating Scale** (based on RISK PROFILE, not upside):
- **Buy**: Low risk profile (stable fundamentals, low volatility, no major overhangs)
- **Overweight**: Manageable risk (some concerns but overall safe)
- **Hold**: Moderate risk (balanced risk/reward, maintain with caution)
- **Underweight**: Elevated risk (multiple risk factors present)
- **Sell**: High risk (structural risks like consecutive limit-down risk, major policy reversal, ST status)

**Context:**
- Research Manager's investment plan: **{research_plan}**
- Trader's transaction proposal: **{trader_plan}**
{lessons_line}
**Risk Analysts Debate History:**
{history}

---

Output a structured RiskControlDecision with specific numbers (position size %, stop-loss %, max loss %). Ground every constraint in specific evidence from the debate.{get_language_instruction()}"""

        risk_control_decision = invoke_structured_or_freetext(
            risk_llm,
            llm,
            risk_judge_prompt,
            render_risk_control_decision,
            "Risk Manager",
        )

        # ============================================================
        # Phase 2: Portfolio Manager - Make Final Decision (respecting risk constraints)
        # ============================================================
        final_decision_prompt = f"""As the Portfolio Manager, your job is to make the **final trading decision**, respecting the risk constraints set by the Risk Manager.

⚠️ You MUST respect these hard constraints from the Risk Manager:
- Maximum position size: do NOT exceed this limit
- Stop-loss level: you can tighten it but NOT loosen it
- Max acceptable loss: your position size must respect this

You CAN:
- Choose to be more conservative than the Risk Manager's recommendations
- Tighten stop-loss beyond the Risk Manager's suggestion
- Lower position size if you disagree with the upside potential

You CANNOT:
- Exceed the max position size (this is a hard limit)
- Loosen the stop-loss level (this is a safety constraint)
- Ignore the worst-case scenario analysis

{instrument_context}

---

**A-Stock Trading Constraints** (must factor into your decision):
- T+1 settlement: shares bought today cannot be sold until the next trading day
- Daily price limits: main board ±10%, STAR/ChiNext ±20%, ST stocks ±5%
- Minimum lot size: 100 shares (1 手) for main board; 200 shares for STAR/ChiNext
- Trading hours: 09:30-11:30, 13:00-15:00 (Beijing time)
- ST/delisting risk: ST or *ST status signals regulatory warning; factor into position sizing
- Margin eligibility: not all A-shares are margin-eligible; assume cash-only unless stated

---

**Rating Scale** (based on UPSIDE vs DOWNSIDE balance):
- **Buy**: Strong conviction in upside, risk constraints allow significant position
- **Overweight**: Favorable upside, can take recommended position size
- **Hold**: Balanced upside/downside, maintain with moderate position
- **Underweight**: Upside limited or downside elevated, reduce exposure
- **Sell**: Downside dominates or risk constraints prohibit meaningful position

**Context:**
- Research Manager's investment plan: **{research_plan}**
- Trader's transaction proposal: **{trader_plan}**
- **Risk Manager's constraints (MUST RESPECT):** **{risk_control_decision}**
{lessons_line}
**Risk Analysts Debate History:**
{history}

---

Make the final call. Your position size MUST be ≤ Risk Manager's max_position_size. Your stop-loss MUST be ≥ Risk Manager's stop_loss_level (i.e., tighter or equal).{get_language_instruction()}"""

        final_trade_decision = invoke_structured_or_freetext(
            portfolio_llm,
            llm,
            final_decision_prompt,
            render_pm_decision,
            "Portfolio Manager",
        )

        new_risk_debate_state = {
            "judge_decision": risk_control_decision,
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
            "risk_control_decision": risk_control_decision,
            "final_trade_decision": final_trade_decision,
        }

    return portfolio_manager_node
