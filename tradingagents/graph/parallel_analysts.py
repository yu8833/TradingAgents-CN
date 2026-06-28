import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Callable

from langchain_core.messages import HumanMessage, RemoveMessage, ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from tradingagents.agents.analysts.policy_analyst import create_policy_analyst
from tradingagents.agents.analysts.hot_money_tracker import create_hot_money_tracker
from tradingagents.agents.analysts.lockup_watcher import create_lockup_watcher
from tradingagents.dataflows.data_source_logger import get_current_logger, set_current_logger, DataSourceLogger

logger = logging.getLogger(__name__)


ANALYST_CREATORS = {
    "market": create_market_analyst,
    "social": create_social_media_analyst,
    "news": create_news_analyst,
    "fundamentals": create_fundamentals_analyst,
    "policy": create_policy_analyst,
    "hot_money": create_hot_money_tracker,
    "lockup": create_lockup_watcher,
}

ANALYST_REPORT_FIELDS = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
    "policy": "policy_report",
    "hot_money": "hot_money_report",
    "lockup": "lockup_report",
}

ANALYST_DATA_SOURCE_NAMES = {
    "market": "技术分析师",
    "social": "市场情绪分析师",
    "news": "新闻分析师",
    "fundamentals": "基本面分析师",
    "policy": "政策分析师",
    "hot_money": "游资追踪师",
    "lockup": "解禁追踪师",
}


def _extract_report_from_result(result: Any, report_field: str) -> str:
    if isinstance(result, dict) and report_field in result:
        val = result[report_field]
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _has_tool_calls(message: Any) -> bool:
    if not hasattr(message, 'tool_calls'):
        return False
    tc = getattr(message, 'tool_calls', None)
    return tc is not None and len(tc) > 0


def _get_message_content(message: Any) -> str:
    if hasattr(message, 'content'):
        content = getattr(message, 'content', '')
        return content if isinstance(content, str) else str(content)
    return ""


