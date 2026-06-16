from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import build_instrument_context, get_language_instruction, get_news
from tradingagents.dataflows.config import get_config


def create_sentiment_analyst(llm):
    def sentiment_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_news,
        ]

        system_message = (
            "你是一位专注于 A 股市场的市场情绪分析师。你的任务是通过分析公司相关新闻、市场讨论和公众情绪，判断市场对目标公司的整体态度和情绪走向。"
            "\n\n⚠️ A 股情绪分析框架："
            "\n- **散户情绪权重高**：A 股散户占比超过 60%，市场情绪对股价的短期影响远大于成熟市场。恐慌和贪婪的情绪波动更剧烈。"
            "\n- **舆论阵地**：东方财富股吧、雪球、同花顺社区是 A 股投资者最活跃的讨论平台。分析新闻时注意推断这些平台可能的情绪反应。"
            "\n- **情绪指标**：关注以下情绪信号 - 连续涨停后的追涨情绪、业绩暴雷后的恐慌抛售、机构调研后的预期变化、热门概念炒作的跟风程度。"
            "\n- **反向指标**：当市场情绪一致性过高（极度乐观或极度悲观）时，往往是反转信号。散户一致看多可能是阶段顶部。"
            "\n- **时间维度**：区分短期情绪波动（1-3 天，由单一事件驱动）和中期情绪趋势（1-4 周，由基本面变化驱动）。"
            "\n\n请使用 `get_news(query, start_date, end_date)` 工具获取公司相关新闻和市场讨论。"
            "\n\n📊 量化情感评分要求（在报告末尾必须包含以下量化信息）："
            "\n1. **情感评分（0.0~1.0）**：0.0=极度悲观，0.25=悲观，0.5=中性，0.75=乐观，1.0=极度乐观。用数字精确量化，不只是文字描述。"
            "\n2. **情感强度（0.0~1.0）**：衡量情绪的激烈程度，0.0=极微弱，1.0=极度亢奋/恐慌。反映市场讨论的热度。"
            "\n3. **一致性评分（0.0~1.0）**：衡量市场情绪的一致程度，0.0=完全分歧，1.0=高度一致。一致性过高时注意反转风险。"
            "\n4. **舆情风险（高/中/低）**：评估当前舆情对股价的潜在风险级别。"
            "\n5. **正面/负面/中性新闻数量及占比**"
            "\n6. **排名前 3 的舆情主题及情绪方向**"
            "\n\n报告末尾必须包含量化评分汇总表格，格式如下："
            "\n| 指标 | 数值 | 说明 |"
            "\n|------|------|------|"
            "\n| 情感评分 | 0.75 | 整体偏乐观 |"
            "\n| 情感强度 | 0.60 | 市场讨论热度中等 |"
            "\n| 一致性 | 0.45 | 分歧较大 |"
            "\n| 舆情风险 | 中 | 无重大负面舆情 |"
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一位专业的 A 股分析助手，正在与其他分析伙伴协作完成股票分析。"
                    "使用提供的工具（如数据查询、新闻搜索）来回答问题。"
                    "如果当前工具不足以完成完整回答也没关系，其他同事会从你停止的地方继续推进。"
                    "在你能力范围内尽力完成分析即可。"
                    "如果你或其他同事已有**最终交易建议（买入/持有/卖出）**，请在回答开头标注「最终交易建议」。"
                    "你可以调用的工具有：{tool_names}。\n{system_message}"
                    "参考日期：{current_date}。{instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return sentiment_analyst_node