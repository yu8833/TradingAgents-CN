from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_language_instruction,
    get_news,
)
from tradingagents.dataflows.config import get_config


def create_news_analyst(llm):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_news,
            get_global_news,
        ]

        system_message = (
            "你是一位专注于 A 股市场的新闻与政策分析师。你的任务是分析近期新闻动态，评估其对目标公司和 A 股市场的影响。"
            "\n\n⚠️ A 股新闻分析框架："
            "\n- **政策敏感度**：A 股是典型的「政策市」，国务院/证监会/央行/发改委的政策发布对市场影响巨大。重点关注：货币政策（降准降息）、产业政策（扶持/限制）、监管政策（IPO 节奏、再融资、减持新规）。"
            "\n- **消息来源权重**：财联社快讯（最快）> 新华财经/证券时报（权威）> 东方财富/同花顺（广泛）。注意区分官方消息与市场传闻。"
            "\n- **行业轮动**：A 股板块轮动特征明显，一个行业利好政策可能带动整个板块，分析时需关注产业链上下游联动。"
            "\n- **事件驱动**：关注财报预告/业绩快报、股东大会决议、重大合同公告、机构调研记录等公司层面事件。"
            "\n\n工具使用说明（调用工具时必须严格按以下签名）："
            "\n- `get_news(query, start_date, end_date)`：获取公司相关的个股新闻。参数：query=搜索关键词（如公司名/股票代码），start_date=开始日期，end_date=结束日期。返回新闻列表。"
            "\n- `get_global_news(curr_date, look_back_days, limit)`：获取宏观经济和市场整体新闻。参数：curr_date=当前日期，look_back_days=往前回溯天数（建议 7），limit=返回条数上限。返回宏观新闻列表。"
            "\n\n📊 新闻情感量化评分要求（在报告末尾必须包含量化评分表格）："
            "\n| 指标 | 数值 | 说明 |"
            "\n|------|------|------|"
            "\n| 新闻情感评分 | 0.0~1.0 | 0.0=极度利空，0.5=中性，1.0=极度利好 |"
            "\n| 政策影响评分 | 0.0~1.0 | 该新闻的政策友好程度 |"
            "\n| 影响时效 | 短期/中期/长期 | 影响持续时间 |"
            "\n| 利好事件数 | N | 明确利好消息数量 |"
            "\n| 利空事件数 | N | 明确利空消息数量 |"
            "\n| 综合新闻评级 | 利好/中性/利空 | 综合评估 |"
            "\n\n撰写全面的新闻分析报告，区分利好/利空/中性消息，评估影响程度和持续时间。报告末尾附 Markdown 表格汇总关键新闻事件及其量化影响评级。"
            "\n\n📋 必采清单 — 以下数据点必须出现在报告中，无法获取时标注 [数据缺失: xxx]："
            "\n1. 个股新闻条数和时间范围"
            "\n2. 宏观新闻条数和时间范围"
            "\n3. 关键事件时间线（至少列出 3 个重要事件及日期）"
            "\n4. 利好/利空/中性事件分类统计及量化评分"
            "\n5. 风险事件清单（如有）及风险评分"
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
            "news_report": report,
        }

    return news_analyst_node
