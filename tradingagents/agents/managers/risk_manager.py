import time
import json

from tradingagents.utils.logging_init import get_logger
from tradingagents.agents.utils.instrument_utils import build_instrument_context
from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.structured import get_structured_llm, parse_structured_output

logger = get_logger("default")


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
        else:
            logger.warning(f"⚠️ [DEBUG] memory为None，跳过历史记忆检索")
            past_memories = []

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""作为风险管理委员会主席和辩论主持人，您的目标是评估三位风险分析师——激进、中性和安全/保守——之间的辩论，并综合市场分析师的技术分析报告，确定交易员的最佳行动方案。您的决策必须产生客观、平衡的投资建议。

**重要原则**：
- **持有是中性建议**，不需要比买入/卖出更强的理由
- **警惕辩论中的极端观点和主观臆测**（如"历史教训表明..."、"类似标的上..."等无数据支撑的说法）
- **综合权衡**，而非简单地选择辩论中最极端的一方
- **市场分析师的技术分析应作为重要参考**

**A股市场特别考虑**：
- T+1交易制度的影响
- 涨跌停板限制
- 北向资金流动作为聪明钱指标
- 估值区间方法
- 限售股解禁时间
- 行业轮动意识

决策指导原则：
1. **总结关键论点**：提取每位分析师的最强观点，重点关注有数据支撑的证据。
2. **提供理由**：用辩论中的直接引用和反驳论点支持您的建议。
3. **完善交易员计划**：从交易员的原始计划**{trader_plan}**开始，根据分析师的见解进行调整，但要保持合理的平衡，避免过于极端。
4. **从过去的错误中学习**：使用**{past_memory_str}**中的经验教训来解决先前的误判，但不要被历史偏见影响当前客观分析。

标的约束：
{instrument_context}

---

**分析师辩论历史：**
{history}

---

专注于可操作的见解和持续改进。建立在过去经验教训的基础上，批判性地评估所有观点，确保每个决策都能带来更好的结果。请用中文撰写所有分析内容和建议。"""

        prompt_length = len(prompt)
        estimated_tokens = int(prompt_length / 1.8)

        logger.info(f"📊 [Risk Manager] Prompt 统计:")
        logger.info(f"   - 辩论历史长度: {len(history)} 字符")
        logger.info(f"   - 交易员计划长度: {len(trader_plan)} 字符")
        logger.info(f"   - 历史记忆长度: {len(past_memory_str)} 字符")
        logger.info(f"   - 总 Prompt 长度: {prompt_length} 字符")
        logger.info(f"   - 估算输入 Token: ~{estimated_tokens} tokens")

        max_retries = 3
        retry_count = 0
        response_content = ""
        decision = None

        while retry_count < max_retries:
            try:
                logger.info(f"🔄 [Risk Manager] 调用LLM生成交易决策 (尝试 {retry_count + 1}/{max_retries})")

                start_time = time.time()

                structured_llm = get_structured_llm(llm, PortfolioDecision)
                
                try:
                    response = structured_llm.invoke(prompt)
                    decision = parse_structured_output(response, PortfolioDecision)
                    response_content = render_pm_decision(decision)
                    logger.info(f"✅ [Risk Manager] 结构化输出解析成功: {decision.rating}")
                except Exception as e:
                    logger.warning(f"⚠️ [Risk Manager] 结构化输出失败，回退到文本模式: {e}")
                    response = llm.invoke(prompt)
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    decision = parse_structured_output(response_text, PortfolioDecision)
                    response_content = render_pm_decision(decision)

                elapsed_time = time.time() - start_time

                response_length = len(response_content)
                estimated_output_tokens = int(response_length / 1.8)

                usage_info = ""
                if hasattr(response, 'response_metadata') and response.response_metadata:
                    metadata = response.response_metadata
                    if 'token_usage' in metadata:
                        token_usage = metadata['token_usage']
                        usage_info = f", 实际Token: 输入={token_usage.get('prompt_tokens', 'N/A')} 输出={token_usage.get('completion_tokens', 'N/A')} 总计={token_usage.get('total_tokens', 'N/A')}"

                logger.info(f"⏱️ [Risk Manager] LLM调用耗时: {elapsed_time:.2f}秒")
                logger.info(f"📊 [Risk Manager] 响应统计: {response_length} 字符, 估算~{estimated_output_tokens} tokens{usage_info}")

                if len(response_content) > 10:
                    logger.info(f"✅ [Risk Manager] LLM调用成功")
                    break
                else:
                    logger.warning(f"⚠️ [Risk Manager] LLM响应内容过短: {len(response_content)} 字符")
                    response_content = ""

            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(f"❌ [Risk Manager] LLM调用失败 (尝试 {retry_count + 1}): {str(e)}")
                logger.error(f"⏱️ [Risk Manager] 失败前耗时: {elapsed_time:.2f}秒")
                response_content = ""
            
            retry_count += 1
            if retry_count < max_retries and not response_content:
                logger.info(f"🔄 [Risk Manager] 等待2秒后重试...")
                time.sleep(2)
        
        if not response_content:
            logger.error(f"❌ [Risk Manager] 所有LLM调用尝试失败，使用默认决策")
            decision = PortfolioDecision(
                rating="Hold",
                executive_summary=f"由于技术原因无法生成详细分析，建议对{company_name}采取持有策略",
                investment_thesis="市场信息不足，避免盲目操作；保持现有仓位，等待更明确的市场信号；控制风险，避免在不确定性高的情况下做出激进决策",
            )
            response_content = render_pm_decision(decision)

        new_risk_debate_state = {
            "judge_decision": response_content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
            "rating": decision.rating.value if decision else "Hold",
            "price_target": decision.price_target if decision else None,
        }

        logger.info(f"📋 [Risk Manager] 最终决策生成完成，内容长度: {len(response_content)} 字符")
        
        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response_content,
        }

    return risk_manager_node