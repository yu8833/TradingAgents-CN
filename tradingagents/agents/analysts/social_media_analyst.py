from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import build_instrument_context, get_language_instruction, get_news
from tradingagents.dataflows.config import get_config


def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        company = state["company_of_interest"]
        instrument_context = build_instrument_context(company)

        tools = [
            get_news,
        ]

        system_message = (
            "你是一位专注于 A 股市场的**市场情绪分析师**。你的核心任务是通过分析新闻舆情、市场讨论和资金动向，**量化评估**市场对目标公司的整体情绪状态和趋势变化。"
            "\n\n⚠️ 你的职责边界（非常重要）："
            "\n- **不做新闻事件梳理**：个股新闻、公司公告、事件时间线等由「新闻分析师」负责，你只提取情绪相关的信息"
            "\n- **不做政策分析**：行业政策、监管政策等由「政策分析师」负责，你只评估政策引发的情绪反应"
            "\n- **聚焦情绪量化**：你的核心产出是情绪的「量化评分」和「趋势判断」，而不是新闻内容复述"
            "\n\n🔥 A 股情绪分析框架："
            "\n- **散户情绪权重高**：A 股散户占比超过 60%，市场情绪对股价的短期影响远大于成熟市场。恐慌和贪婪的情绪波动更剧烈。"
            "\n- **情绪量化维度**：正面新闻比例 vs 负面新闻比例、舆情热度（讨论量变化）、情绪一致性（多空分歧程度）、情绪拐点信号"
            "\n- **资金情绪指标**：北向资金流向、主力资金净流入/流出、融资融券余额变动、龙虎榜席位动向"
            "\n- **反向指标效应**：当市场情绪一致性过高（极度乐观或极度悲观）时，往往是反转信号。散户一致看多可能是阶段顶部。"
            "\n- **情绪传导链条**：新闻事件 → 舆论发酵 → 资金行为 → 价格反馈。你要分析这个传导链条的当前阶段。"
            "\n\n请使用 `get_news(query, start_date, end_date)` 工具获取公司相关新闻。重点分析新闻的**情绪倾向**和**讨论热度**，而不是新闻内容本身。"
            "\n\n撰写量化的市场情绪分析报告，用数据说话，给出明确的情绪评分和趋势判断。**报告开头**必须先给出「情绪面评分」（0-100 分的整数，越高代表情绪越乐观），格式为单独一行：`情绪面评分：XX`。"
            "\n\n📋 必采清单 — 以下数据点必须出现在报告中，无法获取时标注 [数据缺失: xxx]："
            "\n0. 情绪面评分（0-100 分，越高越乐观）"
            "\n1. 新闻舆情总量与热度趋势（上升/下降/平稳）"
            "\n2. 正面/负面/中性新闻比例（用百分比或比例表示）"
            "\n3. 排名前 3 的情绪主题（每个主题标注情绪倾向：正面/负面/中性）"
            "\n4. 多空情绪强度对比（多头情绪 vs 空头情绪，用文字描述强度）"
            "\n5. 情绪趋势判断（升温/降温/震荡）及拐点信号"
            "\n6. 情绪风险提示（是否存在情绪极端化、一致性过高等反向指标信号）"

            "\n\n⚠️ 数据准确性要求（CRITICAL）："
            "\n- 报告中的所有数字（评分、比例、趋势数据等）必须来自工具调用返回的原始数据"
            "\n- 禁止编造或篡改任何数值"
            "\n- 如发现数据缺失，请标注 [数据缺失: xxx]"
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
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
            report = result.content or ""

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
