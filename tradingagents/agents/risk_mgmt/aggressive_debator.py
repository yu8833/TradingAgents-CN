

def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")

        trader_decision = state["trader_investment_plan"]

        prompt = f"""As the Aggressive Risk Analyst evaluating an A-share (China mainland) stock, your role is to advocate for **larger position sizing and looser stop-loss levels** when the upside potential is strong. You are NOT arguing about "buy or sell" — that decision has already been made by the Research Manager and Trader. Your job is purely risk control: how big can we safely go, and where should we place the stop-loss?

⚠️ Your Responsibility Boundary (CRITICAL):
- **DO NOT re-argue the buy/sell decision** — The Research Manager and Trader have already made that call
- **DO NOT discuss company fundamentals** — That's the analysts' and researchers' job
- **ONLY focus on risk control parameters**: position sizing (%), stop-loss level, max acceptable loss, risk/reward ratio

A-Share Aggressive Risk Framework — use these arguments to justify larger positions:
- Limit-Up Momentum: If the stock is showing consecutive limit-ups with volume confirmation, a larger position (8-10%) is justified because momentum reduces downside risk
- Policy Backing: When Beijing backs a sector (AI, chips, new energy), the policy floor reduces downside risk → can justify larger position
- Hot Money Conviction: If top hot money seats (游资席位) are in with strong reason tags, their exit risk is lower in the short term → larger position acceptable
- Northbound Flow: If foreign institutions via Stock Connect are net buying, this confirms smart money confidence → can go larger
- PE Digestion Feasibility: If forward PE is reasonable (<30x) or PEG < 1, the valuation risk is low → can take larger position
- Volume Trend: If volume is expanding with price rising (量价齐升), the trend is healthy → can risk more

Here is the trader's decision (your job is to assess if this position sizing is too conservative):

{trader_decision}

Challenge the conservative and neutral analysts on **risk parameters only**. Argue for:
1. Larger position sizing (e.g., "保守分析师建议3%仓位太低，建议提高到5-8%")
2. Looser stop-loss (e.g., "止损位设置在-5%太紧，建议放宽到-8%以避免被洗盘")
3. Higher acceptable max loss (e.g., "最大可接受亏损2%太保守，建议提高到3%")
4. Better risk/reward ratio justification (e.g., "风险/回报比1:2不够吸引，当前设置是1:3")

Use these data sources:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest News Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Policy Analysis Report: {policy_report}
Hot Money / Capital Flow Report: {hot_money_report}
Lockup Expiry / Insider Reduction Report: {lockup_report}
Conversation history: {history} Last conservative argument: {current_conservative_response} Last neutral argument: {current_neutral_response}. If no responses yet, present your own argument.

Engage actively, debate persuasively, and assert why aggressive positioning is optimal for this A-share opportunity. Output conversationally without special formatting."""

        response = llm.invoke(prompt)

        argument = f"Aggressive Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
