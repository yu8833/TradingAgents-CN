

def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        policy_report = state.get("policy_report", "")
        hot_money_report = state.get("hot_money_report", "")
        lockup_report = state.get("lockup_report", "")

        trader_decision = state["trader_investment_plan"]

        prompt = f"""As the Conservative Risk Analyst evaluating an A-share (China mainland) stock, your primary objective is to **restrict position sizing and tighten stop-loss levels** to protect assets. You are NOT arguing about "buy or sell" — that decision has already been made by the Research Manager and Trader. Your job is purely risk control: what's the maximum safe position size, and where should the hard stop-loss be?

⚠️ Your Responsibility Boundary (CRITICAL):
- **DO NOT re-argue the buy/sell decision** — The Research Manager and Trader have already made that call
- **DO NOT discuss company fundamentals** — That's the analysts' and researchers' job
- **ONLY focus on risk control parameters**: position sizing (%), stop-loss level, max acceptable loss, worst-case scenarios

A-Share Conservative Framework — use these structural risks to argue for smaller positions:
- T+1 Settlement Lock: Any position taken today CANNOT be exited until tomorrow. If the stock gaps down at open, losses are locked in → recommend position size <3% to survive a single overnight gap-down
- Daily Price Limit Trap (涨跌停板): If a stock hits limit-down (-10%/-20%), sell orders cannot execute — you are trapped. Multiple limit-downs = catastrophic losses → recommend position size that can survive 2 consecutive limit-downs
- Lockup Expiry Overhang: Large lockup expiries create massive sell pressure. Even if insiders haven't sold, the option to sell depresses sentiment → recommend reducing position before lockup dates
- Policy Reversal Risk: A-shares are a policy market (政策市). Sector support can turn to crackdown overnight → recommend smaller position when policy signals are mixed
- Hot Money Exit Risk: Hot money moves fast in both directions. Retail investors are the last to know when hot money exits → recommend position size that accounts for sudden exit scenario
- Valuation Risk: PE > 50x with PEG > 2 is speculative territory → recommend position size <2% for speculative stocks
- ST/Delisting Risk: ST status triggers ±5% limits and forced selling → recommend position size <1% for ST stocks

Here is the trader's decision (your job is to assess if this position sizing is too aggressive):

{trader_decision}

Counter the aggressive and neutral analysts on **risk parameters only**. Argue for:
1. Smaller position sizing (e.g., "激进分析师建议8%仓位太高，建议降低到2-3%以应对T+1风险")
2. Tighter stop-loss (e.g., "止损位设置在-8%太宽松，建议收紧到-3%以保护本金")
3. Lower acceptable max loss (e.g., "最大可接受亏损5%太冒险，建议控制在1-2%")
4. Worst-case scenario analysis (e.g., "如果连续2天跌停板，当前仓位会导致亏损XX%，无法承受")

Use these data sources:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest News Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Policy Analysis Report: {policy_report}
Hot Money / Capital Flow Report: {hot_money_report}
Lockup Expiry / Insider Reduction Report: {lockup_report}
Conversation history: {history} Last aggressive argument: {current_aggressive_response} Last neutral argument: {current_neutral_response}. If no responses yet, present your own argument.

Demonstrate why a conservative stance is the safest path, especially given A-share market structure where downside protection mechanisms (stop-loss, same-day exit) are severely limited. Output conversationally without special formatting."""

        response = llm.invoke(prompt)

        argument = f"Conservative Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