def run_single_analyst(
    analyst_type: str,
    analyst_node: Callable,
    tool_node: ToolNode,
    state: Dict[str, Any],
    max_iterations: int = 10,
) -> Dict[str, Any]:
    company = state.get("company_of_interest", "")
    analyst_name = ANALYST_DATA_SOURCE_NAMES.get(analyst_type, analyst_type)
    
    data_logger = DataSourceLogger(stock_code=company, analyst_name=analyst_name)
    set_current_logger(data_logger)
    
    current_state = dict(state)
    report_field = ANALYST_REPORT_FIELDS.get(analyst_type, f"{analyst_type}_report")
    report = ""
    error_msg = ""
    
    try:
        for i in range(max_iterations):
            logger.debug(f"🔄 [{analyst_type}] 第 {i+1} 次迭代")
            
            try:
                result = analyst_node(current_state)
            except Exception as e:
                error_msg = f"分析师调用异常: {str(e)}"
                logger.error(f"❌ [{analyst_type}] {error_msg}", exc_info=True)
                break
            
            node_report = _extract_report_from_result(result, report_field)
            if node_report:
                report = node_report
                logger.debug(f"✅ [{analyst_type}] 从 node 返回中获取报告，长度: {len(report)}")
                break
            
            if "messages" in result and result["messages"]:
                new_msgs = result["messages"]
                if isinstance(new_msgs, list):
                    current_state["messages"] = current_state["messages"] + new_msgs
                else:
                    current_state["messages"] = current_state["messages"] + [new_msgs]
            
            if not current_state.get("messages"):
                error_msg = "消息队列为空"
                logger.error(f"❌ [{analyst_type}] {error_msg}")
                break
            
            last_message = current_state["messages"][-1]
            
            if _has_tool_calls(last_message):
                tool_calls = last_message.tool_calls
                new_tool_messages = []
                tools_by_name = getattr(tool_node, 'tools_by_name', {})
                
                logger.debug(f"🔧 [{analyst_type}] 执行 {len(tool_calls)} 个工具调用")
                
                for tc in tool_calls:
                    tool_name = tc.get('name', '') if isinstance(tc, dict) else getattr(tc, 'name', '')
                    tool_args = tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                    tool_id = tc.get('id', '') if isinstance(tc, dict) else getattr(tc, 'id', '')
                    
                    tool = tools_by_name.get(tool_name)
                    if tool:
                        try:
                            tool_output = tool.invoke(tool_args)
                            new_tool_messages.append(
                                ToolMessage(content=str(tool_output), tool_call_id=tool_id)
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ [{analyst_type}] 工具 {tool_name} 调用失败: {e}")
                            new_tool_messages.append(
                                ToolMessage(content=f"Tool call error: {str(e)}", tool_call_id=tool_id)
                            )
                    else:
                        logger.warning(f"⚠️ [{analyst_type}] 未找到工具: {tool_name}")
                        new_tool_messages.append(
                            ToolMessage(content=f"Tool not found: {tool_name}", tool_call_id=tool_id)
                        )
                
                current_state["messages"] = current_state["messages"] + new_tool_messages
            else:
                content = _get_message_content(last_message)
                if content and len(content.strip()) > 20:
                    report = content.strip()
                    logger.debug(f"✅ [{analyst_type}] 从最后一条消息提取报告，长度: {len(report)}")
                else:
                    error_msg = f"最后一条消息内容过短或为空（长度: {len(content)}）"
                    logger.warning(f"⚠️ [{analyst_type}] {error_msg}")
                break
        
        if not report and not error_msg:
            error_msg = f"达到最大迭代次数 ({max_iterations}) 仍未生成报告"
            logger.warning(f"⚠️ [{analyst_type}] {error_msg}")
            
            if current_state.get("messages"):
                for msg in reversed(current_state["messages"]):
                    content = _get_message_content(msg)
                    if content and len(content.strip()) > 50:
                        report = content.strip()
                        logger.info(f"🔧 [{analyst_type}] 兜底：从历史消息中提取报告，长度: {len(report)}")
                        break
        
        if not report and error_msg:
            report = f"[分析未能完成: {error_msg}]"
        
    except Exception as e:
        report = f"[分析异常: {str(e)}]"
        logger.error(f"❌ [{analyst_type}] 执行异常: {e}", exc_info=True)
    finally:
        set_current_logger(None)
    
    logger.info(f"📊 [{analyst_type}] 最终报告长度: {len(report)}")
    return {report_field: report}


def create_parallel_analysts_node(
    quick_thinking_llm: Any,
    tool_nodes: Dict[str, ToolNode],
    selected_analysts: List[str],
):
    analyst_instances = {}
    for analyst_type in selected_analysts:
        creator = ANALYST_CREATORS.get(analyst_type)
        if creator:
            analyst_instances[analyst_type] = creator(quick_thinking_llm)
    
    def parallel_analysts_node(state: AgentState) -> dict:
        logger.info(f"🚀 开始并行执行 {len(selected_analysts)} 位分析师: {selected_analysts}")
        
        base_state = dict(state)
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(selected_analysts)) as executor:
            future_to_analyst = {}
            for analyst_type in selected_analysts:
                analyst_node = analyst_instances.get(analyst_type)
                tool_node = tool_nodes.get(analyst_type)
                if analyst_node and tool_node:
                    future = executor.submit(
                        run_single_analyst,
                        analyst_type,
                        analyst_node,
                        tool_node,
                        base_state,
                    )
                    future_to_analyst[future] = analyst_type
                else:
                    logger.warning(f"⚠️ 分析师 {analyst_type} 缺少 node 或 tool_node，跳过")
                    report_field = ANALYST_REPORT_FIELDS.get(analyst_type, f"{analyst_type}_report")
                    results[report_field] = f"[分析师 {analyst_type} 未初始化]"
            
            for future in as_completed(future_to_analyst):
                analyst_type = future_to_analyst[future]
                try:
                    result = future.result()
                    results.update(result)
                    logger.info(f"✅ 分析师 {analyst_type} 完成")
                except Exception as e:
                    logger.error(f"❌ 分析师 {analyst_type} 执行失败: {e}", exc_info=True)
                    report_field = ANALYST_REPORT_FIELDS.get(analyst_type, f"{analyst_type}_report")
                    results[report_field] = f"[分析失败: {str(e)}]"
        
        for analyst_type in selected_analysts:
            report_field = ANALYST_REPORT_FIELDS.get(analyst_type, f"{analyst_type}_report")
            if report_field not in results:
                results[report_field] = f"[分析师 {analyst_type} 未执行]"
                logger.warning(f"⚠️ 分析师 {analyst_type} 未产生结果，填充占位")
        
        messages = state.get("messages", [])
        results["messages"] = messages
        
        logger.info(f"✅ 所有分析师并行执行完成，共 {len(selected_analysts)} 位")
        return results
    
    return parallel_analysts_node
