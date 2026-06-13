from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入统一新闻工具
from tradingagents.tools.unified_news_tool import create_unified_news_tool
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler
from tradingagents.agents.utils.instrument_utils import build_instrument_context

logger = get_logger("analysts.policy")


def create_policy_analyst(llm, toolkit):
    @log_analyst_module("policy")
    def policy_analyst_node(state):
        start_time = datetime.now()

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("news_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.info(f"[政策分析师] 开始分析 {ticker} 的政策相关消息，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[政策分析师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[政策分析师] 股票类型: {market_info['market_name']}")
        
        # 获取公司名称
        def _get_company_name(ticker: str, market_info: dict) -> str:
            """根据股票代码获取公司名称"""
            try:
                if market_info['is_china']:
                    # 中国A股：使用统一接口获取股票信息
                    from tradingagents.dataflows.interface import get_china_stock_info_unified
                    stock_info = get_china_stock_info_unified(ticker)
                    
                    # 解析股票名称
                    if "股票名称:" in stock_info:
                        company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                        logger.debug(f"📊 [DEBUG] 从统一接口获取中国股票名称: {ticker} -> {company_name}")
                        return company_name
                    else:
                        logger.warning(f"⚠️ [DEBUG] 无法从统一接口解析股票名称: {ticker}")
                        return f"股票代码{ticker}"
                        
                elif market_info['is_hk']:
                    # 港股：使用改进的港股工具
                    try:
                        from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                        company_name = get_hk_company_name_improved(ticker)
                        logger.debug(f"📊 [DEBUG] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                        return company_name
                    except Exception as e:
                        logger.debug(f"📊 [DEBUG] 改进港股工具获取名称失败: {e}")
                        # 降级方案：生成友好的默认名称
                        clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                        return f"港股{clean_ticker}"
                        
                elif market_info['is_us']:
                    # 美股：使用简单映射或返回代码
                    us_stock_names = {
                        'AAPL': '苹果公司',
                        'TSLA': '特斯拉',
                        'NVDA': '英伟达',
                        'MSFT': '微软',
                        'GOOGL': '谷歌',
                        'AMZN': '亚马逊',
                        'META': 'Meta',
                        'NFLX': '奈飞'
                    }
                    
                    company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
                    logger.debug(f"📊 [DEBUG] 美股名称映射: {ticker} -> {company_name}")
                    return company_name
                    
                else:
                    return f"股票{ticker}"
                    
            except Exception as e:
                logger.error(f"❌ [DEBUG] 获取公司名称失败: {e}")
                return f"股票{ticker}"
        
        company_name = _get_company_name(ticker, market_info)
        instrument_context = build_instrument_context(ticker)
        logger.info(f"[政策分析师] 公司名称: {company_name}")
        
        # 🔧 使用统一新闻工具，筛选政策相关新闻
        logger.info(f"[政策分析师] 使用统一新闻工具获取新闻数据，自动筛选政策相关内容")
        # 创建统一新闻工具
        unified_news_tool = create_unified_news_tool(toolkit)
        unified_news_tool.name = "get_stock_news_unified"
        
        tools = [unified_news_tool]
        logger.info(f"[政策分析师] 已加载统一新闻工具: get_stock_news_unified")

        # 政策关键词列表，用于筛选政策新闻
        policy_keywords = [
            "证监会", "银保监会", "国务院", "央行", "财政部", "发改委", "商务部", 
            "工信部", "科技部", "证监会", "保监会", "交易所", "证监会主席",
            "监管", "政策", "规定", "办法", "意见", "通知", "公告", "决定",
            "产业政策", "行业政策", "扶持政策", "补贴", "减税", "免税",
            "窗口指导", " IPO", "再融资", "并购重组", "退市", "注册制",
            "北向资金", "QFII", "RQFII", "陆股通", "港股通",
            "央行降准", "央行降息", "LPR", "逆回购", "MLF", "SLF",
            "财政部发布会", "国务院常务会议", "中央政治局会议",
            "金融稳定", "风险防控", "合规", "整改"
        ]
        
        policy_keywords_str = "、".join(policy_keywords)

        system_message = (
            f"""您是一位专业的A股政策分析师，负责分析政策相关新闻和事件对股票价格的潜在影响。

您的主要职责包括：
1. 获取和分析最新的政策相关新闻（优先15-30分钟内的新闻）
2. 评估政策对A股市场的短期和中长期影响
3. 识别政策对个股的利好/利空影响
4. 分析政策时效性和影响程度
5. 判断政策的市场反应和资金流向

🎯 重点关注的政策类型：
- 监管政策：证监会、银保监会发布的法规、规定、办法
- 产业政策：发改委、工信部、商务部等发布的行业扶持政策
- 窗口指导：交易所、监管部门对市场的指导性意见
- 货币财政政策：央行、财政部的货币政策和财政政策
- 顶层政策：国务院、中央政治局的重要决策

📊 A股政策市特性分析要求：
- 分析政策对板块轮动的影响（哪些板块受益/受损）
- 评估政策对市场情绪和资金面的影响
- 判断政策的时效性（短期刺激还是长期影响）
- 分析政策力度（试探性还是实质性）
- 评估政策的执行力度和持续性

🔍 政策关键词识别（优先分析包含以下关键词的新闻）：
{policy_keywords_str}

📈 利好/利空评估标准：
- 直接受益政策且力度大：强烈利好（★★★★★）
- 受益政策但力度有限：一般利好（★★★☆☆）
- 政策影响中性：保持观望
- 受政策限制或监管：一般利空（★★★☆☆）
- 直接受限且力度大：强烈利空（★★★★★）

⏰ 时效性判断：
- 政策发布后1-2小时内：最新政策，需重点关注
- 政策发布后半天内：近期政策，需关注市场反应
- 政策发布超过24小时：需分析是否已被市场消化
- 政策预期/传闻：需谨慎判断真伪

请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。"""
        )

        # 🔧 工具名称列表（在构建 prompt 前必须先定义，避免 NameError）
        tool_names_str = ", ".join([tool.name for tool in tools])

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""您是一位专业的A股政策分析师。

🚨 CRITICAL REQUIREMENT - 绝对强制要求：

❌ 禁止行为：
- 绝对禁止在没有调用工具的情况下直接回答
- 绝对禁止基于推测或假设生成任何分析内容
- 绝对禁止跳过工具调用步骤
- 绝对禁止说'我无法获取实时数据'等借口

✅ 强制执行步骤：
1. 您的第一个动作必须是调用 get_stock_news_unified 工具
2. 该工具会自动识别股票类型（A股、港股、美股）并获取相应新闻
3. 只有在成功获取新闻数据后，才能开始分析
4. 您的回答必须基于工具返回的真实数据
5. 在分析中优先识别政策相关新闻（包含政策关键词的新闻）

🔧 工具调用格式示例：
调用: get_stock_news_unified(stock_code='{ticker}', max_news=10)

⚠️ 如果您不调用工具，您的回答将被视为无效并被拒绝。
⚠️ 您必须先调用工具获取数据，然后基于数据进行分析。
⚠️ 没有例外，没有借口，必须调用工具。

您可以访问以下工具：{tool_names_str}。
标的约束：{instrument_context}
{system_message}
供您参考，当前日期是{current_date}。我们正在查看公司{ticker}。
请按照上述要求执行，用中文撰写所有分析内容。""",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        
        # 获取模型信息用于统一新闻工具的特殊处理
        model_info = ""
        try:
            if hasattr(llm, 'model_name'):
                model_info = f"{llm.__class__.__name__}:{llm.model_name}"
            else:
                model_info = llm.__class__.__name__
        except:
            model_info = "Unknown"
        
        logger.info(f"[政策分析师] 准备调用LLM进行政策新闻分析，模型: {model_info}")
        
        # 🚨 DashScope/DeepSeek/Zhipu预处理：强制获取新闻数据
        pre_fetched_news = None
        if ('DashScope' in llm.__class__.__name__ 
            or 'DeepSeek' in llm.__class__.__name__
            or 'Zhipu' in llm.__class__.__name__
            ):
            logger.warning(f"[政策分析师] 🚨 检测到{llm.__class__.__name__}模型，启动预处理强制新闻获取...")
            try:
                # 强制预先获取新闻数据
                logger.info(f"[政策分析师] 🔧 预处理：强制调用统一新闻工具...")
                logger.info(f"[政策分析师] 📊 调用参数: stock_code={ticker}, max_news=10, model_info={model_info}")

                pre_fetched_news = unified_news_tool(stock_code=ticker, max_news=10, model_info=model_info)

                logger.info(f"[政策分析师] 📋 预处理返回结果长度: {len(pre_fetched_news) if pre_fetched_news else 0} 字符")
                logger.info(f"[政策分析师] 📄 预处理返回结果预览 (前500字符): {pre_fetched_news[:500] if pre_fetched_news else 'None'}")

                if pre_fetched_news and len(pre_fetched_news.strip()) > 100:
                    logger.info(f"[政策分析师] ✅ 预处理成功获取新闻: {len(pre_fetched_news)} 字符")

                    # 直接基于预获取的新闻生成分析，跳过工具调用
                    # 🔧 重要：构建不包含工具调用指导的系统提示词
                    analysis_system_prompt = f"""您是一位专业的A股政策分析师。

您的职责是基于提供的新闻数据，对股票进行深入的政策影响分析。

重点分析要点：
1. 筛选政策相关新闻（关注监管政策、产业政策、窗口指导等）
2. 评估政策对个股的利好/利空影响程度
3. 分析政策的时效性和影响范围
4. 判断政策对板块轮动的影响
5. 评估政策对市场情绪和资金面的影响

重要说明：新闻数据已经为您提供，您无需调用任何工具，直接基于提供的数据进行分析。"""

                    enhanced_prompt = f"""请基于以下已获取的新闻数据，对股票 {ticker}（{company_name}）进行详细的政策分析：

=== 最新新闻数据 ===
{pre_fetched_news}

=== 分析要求 ===
请重点分析上述新闻中的政策相关内容，包括：
1. 识别政策相关新闻及其政策类型
2. 评估政策对该股票的利好/利空影响
3. 分析政策的时效性和影响程度
4. 判断政策对市场情绪的影响
5. 提供基于政策分析的投资建议

请撰写详细的中文分析报告。"""

                    logger.info(f"[政策分析师] 🔄 使用预获取新闻数据直接生成分析...")
                    logger.info(f"[政策分析师] 📝 系统提示词长度: {len(analysis_system_prompt)} 字符")
                    logger.info(f"[政策分析师] 📝 用户提示词长度: {len(enhanced_prompt)} 字符")

                    llm_start_time = datetime.now()
                    # 🔧 重要：传递系统消息和用户消息，不包含工具调用
                    result = llm.invoke([
                        {"role": "system", "content": analysis_system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ])

                    llm_end_time = datetime.now()
                    llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
                    logger.info(f"[政策分析师] LLM调用完成（预处理模式），耗时: {llm_time_taken:.2f}秒")

                    # 直接返回结果，跳转到最终处理
                    if hasattr(result, 'content') and result.content:
                        report = result.content
                        logger.info(f"[政策分析师] ✅ 预处理模式成功，报告长度: {len(report)} 字符")
                        logger.info(f"[政策分析师] 📄 报告预览 (前300字符): {report[:300]}")

                        # 跳转到最终处理
                        from langchain_core.messages import AIMessage
                        clean_message = AIMessage(content=report)

                        end_time = datetime.now()
                        time_taken = (end_time - start_time).total_seconds()
                        logger.info(f"[政策分析师] 政策分析完成（预处理模式），总耗时: {time_taken:.2f}秒")
                        # 🔧 更新工具调用计数器
                        return {
                            "messages": [clean_message],
                            "policy_report": report,
                            "policy_tool_call_count": tool_call_count + 1
                        }
                    else:
                        logger.warning(f"[政策分析师] ⚠️ LLM返回结果为空，回退到标准模式")

                else:
                    logger.warning(f"[政策分析师] ⚠️ 预处理获取新闻失败或内容过短（{len(pre_fetched_news) if pre_fetched_news else 0}字符），回退到标准模式")
                    if pre_fetched_news:
                        logger.warning(f"[政策分析师] 📄 失败的新闻内容: {pre_fetched_news}")

            except Exception as e:
                logger.error(f"[政策分析师] ❌ 预处理失败: {e}，回退到标准模式")
                import traceback
                logger.error(f"[政策分析师] 📋 异常堆栈: {traceback.format_exc()}")
        
        # 使用统一的Google工具调用处理器
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[政策分析师] 开始LLM调用，分析 {ticker} 的政策新闻")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[政策分析师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [政策分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="政策分析",
                specific_requirements=f"重点关注政策相关新闻，优先识别包含以下关键词的内容：{policy_keywords_str}。评估政策对股价的利好/利空影响，分析政策的时效性和影响程度。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="政策分析师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[政策分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")

            # 检查工具调用情况
            current_tool_calls = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[政策分析师] LLM调用了 {current_tool_calls} 个工具")
            logger.debug(f"📊 [DEBUG] 累计工具调用次数: {tool_call_count}/{max_tool_calls}")

            if current_tool_calls == 0:
                logger.warning(f"[政策分析师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                logger.warning(f"[政策分析师] 📄 LLM原始响应内容 (前500字符): {result.content[:500] if hasattr(result, 'content') else 'No content'}")

                try:
                    # 强制获取新闻数据
                    logger.info(f"[政策分析师] 🔧 强制调用统一新闻工具获取新闻数据...")
                    logger.info(f"[政策分析师] 📊 调用参数: stock_code={ticker}, max_news=10")

                    forced_news = unified_news_tool(stock_code=ticker, max_news=10, model_info=model_info)

                    logger.info(f"[政策分析师] 📋 强制获取返回结果长度: {len(forced_news) if forced_news else 0} 字符")
                    logger.info(f"[政策分析师] 📄 强制获取返回结果预览 (前500字符): {forced_news[:500] if forced_news else 'None'}")

                    if forced_news and len(forced_news.strip()) > 100:
                        logger.info(f"[政策分析师] ✅ 强制获取新闻成功: {len(forced_news)} 字符")

                        # 基于真实新闻数据重新生成分析
                        forced_prompt = f"""
您是一位专业的A股政策分析师。请基于以下最新获取的新闻数据，对股票 {ticker}（{company_name}）进行详细政策分析：

=== 最新新闻数据 ===
{forced_news}

=== 分析要求 ===
重点分析上述新闻中的政策相关内容：
1. 识别政策相关新闻及其政策类型（监管政策、产业政策、窗口指导等）
2. 评估政策对该股票的利好/利空影响程度
3. 分析政策的时效性和影响程度
4. 判断政策对市场情绪和资金面的影响
5. 分析政策对板块轮动的影响
6. 提供基于政策分析的投资建议

{system_message}

请基于上述真实新闻数据撰写详细的中文分析报告。
"""

                        logger.info(f"[政策分析师] 🔄 基于强制获取的新闻数据重新生成完整分析...")
                        logger.info(f"[政策分析师] 📝 强制提示词长度: {len(forced_prompt)} 字符")

                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])

                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[政策分析师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                            logger.info(f"[政策分析师] 📄 报告预览 (前300字符): {report[:300]}")
                        else:
                            logger.warning(f"[政策分析师] ⚠️ 强制补救LLM返回为空，使用原始结果")
                            report = result.content if hasattr(result, 'content') else ""
                    else:
                        logger.warning(f"[政策分析师] ⚠️ 统一新闻工具获取失败或内容过短（{len(forced_news) if forced_news else 0}字符），使用原始结果")
                        if forced_news:
                            logger.warning(f"[政策分析师] 📄 失败的新闻内容: {forced_news}")
                        report = result.content if hasattr(result, 'content') else ""

                except Exception as e:
                    logger.error(f"[政策分析师] ❌ 强制补救过程失败: {e}")
                    import traceback
                    logger.error(f"[政策分析师] 📋 异常堆栈: {traceback.format_exc()}")
                    report = result.content if hasattr(result, 'content') else ""
            else:
                # 有工具调用，直接使用结果
                report = result.content
        
        total_time_taken = (datetime.now() - start_time).total_seconds()
        logger.info(f"[政策分析师] 政策分析完成，总耗时: {total_time_taken:.2f}秒")

        # 🔧 修复死循环问题：返回清洁的AIMessage，不包含tool_calls
        # 这确保工作流图能正确判断分析已完成，避免重复调用
        from langchain_core.messages import AIMessage
        clean_message = AIMessage(content=report)

        logger.info(f"[政策分析师] ✅ 返回清洁消息，报告长度: {len(report)} 字符")

        # 🔧 更新工具调用计数器
        return {
            "messages": [clean_message],
            "policy_report": report,
            "policy_tool_call_count": tool_call_count + 1
        }

    return policy_analyst_node
