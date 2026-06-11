import time
import json

from tradingagents.utils.logging_init import get_logger
from tradingagents.agents.utils.instrument_utils import build_instrument_context
from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.structured import get_structured_llm, parse_structured_output
from tradingagents.agents.utils.data_quality import (
    assess_report_quality,
    format_quality_report,
    DataQualityGrade,
    get_quality_weight,
)

logger = get_logger("default")


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        ticker = state["company_of_interest"]
        instrument_context = build_instrument_context(ticker)
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        # 数据质量评估
        market_quality = assess_report_quality(market_research_report, report_type="market")
        fundamentals_quality = assess_report_quality(fundamentals_report, report_type="fundamentals")
        
        logger.info(f"📊 [Research Manager] 数据质量评估:")
        logger.info(f"   - 市场报告: {market_quality.grade} ({market_quality.confidence_score:.1%})")
        logger.info(f"   - 基本面报告: {fundamentals_quality.grade} ({fundamentals_quality.confidence_score:.1%})")

        quality_warnings = []
        if market_quality.grade in [DataQualityGrade.D, DataQualityGrade.F]:
            quality_warnings.append(f"市场报告质量较低({market_quality.grade})，请减少依赖")
        if fundamentals_quality.grade in [DataQualityGrade.D, DataQualityGrade.F]:
            quality_warnings.append(f"基本面报告质量较低({fundamentals_quality.grade})，请减少依赖")

        if quality_warnings:
            quality_hint = "\n".join([f"⚠️ {warning}" for warning in quality_warnings])
        else:
            quality_hint = "✅ 所有报告数据质量良好"

        prompt = f"""作为投资组合经理和辩论主持人，您的职责是综合评估辩论双方的观点，并结合市场分析师的技术分析报告，给出客观、平衡的投资建议。

**重要原则**：
- **市场分析师的建议应作为重要参考**，而非被辩论双方的观点覆盖
- **持有是中性建议**，不需要比买入/卖出更强的理由
- **警惕辩论中的极端观点和主观臆测**（如"历史教训表明..."、"类似标的上..."等无数据支撑的说法）
- **综合权衡**，而非简单地选择辩论中最"响亮"的一方

**数据质量提示**：
{quality_hint}

**A股市场特别考虑**：
- T+1交易制度的影响
- 涨跌停板限制
- 北向资金流动作为聪明钱指标
- 估值区间方法
- 限售股解禁时间
- 行业轮动意识

以下是您对错误的过去反思：
\"{past_memory_str}\"

标的约束：
{instrument_context}

以下是综合分析报告：
市场研究：{market_research_report}

情绪分析：{sentiment_report}

新闻分析：{news_report}

基本面分析：{fundamentals_report}

以下是辩论：
辩论历史：
{history}

请用中文撰写所有分析内容和建议。"""

        prompt_length = len(prompt)
        estimated_tokens = int(prompt_length / 1.8)

        logger.info(f"📊 [Research Manager] Prompt 统计:")
        logger.info(f"   - 辩论历史长度: {len(history)} 字符")
        logger.info(f"   - 总 Prompt 长度: {prompt_length} 字符")
        logger.info(f"   - 估算输入 Token: ~{estimated_tokens} tokens")

        start_time = time.time()

        structured_llm = get_structured_llm(llm, PortfolioDecision)
        
        try:
            response = structured_llm.invoke(prompt)
            decision = parse_structured_output(response, PortfolioDecision)
            logger.info(f"✅ [Research Manager] 结构化输出解析成功: {decision.rating}")
        except Exception as e:
            logger.warning(f"⚠️ [Research Manager] 结构化输出失败，回退到文本模式: {e}")
            response = llm.invoke(prompt)
            decision = parse_structured_output(response.content if hasattr(response, 'content') else str(response), PortfolioDecision)

        elapsed_time = time.time() - start_time

        response_content = render_pm_decision(decision)
        response_length = len(response_content)
        estimated_output_tokens = int(response_length / 1.8)

        logger.info(f"⏱️ [Research Manager] LLM调用耗时: {elapsed_time:.2f}秒")
        logger.info(f"📊 [Research Manager] 响应统计: {response_length} 字符, 估算~{estimated_output_tokens} tokens")

        new_investment_debate_state = {
            "judge_decision": response_content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response_content,
            "count": investment_debate_state["count"],
            "rating": decision.rating.value,
            "price_target": decision.price_target,
            "data_quality": {
                "market": market_quality.grade.value,
                "fundamentals": fundamentals_quality.grade.value,
            },
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response_content,
        }

    return research_manager_node