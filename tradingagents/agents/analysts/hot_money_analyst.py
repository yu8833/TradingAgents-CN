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

logger = get_logger("analysts.hot_money")


def create_hot_money_analyst(llm, toolkit):
    @log_analyst_module("hot_money")
    def hot_money_analyst_node(state):
        start_time = datetime.now()

        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("hot_money_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        logger.info(f"[游资追踪师] 开始分析 {ticker} 的游资和龙虎榜数据，交易日期: {current_date}")
        session_id = state.get("session_id", "未知会话")
        logger.info(f"[游资追踪师] 会话ID: {session_id}，开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取市场信息
        market_info = StockUtils.get_market_info(ticker)
        logger.info(f"[游资追踪师] 股票类型: {market_info['market_name']}")
        
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
        logger.info(f"[游资追踪师] 公司名称: {company_name}")
        
        # 🔧 创建统一游资数据工具
        logger.info(f"[游资追踪师] 创建游资和龙虎榜数据获取工具...")
        
        def get_hot_money_data(stock_code: str, days: int = 10) -> str:
            """
            获取游资和龙虎榜数据的统一工具
            
            Args:
                stock_code: 股票代码
                days: 获取天数，默认10天
            
            Returns:
                str: 格式化的游资和龙虎榜数据
            """
            logger.info(f"[游资追踪师工具] 开始获取 {stock_code} 的游资数据，天数: {days}")
            
            try:
                import akshare as ak
                import pandas as pd
                import time as time_module
                
                result_parts = []
                stock_code_6 = stock_code.zfill(6)
                
                # 1. 获取龙虎榜详情数据 (stock_lhb_detail_em)
                try:
                    logger.info(f"[游资追踪师工具] 📊 获取龙虎榜详情数据: stock_lhb_detail_em")
                    time_module.sleep(0.5)  # 避免请求过快
                    
                    # stock_lhb_detail_em 需要股票代码和日期范围
                    from datetime import datetime, timedelta
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    lhb_df = ak.stock_lhb_detail_em(symbol=stock_code_6)
                    
                    if lhb_df is not None and not lhb_df.empty:
                        logger.info(f"[游资追踪师工具] ✅ 龙虎榜数据获取成功: {len(lhb_df)} 条记录")
                        
                        # 格式化龙虎榜数据
                        lhb_report = f"\n{'='*60}\n"
                        lhb_report += f"📊 龙虎榜详情 (stock_lhb_detail_em)\n"
                        lhb_report += f"{'='*60}\n"
                        lhb_report += f"股票代码: {stock_code_6}\n"
                        lhb_report += f"记录数量: {len(lhb_df)} 条\n\n"
                        
                        # 显示前几列和数据样本
                        if '序号' in lhb_df.columns:
                            lhb_report += "龙虎榜数据概览:\n"
                            display_df = lhb_df.head(10)
                            lhb_report += display_df.to_string(index=False)
                            lhb_report += "\n\n"
                        
                        # 分析买卖席位
                        if '股票简称' in lhb_df.columns and '龙虎榜净买额' in lhb_df.columns:
                            buy_total = 0
                            sell_total = 0
                            for _, row in lhb_df.iterrows():
                                try:
                                    net_buy = float(str(row.get('龙虎榜净买额', 0)).replace(',', ''))
                                    if net_buy > 0:
                                        buy_total += net_buy
                                    else:
                                        sell_total += abs(net_buy)
                                except:
                                    pass
                            
                            lhb_report += f"📈 游资买卖分析:\n"
                            lhb_report += f"  - 买入总额: {buy_total:,.2f} 万元\n"
                            lhb_report += f"  - 卖出总额: {sell_total:,.2f} 万元\n"
                            lhb_report += f"  - 净买入: {buy_total - sell_total:,.2f} 万元\n\n"
                        
                        # 营业部席位分析
                        if '营业部名称' in lhb_df.columns or '买入席位' in lhb_df.columns:
                            lhb_report += "📍 营业部席位分析:\n"
                            if '营业部名称' in lhb_df.columns:
                                seat_counts = lhb_df['营业部名称'].value_counts().head(10)
                                for seat, count in seat_counts.items():
                                    lhb_report += f"  - {seat}: {count}次上榜\n"
                            lhb_report += "\n"
                        
                        result_parts.append(lhb_report)
                    else:
                        logger.warning(f"[游资追踪师工具] ⚠️ 龙虎榜数据为空")
                        result_parts.append(f"\n⚠️ {stock_code_6} 近期无龙虎榜记录\n")
                        
                except Exception as e:
                    logger.error(f"[游资追踪师工具] ❌ 获取龙虎榜详情失败: {e}")
                    result_parts.append(f"\n⚠️ 龙虎榜详情获取失败: {str(e)}\n")
                
                # 2. 获取主力资金流向 (stock_individual_fund_flow)
                try:
                    logger.info(f"[游资追踪师工具] 💰 获取主力资金流向: stock_individual_fund_flow")
                    time_module.sleep(0.5)  # 避免请求过快
                    
                    fund_df = ak.stock_individual_fund_flow(stock=stock_code_6, market="sh")
                    
                    # 尝试沪市接口失败后尝试深市
                    if fund_df is None or fund_df.empty:
                        fund_df = ak.stock_individual_fund_flow(stock=stock_code_6, market="sz")
                    
                    if fund_df is not None and not fund_df.empty:
                        logger.info(f"[游资追踪师工具] ✅ 资金流向数据获取成功: {len(fund_df)} 条记录")
                        
                        fund_report = f"\n{'='*60}\n"
                        fund_report += f"💰 主力资金流向 (stock_individual_fund_flow)\n"
                        fund_report += f"{'='*60}\n"
                        fund_report += f"股票代码: {stock_code_6}\n"
                        fund_report += f"记录数量: {len(fund_df)} 条\n\n"
                        
                        # 显示最新几天的资金流向
                        if len(fund_df) > 0:
                            fund_report += "近日期金流向:\n"
                            display_df = fund_df.tail(10) if len(fund_df) > 10 else fund_df
                            fund_report += display_df.to_string(index=False)
                            fund_report += "\n\n"
                        
                        # 计算资金净流入/净流出
                        net_inflow_cols = [col for col in fund_df.columns if '净流入' in col or '净流出' in col]
                        if net_inflow_cols:
                            latest_col = net_inflow_cols[0]
                            try:
                                if latest_col in fund_df.columns:
                                    total_net = pd.to_numeric(fund_df[latest_col], errors='coerce').sum()
                                    fund_report += f"📊 累计净流入: {total_net:,.2f} 万元\n"
                                    
                                    # 近5日平均
                                    recent_avg = pd.to_numeric(fund_df[latest_col].tail(5), errors='coerce').mean()
                                    fund_report += f"📊 近5日平均净流入: {recent_avg:,.2f} 万元\n"
                            except Exception as e:
                                logger.warning(f"[游资追踪师工具] ⚠️ 计算资金净流入失败: {e}")
                        
                        result_parts.append(fund_report)
                    else:
                        logger.warning(f"[游资追踪师工具] ⚠️ 资金流向数据为空")
                        result_parts.append(f"\n⚠️ {stock_code_6} 资金流向数据暂时不可用\n")
                        
                except Exception as e:
                    logger.error(f"[游资追踪师工具] ❌ 获取资金流向失败: {e}")
                    result_parts.append(f"\n⚠️ 资金流向获取失败: {str(e)}\n")
                
                # 3. 获取个股资金流向详细数据 (作为补充)
                try:
                    logger.info(f"[游资追踪师工具] 💵 获取个股资金流向详细数据")
                    time_module.sleep(0.5)
                    
                    # 使用 stock_individual_fund_flow_rank 获取排名数据作为参考
                    try:
                        rank_df = ak.stock_individual_fund_flow_rank(indicator="今日")
                        if rank_df is not None and not rank_df.empty:
                            # 查找当前股票
                            stock_rank = rank_df[rank_df['代码'] == stock_code_6]
                            if not stock_rank.empty:
                                logger.info(f"[游资追踪师工具] ✅ 找到个股资金排名数据")
                                rank_report = f"\n{'='*60}\n"
                                rank_report += f"🏆 今日个股资金排名 (参考)\n"
                                rank_report += f"{'='*60}\n"
                                rank_report += stock_rank.to_string(index=False)
                                rank_report += "\n\n"
                                result_parts.append(rank_report)
                    except Exception as rank_err:
                        logger.debug(f"[游资追踪师工具] 个股资金排名获取失败: {rank_err}")
                        
                except Exception as e:
                    logger.error(f"[游资追踪师工具] ❌ 获取个股资金流向详细失败: {e}")
                
                # 组合最终结果
                if result_parts:
                    final_report = f"\n{'='*60}\n"
                    final_report += f"🔥 游资追踪分析报告 - {stock_code_6} ({company_name})\n"
                    final_report += f"{'='*60}\n"
                    final_report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    final_report += f"数据范围: 近 {days} 个交易日\n"
                    final_report += "".join(result_parts)
                    final_report += f"\n{'='*60}\n"
                    final_report += "数据来源: AKShare (东方财富)\n"
                    final_report += f"{'='*60}\n"
                    
                    logger.info(f"[游资追踪师工具] ✅ 游资数据获取完成，报告长度: {len(final_report)} 字符")
                    return final_report
                else:
                    return f"❌ 无法获取 {stock_code} 的游资数据，所有数据源均不可用"
                    
            except ImportError as e:
                logger.error(f"[游资追踪师工具] ❌ AKShare未安装: {e}")
                return f"❌ AKShare未安装，无法获取游资数据: {str(e)}"
            except Exception as e:
                logger.error(f"[游资追踪师工具] ❌ 获取游资数据异常: {e}")
                import traceback
                logger.error(f"[游资追踪师工具] 📋 异常堆栈: {traceback.format_exc()}")
                return f"❌ 获取游资数据异常: {str(e)}"
        
        # 设置工具属性
        get_hot_money_data.name = "get_hot_money_data"
        get_hot_money_data.description = """
游资追踪工具 - 获取A股股票的龙虎榜和资金流向数据

功能:
- 获取龙虎榜详情数据 (stock_lhb_detail_em)
- 获取主力资金流向 (stock_individual_fund_flow)
- 分析营业部席位分布
- 计算游资买卖金额和占比
- 识别资金净流入/净流出状态

参数:
- stock_code: 股票代码 (6位A股代码)
- days: 获取天数，默认10天

适用场景:
- 分析游资炒作标的
- 跟踪龙虎榜营业部动向
- 判断主力资金动向
- 识别短线还是波段操作
"""
        
        tools = [get_hot_money_data]
        logger.info(f"[游资追踪师] 已加载游资追踪工具: get_hot_money_data")

        system_message = (
            """您是一位专业的游资追踪分析师，负责分析龙虎榜数据和游资动向对股票价格的影响。

您的核心职责是追踪和分析A股市场的游资行为：

1. **龙虎榜核心地位**
   - 龙虎榜是A股短线定价的核心力量
   - 上榜股票往往具有短期暴涨暴跌的特征
   - 营业部席位是游资的主要操作载体

2. **游资炒作逻辑和风格**
   - 短线游资：打板、连板、龙头战法
   - 波段游资：趋势投资、板块轮动
   - 冷门股挖掘：寻找被低估的标的
   - 热点追逐：政策利好、突发事件驱动

3. **大单流向和主力资金动态**
   - 资金规模：游资通常使用大资金操作
   - 买入集中度：是否有集中买入行为
   - 卖出时机：是否出现高位砸盘
   - 净流入/净流出：判断主力意图

4. **机构和营业部席位分析**
   - 知名游资营业部：华鑫系、章盟主、欢乐海岸等
   - 席位联动：多个关联席位同时上榜
   - 机构专用席位的意义
   - 营业部历史操盘风格

5. **识别游资操作类型**
   - 短线操作：快进快出、当日或次日了结
   - 波段操作：持续多日买入、趋势持有
   - 价值投资：长期布局、业绩驱动

重点分析维度：
- 游资买入卖出金额和占比
- 机构和营业部席位分布
- 主力资金净流入/净流出状态
- 历史龙虎榜模式和股价关联
- 游资撤退信号识别

📊 分析要求：
- 必须调用工具获取真实的龙虎榜和资金流向数据
- 结合股价位置分析游资成本
- 识别是短线博弈还是波段布局
- 分析席位联动和游资风格
- 提供游资动向对股价短期影响的评估

⚠️ 注意事项：
- 游资操作具有高风险性，报告需提示风险
- 龙虎榜数据有时滞，需结合实时行情
- 同一营业部可能代表不同游资，需区分对待
"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位专业的游资追踪分析师。"
                    "\n🚨 CRITICAL REQUIREMENT - 绝对强制要求："
                    "\n"
                    "\n❌ 禁止行为："
                    "\n- 绝对禁止在没有调用工具的情况下直接回答"
                    "\n- 绝对禁止基于推测或假设生成任何分析内容"
                    "\n- 绝对禁止跳过工具调用步骤"
                    "\n- 绝对禁止说'我无法获取实时数据'等借口"
                    "\n"
                    "\n✅ 强制执行步骤："
                    "\n1. 您的第一个动作必须是调用 get_hot_money_data 工具"
                    "\n2. 该工具会获取龙虎榜详情和主力资金流向数据"
                    "\n3. 只有在成功获取数据后，才能开始分析"
                    "\n4. 您的回答必须基于工具返回的真实数据"
                    "\n"
                    "\n🔧 工具调用格式示例："
                    "\n调用: get_hot_money_data(stock_code='{ticker}', days=10)"
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
        
        logger.info(f"[游资追踪师] 准备调用LLM进行游资分析，模型: {model_info}")
        
        # 🚨 DashScope/DeepSeek/Zhipu预处理：强制获取游资数据
        pre_fetched_data = None
        if ('DashScope' in llm.__class__.__name__ 
            or 'DeepSeek' in llm.__class__.__name__
            or 'Zhipu' in llm.__class__.__name__
            ):
            logger.warning(f"[游资追踪师] 🚨 检测到{llm.__class__.__name__}模型，启动预处理强制数据获取...")
            try:
                # 强制预先获取游资数据
                logger.info(f"[游资追踪师] 🔧 预处理：强制调用游资追踪工具...")
                logger.info(f"[游资追踪师] 📊 调用参数: stock_code={ticker}, days=10")

                pre_fetched_data = get_hot_money_data(stock_code=ticker, days=10)

                logger.info(f"[游资追踪师] 📋 预处理返回结果长度: {len(pre_fetched_data) if pre_fetched_data else 0} 字符")
                logger.info(f"[游资追踪师] 📄 预处理返回结果预览 (前500字符): {pre_fetched_data[:500] if pre_fetched_data else 'None'}")

                if pre_fetched_data and len(pre_fetched_data.strip()) > 100:
                    logger.info(f"[游资追踪师] ✅ 预处理成功获取游资数据: {len(pre_fetched_data)} 字符")

                    # 直接基于预获取的数据生成分析，跳过工具调用
                    analysis_system_prompt = f"""您是一位专业的游资追踪分析师。

您的职责是基于提供的龙虎榜和资金流向数据，对股票进行深入的游资动向分析。

分析要点：
1. 龙虎榜席位分布和游资买卖情况
2. 主力资金净流入/净流出状态
3. 营业部席位联动分析
4. 游资操作风格识别（短线/波段）
5. 游资动向对股价短期影响评估

重要说明：游资数据已经为您提供，您无需调用任何工具，直接基于提供的数据进行分析。"""

                    enhanced_prompt = f"""请基于以下已获取的龙虎榜和资金流向数据，对股票 {ticker}（{company_name}）进行详细的游资追踪分析：

=== 游资追踪数据 ===
{pre_fetched_data}

请撰写详细的中文分析报告，包括：
1. 龙虎榜席位分析和游资买卖情况
2. 主力资金流向分析
3. 营业部席位联动和游资风格识别
4. 游资操作类型判断（短线/波段）
5. 游资动向对股价短期影响评估
6. 风险提示

请在报告末尾附上Markdown表格总结关键发现。"""

                    logger.info(f"[游资追踪师] 🔄 使用预获取游资数据直接生成分析...")
                    logger.info(f"[游资追踪师] 📝 系统提示词长度: {len(analysis_system_prompt)} 字符")
                    logger.info(f"[游资追踪师] 📝 用户提示词长度: {len(enhanced_prompt)} 字符")

                    llm_start_time = datetime.now()
                    result = llm.invoke([
                        {"role": "system", "content": analysis_system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ])

                    llm_end_time = datetime.now()
                    llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
                    logger.info(f"[游资追踪师] LLM调用完成（预处理模式），耗时: {llm_time_taken:.2f}秒")

                    if hasattr(result, 'content') and result.content:
                        report = result.content
                        logger.info(f"[游资追踪师] ✅ 预处理模式成功，报告长度: {len(report)} 字符")
                        logger.info(f"[游资追踪师] 📄 报告预览 (前300字符): {report[:300]}")

                        from langchain_core.messages import AIMessage
                        clean_message = AIMessage(content=report)

                        end_time = datetime.now()
                        time_taken = (end_time - start_time).total_seconds()
                        logger.info(f"[游资追踪师] 游资分析完成（预处理模式），总耗时: {time_taken:.2f}秒")
                        return {
                            "messages": [clean_message],
                            "hot_money_report": report,
                            "hot_money_tool_call_count": tool_call_count + 1
                        }
                    else:
                        logger.warning(f"[游资追踪师] ⚠️ LLM返回结果为空，回退到标准模式")

                else:
                    logger.warning(f"[游资追踪师] ⚠️ 预处理获取游资数据失败或内容过短（{len(pre_fetched_data) if pre_fetched_data else 0}字符），回退到标准模式")
                    if pre_fetched_data:
                        logger.warning(f"[游资追踪师] 📄 失败的数据内容: {pre_fetched_data}")

            except Exception as e:
                logger.error(f"[游资追踪师] ❌ 预处理失败: {e}，回退到标准模式")
                import traceback
                logger.error(f"[游资追踪师] 📋 异常堆栈: {traceback.format_exc()}")
        
        # 使用标准的工具调用链
        llm_start_time = datetime.now()
        chain = prompt | llm.bind_tools(tools)
        logger.info(f"[游资追踪师] 开始LLM调用，分析 {ticker} 的游资动向")
        result = chain.invoke({"messages": state["messages"]})
        
        llm_end_time = datetime.now()
        llm_time_taken = (llm_end_time - llm_start_time).total_seconds()
        logger.info(f"[游资追踪师] LLM调用完成，耗时: {llm_time_taken:.2f}秒")

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [游资追踪师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="游资追踪分析",
                specific_requirements="重点关注龙虎榜席位分布、游资买卖金额、资金流向、营业部联动、游资操作风格识别等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="游资追踪师"
            )
        else:
            # 非Google模型的处理逻辑
            logger.info(f"[游资追踪师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")

            # 检查工具调用情况
            current_tool_calls = len(result.tool_calls) if hasattr(result, 'tool_calls') else 0
            logger.info(f"[游资追踪师] LLM调用了 {current_tool_calls} 个工具")
            logger.debug(f"📊 [DEBUG] 累计工具调用次数: {tool_call_count}/{max_tool_calls}")

            if current_tool_calls == 0:
                logger.warning(f"[游资追踪师] ⚠️ {llm.__class__.__name__} 没有调用任何工具，启动补救机制...")
                logger.warning(f"[游资追踪师] 📄 LLM原始响应内容 (前500字符): {result.content[:500] if hasattr(result, 'content') else 'No content'}")

                try:
                    # 强制获取游资数据
                    logger.info(f"[游资追踪师] 🔧 强制调用游资追踪工具获取数据...")
                    logger.info(f"[游资追踪师] 📊 调用参数: stock_code={ticker}, days=10")

                    forced_data = get_hot_money_data(stock_code=ticker, days=10)

                    logger.info(f"[游资追踪师] 📋 强制获取返回结果长度: {len(forced_data) if forced_data else 0} 字符")
                    logger.info(f"[游资追踪师] 📄 强制获取返回结果预览 (前500字符): {forced_data[:500] if forced_data else 'None'}")

                    if forced_data and len(forced_data.strip()) > 100:
                        logger.info(f"[游资追踪师] ✅ 强制获取游资数据成功: {len(forced_data)} 字符")

                        # 基于真实数据重新生成分析
                        forced_prompt = f"""
您是一位专业的游资追踪分析师。请基于以下最新获取的龙虎榜和资金流向数据，对股票 {ticker}（{company_name}）进行详细的游资追踪分析：

=== 游资追踪数据 ===
{forced_data}

=== 分析要求 ===
{system_message}

请基于上述真实数据撰写详细的中文分析报告，包括龙虎榜席位分析、资金流向分析、游资风格识别等。
"""

                        logger.info(f"[游资追踪师] 🔄 基于强制获取的数据重新生成完整分析...")
                        logger.info(f"[游资追踪师] 📝 强制提示词长度: {len(forced_prompt)} 字符")

                        forced_result = llm.invoke([{"role": "user", "content": forced_prompt}])

                        if hasattr(forced_result, 'content') and forced_result.content:
                            report = forced_result.content
                            logger.info(f"[游资追踪师] ✅ 强制补救成功，生成基于真实数据的报告，长度: {len(report)} 字符")
                            logger.info(f"[游资追踪师] 📄 报告预览 (前300字符): {report[:300]}")
                        else:
                            logger.warning(f"[游资追踪师] ⚠️ 强制补救LLM返回为空，使用原始结果")
                            report = result.content if hasattr(result, 'content') else ""
                    else:
                        logger.warning(f"[游资追踪师] ⚠️ 游资追踪工具获取失败或内容过短（{len(forced_data) if forced_data else 0}字符），使用原始结果")
                        if forced_data:
                            logger.warning(f"[游资追踪师] 📄 失败的数据内容: {forced_data}")
                        report = result.content if hasattr(result, 'content') else ""

                except Exception as e:
                    logger.error(f"[游资追踪师] ❌ 强制补救过程失败: {e}")
                    import traceback
                    logger.error(f"[游资追踪师] 📋 异常堆栈: {traceback.format_exc()}")
                    report = result.content if hasattr(result, 'content') else ""
            else:
                # 有工具调用，直接使用结果
                report = result.content
        
        total_time_taken = (datetime.now() - start_time).total_seconds()
        logger.info(f"[游资追踪师] 游资分析完成，总耗时: {total_time_taken:.2f}秒")

        # 🔧 修复死循环问题：返回清洁的AIMessage，不包含tool_calls
        from langchain_core.messages import AIMessage
        clean_message = AIMessage(content=report)

        logger.info(f"[游资追踪师] ✅ 返回清洁消息，报告长度: {len(report)} 字符")

        # 🔧 更新工具调用计数器
        return {
            "messages": [clean_message],
            "hot_money_report": report,
            "hot_money_tool_call_count": tool_call_count + 1
        }

    return hot_money_analyst_node
