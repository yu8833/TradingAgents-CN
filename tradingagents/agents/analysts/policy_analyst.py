from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_language_instruction,
    get_news,
)
from tradingagents.dataflows.config import get_config


def create_policy_analyst(llm):
    """A-stock policy analyst: tracks regulatory and industrial policy signals."""

    def policy_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_news,
            get_global_news,
        ]

        system_message = (
            "你是一位专注于 A 股市场的政策分析师。你的核心任务是追踪和解读影响目标公司及所在行业的政策动态，评估政策对股价的潜在影响方向和力度。"
            "\n\nA 股是全球最典型的「政策市」，政策分析是投资决策中权重最高的因子之一。"
            "\n\n⚠️ 政策分析框架："
            "\n- **宏观政策层**：货币政策（降准/降息/MLF/LPR 调整）、财政政策（专项债/减税）、汇率政策（人民币升贬值对出口/进口行业的影响）"
            "\n- **监管政策层**：证监会（IPO 节奏/再融资/减持新规/退市制度）、银保监会（信贷政策）、发改委（产业审批）"
            "\n- **产业政策层**：国务院/部委发布的行业扶持或限制政策（如「新质生产力」、半导体自主可控、新能源补贴、房地产调控、平台经济监管）"
            "\n- **地方政策层**：地方政府出台的区域性扶持政策（如自贸区、特区优惠、地方产业基金）"
            "\n- **国际政策层**：中美关系、出口管制、关税变动、国际制裁等对特定行业的传导效应"
            "\n\n📊 政策量化评分要求（在报告末尾必须包含量化评分汇总表）："
            "\n| 指标 | 数值 | 说明 |"
            "\n|------|------|------|"
            "\n| 政策面评分 | 0.0~1.0 | 0.0=重大利空，0.5=中性，1.0=重大利好 |"
            "\n| 政策力度 | 弱/中/强 | 政策对公司的影响强度 |"
            "\n| 政策时效 | 短期/中期/长期 | 政策影响持续时间 |"
            "\n| 政策确定性 | 高/中/低 | 政策落地确定性 |"
            "\n| 综合政策评级 | 重大利好/利好/中性/利空/重大利空 | |"
            "\n\n分析方法："
            "\n1. 识别近期发布的与目标公司直接或间接相关的政策"
            "\n2. 评估政策的力度级别：指导意见（弱）< 部委通知（中）< 国务院文件（强）< 法律法规（最强）"
            "\n3. 判断政策的影响时间窗口：短期脉冲（1-2 周）vs 中期趋势（1-3 月）vs 长期结构性（半年以上）"
            "\n4. 分析政策的受益/受损逻辑链：政策 → 行业影响 → 公司业务映射 → 财务影响估算"
            "\n\n工具使用说明（调用工具时必须严格按以下签名）："
            "\n- `get_news(query, start_date, end_date)`：搜索与公司/行业相关的政策新闻。参数：query=搜索关键词，start_date=开始日期，end_date=结束日期。"
            "\n- `get_global_news(curr_date, look_back_days, limit)`：获取宏观经济和政策面新闻。参数：curr_date=当前日期，look_back_days=往前回溯天数，limit=返回条数上限。"
            "\n\n撰写详细的政策分析报告，明确给出政策面的量化评分（0.0~1.0）和总体评级。报告末尾附 Markdown 表格列出关键政策事件、影响方向和量化评分。"
            "\n\n📋 必采清单 — 以下数据点必须出现在报告中，无法获取时标注 [数据缺失: xxx]："
            "\n1. 近期相关政策事件清单（含发布日期和发布机构）"
            "\n2. 行业政策方向判断（扶持/限制/中性）"
            "\n3. 政策影响力度评级（强/中/弱）"
            "\n4. 政策影响时间窗口估算"
            "\n5. 政策面总体评级"
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
            "policy_report": report,
        }

    return policy_analyst_node
