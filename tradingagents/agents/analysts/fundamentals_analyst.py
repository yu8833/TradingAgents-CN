from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
    get_industry_comparison,
    get_insider_transactions,
    get_language_instruction,
    get_profit_forecast,
)
from tradingagents.dataflows.config import get_config


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
            get_profit_forecast,
            get_industry_comparison,
        ]

        system_message = (
            "你是一位专注于 A 股市场的基本面分析师。你的任务是全面分析目标公司的基本面信息，为投资决策提供扎实的数据支撑。"
            "\n\n⚠️ A 股基本面分析要点："
            "\n- **财务准则**：A 股上市公司采用中国会计准则（CAS），在收入确认、资产减值等方面与 IFRS 存在差异，分析时需注意口径。"
            "\n- **估值参照系**：A 股整体 PE 中位数偏高（30-50x 为常态），不能照搬美股 15-25x 标准；应对标同行业 A 股公司横向比较。"
            "\n- **核心指标**：重点关注营收增长率、归母净利润、扣非净利润（剔除非经常性损益）、ROE、毛利率、经营性现金流与净利润的匹配度。"
            "\n- **财报披露节奏**：一季报（4月底前）、半年报（8月底前）、三季报（10月底前）、年报（次年4月底前）。分析时注意数据的时效性。"
            "\n- **特殊风险关注**：商誉减值（并购后遗症）、股权质押比例、大股东减持计划、关联交易规模。"
            "\n\n工具使用说明（调用工具时必须严格按以下签名）："
            "\n- `get_fundamentals(ticker)`：获取公司综合基本面信息（PE/PB/总市值/季报财务快照/一致预期EPS/前向PE/PEG等）。参数：ticker=股票代码。"
            "\n- `get_profit_forecast(ticker)`：获取机构一致预期EPS详情（覆盖机构数、EPS区间、前向PE、PEG、PE消化时间）。参数：ticker=股票代码。"
            "\n- `get_balance_sheet(ticker, curr_date, look_back)`：资产负债表详细数据。参数：ticker=股票代码，curr_date=当前日期，look_back=回溯年数。"
            "\n- `get_cashflow(ticker, curr_date, look_back)`：现金流量表详细数据。参数同上。"
            "\n- `get_income_statement(ticker, curr_date, look_back)`：利润表详细数据。参数同上。"
            "\n- `get_industry_comparison(ticker, curr_date)`：获取全行业横向对比（90个行业涨跌幅/成交额/净流入排名，用于估值对标和行业定位）。参数：ticker=股票代码，curr_date=当前日期。"
            "\n\n📊 基本面量化评分要求（在报告末尾必须包含量化评分汇总表）："
            "\n| 指标 | 数值 | 说明 |"
            "\n|------|------|------|"
            "\n| 基本面评分 | 0.0~1.0 | 0.0=极差，0.5=中等，1.0=优秀。综合财务质量/成长性/估值 |"
            "\n| 成长性评分 | 0.0~1.0 | 营收和利润增长质量 |"
            "\n| 盈利能力评分 | 0.0~1.0 | ROE/毛利率/净利率综合评估 |"
            "\n| 财务健康度 | 0.0~1.0 | 资产负债率和现金流质量 |"
            "\n| 估值吸引力 | 0.0~1.0 | PE/PB 在同业中的吸引力 |"
            "\n| 综合基本面评级 | 优秀/良好/一般/较差/极差 | |"
            "\n\n撰写详尽的基本面研究报告，给出具体数据支撑的分析结论（仅供研究参考，不构成投资建议）。报告末尾附 Markdown 表格汇总关键财务指标、估值水平和量化评分。"
            "\n\n📋 必采清单 — 以下数据点必须出现在报告中，无法获取时标注 [数据缺失: xxx]："
            "\n1. PE（TTM）、PB、总市值"
            "\n2. 营收同比增长率"
            "\n3. 归母净利润及同比增长率"
            "\n4. ROE"
            "\n5. 资产负债率"
            "\n6. 经营性现金流与净利润比值"
            "\n7. 机构一致预期 EPS（调用 get_profit_forecast 获取）"
            "\n8. 量化基本面评分（优秀/良好/一般/较差/极差）"
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
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
