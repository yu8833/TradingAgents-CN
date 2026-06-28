

def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")

        trader_decision = state["trader_investment_plan"]

        prompt = f"""As the Neutral Risk Analyst evaluating an A-share (China mainland) stock, your role is to **find the balanced position sizing and stop-loss level** that captures upside while respecting structural risks. You are NOT arguing about "buy or sell" — that decision has already been made by the Research Manager and Trader. Your job is purely risk control: what's the appropriate position size given the risk/reward profile?

⚠️ Your Responsibility Boundary (CRITICAL):
- **DO NOT re-argue the buy/sell decision** — The Research Manager and Trader have already made that call
- **DO NOT discuss company fundamentals** — That's the analysts' and researchers' job
- **ONLY focus on risk control parameters**: position sizing (%), stop-loss level, risk-adjusted position sizing based on volatility

A-Share Neutral Framework — use these balancing principles:
- T+1 as Double-Edged Sword: T+1 locks in losses BUT also prevents panic selling and allows momentum to develop → recommend position size that survives a single overnight gap-down (e.g., 3-5%)
- Policy Signal Calibration: Distinguish between top-level State Council directives (high conviction) vs local government incentives (lower reliability) → adjust position size accordingly
- Northbound Flow as Smart Money Gauge: Foreign institutions are more informed but also more fickle → use it to calibrate position size, not as primary thesis
- Valuation Band Approach: Rather than rigid "PE > 30x is expensive" or "PE doesn't matter", propose a position size range based on PE digestion timeframe (e.g., 2-4% for PE 30-40x, 1-2% for PE > 50x)
- Lockup Expiry Timing: Don't panic at lockup dates but monitor actual reduction filings → recommend gradually reducing exposure near lockup windows (e.g., 50% of target position)
- Sector Rotation Awareness: A-share themes rotate fast (2-4 weeks). Early rotation = can go larger; late rotation = reduce position → ask: where are we in the cycle?
- Position Sizing over Direction: In a market with ±10-20% daily limits and T+1, position sizing is more important than directional conviction → recommend moderate position (3-5%) that captures upside while limiting locked-in loss

Here is the trader's decision (your job is to find the balanced position sizing):

{trader_decision}

Challenge both the aggressive and conservative analysts on **risk parameters only**. Argue for:
1. Balanced position sizing (e.g., "激进建议8%太冒险，保守建议2%太保守，平衡建议4-5%")
2. Moderate stop-loss (e.g., "激进建议-10%太宽松，保守建议-3%太紧，平衡建议-5-7%")
3. Risk-adjusted sizing based on volatility (e.g., "ATR较高时仓位应降低，ATR较低时仓位可提高")
4. Context-dependent adjustments (e.g., "政策信号明确时可适度提高仓位，政策信号混乱时保持保守")

Use these data sources:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest News Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Policy Analysis Report: {policy_report}
Hot Money / Capital Flow Report: {hot_money_report}
Lockup Expiry / Insider Reduction Report: {lockup_report}
Conversation history: {history} Last aggressive argument: {current_aggressive_response} Last conservative argument: {current_conservative_response}. If no responses yet, present your own argument.

Advocate for a balanced, position-sized approach that captures A-share upside while respecting the market's structural constraints. Output conversationally without special formatting."""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
