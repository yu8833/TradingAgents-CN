from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from datetime import datetime

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils
# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler
from tradingagents.agents.utils.instrument_utils import build_instrument_context

logger = get_logger("analysts.lockup")


def create_lockup_analyst(llm, toolkit):
    @log_analyst_module("lockup")
    def lockup_analyst_node(state):
        start_time = datetime.now()

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("lockup_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.info(f"[解禁监控师] 开始分析 {ticker} 的限售股解禁情况，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[解禁监控师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[解禁监控师] 股票类型: {market_info['market_name']}")
        
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
        logger.info(f"[解禁监控师] 公司名称: {company_name}")
        
        # 创建解禁数据获取工具
        def get_lockup_data_tool():
            """创建解禁数据获取工具"""
            def _get_lockup_data(stock_code: str, max_items: int = 50):
                """
                获取A股限售股解禁数据
                
                参数:
                    stock_code: 股票代码（如 '000001'）
                    max_items: 最大返回条数
                
                返回:
                    解禁数据详情，包括解禁日期、解禁规模、解禁比例等
                """
                logger.info(f"[解禁监控师] 🔧 获取解禁数据: stock_code={stock_code}, max_items={max_items}")
                
                try:
                    import akshare as ak
                    
                    # 获取解禁详情数据
                    logger.info(f"[解禁监控师] 📊 调用 akshare stock_restricted_release_detail_em 获取解禁数据...")
                    df = ak.stock_restricted_release_detail_em(symbol=stock_code)
                    
                    if df is None or df.empty:
                        logger.warning(f"[解禁监控师] ⚠️ 未获取到 {stock_code} 的解禁数据")
                        return f"暂无 {stock_code} 的解禁数据"
                    
                    # 数据预处理
                    logger.info(f"[解禁监控师] 📋 获取到 {len(df)} 条解禁记录")
                    
                    # 转换数据为可读格式
                    result_lines = []
                    result_lines.append(f"=== {company_name}({ticker}) 限售股解禁数据 ===")
                    result_lines.append(f"数据获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    result_lines.append(f"总记录数: {len(df)} 条")
                    result_lines.append("")
                    
                    # 打印列名帮助调试
                    logger.debug(f"[解禁监控师] 📊 数据列名: {list(df.columns)}")
                    
                    # 遍历数据行
                    for idx, row in df.head(max_items).iterrows():
                        try:
                            # 尝试提取关键字段（根据akshare实际返回格式调整）
                            date = row.get('解禁日期', row.get('日期', row.get('date', '未知')))
                            volume = row.get('解禁数量', row.get('解禁股数', row.get('volume', '未知')))
                            ratio = row.get('解禁比例', row.get('占总股本比例', row.get('ratio', '未知')))
                            holder = row.get('股东名称', row.get('股东', row.get('holder', '未知')))
                            type_ = row.get('股份类型', row.get('类型', row.get('type', '未知')))
                            
                            line = f"日期: {date} | 数量: {volume} | 比例: {ratio} | 股东: {holder} | 类型: {type_}"
                            result_lines.append(line)
                        except Exception as row_error:
                            logger.warning(f"[解禁监控师] ⚠️ 解析数据行失败: {row_error}")
                            continue
                    
                    result = "\n".join(result_lines)
                    logger.info(f"[解禁监控师] ✅ 成功获取解禁数据: {len(result)} 字符")
                    return result
                    
                except Exception as e:
                    logger.error(f"[解禁监控师] ❌ 获取解禁数据失败: {e}")
                    import traceback
                    logger.error(f"[解禁监控师] 📋 异常堆栈: {traceback.format_exc()}")
                    return f"获取解禁数据失败: {str(e)}"
            
            return _get_lockup_data
        
        # 创建解禁数据获取工具
        lockup_tool = get_lockup_data_tool()
        lockup_tool.name = "get_lockup_data"
        
        tools = [lockup_tool]
        logger.info(f"[解禁监控师] 已加载解禁数据工具: get_lockup_data")

        system_message = (
            """您是一位专业的解禁监控分析师，负责分析A股限售股解禁数据对股票价格的潜在影响。

您的主要职责包括：
1. 获取和分析最新的限售股解禁数据
2. 评估解禁对股价的潜在供给冲击
3. 识别大股东减持风险和股权质押风险
4. 分析解禁对股价的短期和中期影响
5. 提供基于解禁数据的投资建议

⚠️ 关键概念说明：
- 解禁是A股特有的重大供给冲击因素
- 限售股解禁意味着更多股份进入流通市场，增加卖盘压力
- 大股东减持通常被视为对公司未来发展信心不足的信号
- 股权质押比例过高可能面临爆仓风险

重点关注的分析要点：
- 近期解禁规模和解禁日期（越近的解禁影响越大）
- 解禁股占总股本的比例（比例越高，供给冲击越大）
- 大股东减持历史和计划（历史减持越多，未来减持压力越大）
- 股权质押比例和爆仓风险（质押比例>50%需高度警惕）
- 解禁对股价的短期（1-2周）和中期（1-3个月）影响

分析维度：
- 解禁规模：绝对数量和相对比例
- 股东背景：控股股东、创投股东、高管等不同类型股东的减持意愿
- 时间分布：集中解禁还是分散解禁
- 历史规律：历史解禁后的股价表现
- 市场环境：牛市中解禁压力可能被低估，熊市中压力会被放大

📊 解禁影响分析要求：
- 评估解禁对股价的负面压力程度
- 分析大股东减持的可能性和潜在规模
- 识别股权质押相关的爆仓风险
- 提供风险等级评估（高/中/低）
- 不允许回复'无法评估影响'或'需要更多信息'

请特别注意：
⚠️ 解禁是A股投资必须重点关注的风险因素
✅ 优先分析即将到来的大规模解禁
📊 提供量化的风险评估指标
💰 必须包含基于解禁数据的投资建议和风险提示
🎯 聚焦解禁数据本身的解读，结合市场环境综合分析"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位专业的解禁监控分析师。"
                    "\n🚨 CRITICAL REQUIREMENT - 绝对强制要求："
                    "\n"
                    "\n❌ 禁止行为："
                    "\n- 绝对禁止在没有调用工具的情况下直接回答"
                    "\n- 绝对禁止基于推测或假设生成任何分析内容"
                    "\n- 绝对禁止跳过工具调用步骤"
                    "\n- 绝对禁止说'我无法获取实时数据'等借口"
                    "\n"
                    "\n✅ 强制执行步骤："
                    "\n1. 您的第一个动作必须是调用 get_lockup_data 工具"
                    "\n2. 该工具会获取指定股票的最新解禁数据"
                    "\n3. 只有在成功获取解禁数据后，才能开始分析"
                    "\n4. 您的回答必须基于工具返回的真实数据"
                    "\n"
                    "\n🔧 工具调用格式示例："
                    "\n调用: get_lockup_data(stock_code='{ticker}', max_items=50)"
                    "\n"
                    "\n⚠️ 如果您不调用工具，您的回答将被视为无效并被拒绝。"
                    "\n⚠️ 您必须先调用工具获取数据，然后基于数据进行分析。"
                    "\n⚠️ 没有例外，没有借口，必须调用工具。"
                    "\n"
                    "\n您可以访问以下工具：{tool_names}。"
                    "\n标的约束：{instrument_context}"
                    "\n{system_message}"
                    "\n供您参考，当前日期是{current_date}。我们正在查看公司{ticker}。"
                    "\n请按照上述要求执行，用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(instrument_context=instrument_context)
        
        # 获取模型信息用于特殊处理
        model_info = ""
        try:
            if hasattr(llm, 'model_name'):
                model_info = f"{llm.__class__.__name__}:{llm.model_name}"
            else:
                model_info = llm.__class__.__name__
        except:
            model_info = "Unknown"
        
        logger.info(f"[解禁监控师] 准备调用LLM进行解禁分析，模型: {model_info}")
        
        # 🚨 DashScope/DeepSeek/Zhipu预处理：强制获取解禁数据
        pre_fetched_data = None
        if ('DashScope' in llm.__class__.__name__ 
            or 'DeepSeek' in llm.__class__.__name__
            or 'Zhipu' in llm.__class__.__name__
            ):
            logger.warning(f"[解禁监控师] 🚨 检测到{llm.__class__.__name__}模型，启动预处理强制解禁数据获取...")
            try:
                # 强制预先获取解禁数据
                logger.info(f"[解禁监控师] 🔧 预处理：强制调用解禁数据工具...")
                logger.info(f"[解禁监控师] 📊 调用参数: stock_code={ticker}, max_items=50")

                pre_fetched_data = lockup_tool(stock_code=ticker, max_items=50)

                logger.info(f"[解禁监控师] 📋 预处理返回结果长度: {len(pre_fetched_data) if pre_fetched_data else 0} 字符")
                logger.info(f"[解禁监控师] 📄 预处理返回结果预览 (前500字符): {pre_fetched_data[:500] if pre_fetched_data else 'None'}")

                if pre_fetched_data and len(pre_fetched_data.strip()) > 50:
                    logger.info(f"[解禁监控师] ✅ 预处理成功获取解禁数据: {len(pre_fetched_data)} 字符")

                    # 直接基于预获取的数据生成分析，跳过工具调用
                    analysis_system_prompt = f"""您是一位专业的解禁监控分析师。

您的职责是基于提供的解禁数据，对股票进行深入的解禁影响分析。

分析要点：
1. 总结最新的解禁数据和解禁规模
2. 分析解禁对股价的潜在供给冲击
3. 评估大股东减持风险和股权质押风险
4. 提供基于解禁数据的投资建议

重要说明：解禁数据已经为您提供，您无需调用任何工具，直接基于提供的数据进行分析。"""

                    enhanced_prompt = f"""请基于以下已获取的解禁数据，对股票 {ticker}（{company_name}）进行详细的解禁分析：

=== 限售股解禁数据 ===
{pre_fetched_data}

请撰写详细的中文分析报告，包括：
1. 解禁数据总结和解禁规模分析
2. 解禁对股价的潜在影响评估
3. 大股东减持风险分析
4. 股权质押风险评估
5. 投资建议和风险提示"""

                    logger.info(f"[解禁监控师] 🔄 使用预获取解禁数据直接生成分析...")
                    logger.info(f"[解禁监控师] 📝 系统提示词长度: {len(analysis_system_prompt)} 字符")
                    logger.info(f"[解禁监控师] 📝 用户提示词长度: {len(enhanced_prompt)} 字符")

                    llm_start_time = datetime.now()
                    # 传递系统消息和用户消息，不包含工具调用
                    result = llm.invoke([
                        {"role": "system", "content": analysis_system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ])

                    llm_end_time = datetime.now()
                    llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
                    logger.info(f"[解禁监控师] LLM调用完成（预处理模式），耗时: {llm_time_taken:.2f}秒")

                    if hasattr(result, 'content') and result.content:
                        report = result.content
                        logger.info(f"[解禁监控师] ✅ 预处理模式成功，报告长度: {len(report)} 字符")
                        logger.info(f"[解禁监控师] 📄 报告预览 (前300字符): {report[:300]}")

                        # 跳转到最终处理
                        from langchain_core.messages import AIMessage
                        clean_message = AIMessage(content=report)

                        end_time = datetime.now()
                        time_taken = (end_time - start_time).total_seconds()
                        logger.info(f"[解禁监控师] 解禁分析完成（预处理模式），总耗时: {time_taken:.2f}秒")
                        # 🔧 更新工具调用计数器
                        return {
                            "messages": [clean_message],
                            "lockup_report": report,
                            "lockup_tool_call_count": tool_call_count + 1
                        }
                    else:
                        logger.warning(f"[解禁监控师] ⚠️ LLM返回结果为空，回退到标准模式")

                else:
                    logger.warning(f"[解禁监控师] ⚠️ 预处理获取解禁数据失败或内容过短（{len(pre_fetched_data) if pre_fetched_data else 0}字符），回退到标准模式")
                    if pre_fetched_data:
                        logger.warning(f"[解禁监控师] 📄 失败的数据内容: {pre_fetched_data}")

            except Exception as e:
                logger.error(f"[解禁监控师] ❌ 预处理失败: {e}，回退到标准模式")
                import traceback
                logger.error(f"[解禁监控师] 📋 异常堆栈: {traceback.format_exc()}")
        
        # 使用统一的Google工具调用处理器
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[解禁监控师] 开始LLM调用，分析 {ticker} 的解禁数据")
        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[解禁监控师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [解禁监控师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="解禁分析",
                specific_requirements="重点关注解禁规模、大股东减持风险、股权质押风险、解禁对股价的供给冲击等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="解禁监控师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[解禁监控师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")

            # 检查工具调用情况
            current_tool_calls = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[解禁监控师] LLM调用了 {current_tool_calls} 个工具")
            logger.debug(f"📊 [DEBUG] 累计工具调用次数: {tool_call_count}/{max_tool_calls}")

            if current_tool_calls == 0:
                logger.warning(f"[解禁监控师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                logger.warning(f"[解禁监控师] 📄 LLM原始响应内容 (前500字符): {result.content[:500] if hasattr(result, 'content') else 'No content'}")

                try:
                    # 强制获取解禁数据
                    logger.info(f"[解禁监控师] 🔧 强制调用解禁数据工具获取数据...")
                    logger.info(f"[解禁监控师] 📊 调用参数: stock_code={ticker}, max_items=50")

                    forced_data = lockup_tool(stock_code=ticker, max_items=50)

                    logger.info(f"[解禁监控师] 📋 强制获取返回结果长度: {len(forced_data) if forced_data else 0} 字符")
                    logger.info(f"[解禁监控师] 📄 强制获取返回结果预览 (前500字符): {forced_data[:500] if forced_data else 'None'}")

                    if forced_data and len(forced_data.strip()) > 50:
                        logger.info(f"[解禁监控师] ✅ 强制获取解禁数据成功: {len(forced_data)} 字符")

                        # 基于真实数据重新生成分析
                        forced_prompt = f"""
您是一位专业的解禁监控分析师。请基于以下最新获取的解禁数据，对股票 {ticker}（{company_name}）进行详细的解禁分析：

=== 限售股解禁数据 ===
{forced_data}

=== 分析要求 ===
{system_message}

请基于上述真实解禁数据撰写详细的中文分析报告。
"""

                        logger.info(f"[解禁监控师] 🔄 基于强制获取的解禁数据重新生成完整分析...")
                        logger.info(f"[解禁监控师] 📝 强制提示词长度: {len(forced_prompt)} 字符")

                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])

                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[解禁监控师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                            logger.info(f"[解禁监控师] 📄 报告预览 (前300字符): {report[:300]}")
                        else:
                            logger.warning(f"[解禁监控师] ⚠️ 强制补救LLM返回为空，使用原始结果")
                            report = result.content if hasattr(result, 'content') else ""
                    else:
                        logger.warning(f"[解禁监控师] ⚠️ 解禁数据工具获取失败或内容过短（{len(forced_data) if forced_data else 0}字符），使用原始结果")
                        if forced_data:
                            logger.warning(f"[解禁监控师] 📄 失败的数据内容: {forced_data}")
                        report = result.content if hasattr(result, 'content') else ""

                except Exception as e:
                    logger.error(f"[解禁监控师] ❌ 强制补救过程失败: {e}")
                    import traceback
                    logger.error(f"[解禁监控师] 📋 异常堆栈: {traceback.format_exc()}")
                    report = result.content if hasattr(result, 'content') else ""
            else:
                # 有工具调用，直接使用结果
                report = result.content
        
        total_time_taken = (datetime.now() - start_time).total_seconds()
        logger.info(f"[解禁监控师] 解禁分析完成，总耗时: {total_time_taken:.2f}秒")

        # 🔧 修复死循环问题：返回清洁的AIMessage，不包含tool_calls
        # 这确保工作流图能正确判断分析已完成，避免重复调用
        from langchain_core.messages import AIMessage
        clean_message = AIMessage(content=report)

        logger.info(f"[解禁监控师] ✅ 返回清洁消息，报告长度: {len(report)} 字符")

        # 🔧 更新工具调用计数器
        return {
            "messages": [clean_message],
            "lockup_report": report,
            "lockup_tool_call_count": tool_call_count + 1
        }

    return lockup_analyst_node
