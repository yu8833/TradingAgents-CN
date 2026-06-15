"""TradingAgents - 智能交易研究平台。

核心子模块
--------
tradingagents.agents        LLM 智能体（分析师 / 风险管理 / 交易）
tradingagents.config        配置管理（环境变量 / MongoDB 存储）
tradingagents.dataflows     数据采集层（A 股 / 美股 / 新闻 / 缓存）
tradingagents.graph         LangGraph 工作流
tradingagents.llm_clients   LLM 客户端工厂
tradingagents.tools         工具层（技术指标计算等）
tradingagents.utils         通用工具
"""

__version__ = "1.0.0-preview"
__all__ = ["__version__"]
