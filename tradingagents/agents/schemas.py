"""Pydantic schemas used by agents that produce structured output.

**daily_stock_analysis 风格**：结构化输出使用中文字段名，
包括「核心洞察 / 操作建议 / 趋势预测 / 策略点位 / 理想买入 / 二次买入 / 止损价格 / 止盈目标」。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 共享评级类型（中文 5 档评级）
# ---------------------------------------------------------------------------


class AShareRating(str, Enum):
    """A股 5 档评级：强烈买入 / 买入 / 持有 / 减仓 / 卖出。"""

    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    REDUCE = "减仓"
    SELL = "卖出"


class AShareAction(str, Enum):
    """3 档操作方向：买入 / 持有 / 卖出。"""

    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"


class RiskLevelCN(str, Enum):
    """风险等级（中文）。"""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


# ---------------------------------------------------------------------------
# 研究经理（Research Manager）输出结构
# ---------------------------------------------------------------------------


class ResearchPlanCN(BaseModel):
    """研究经理的投资计划。输出中文化，以 daily_stock_analysis 风格组织。"""

    rating: AShareRating = Field(
        description="投资建议评级。严格从「强烈买入 / 买入 / 持有 / 减仓 / 卖出」选一个。",
    )
    核心洞察: str = Field(
        description=(
            "2-4 句，用简洁中文描述核心逻辑。"
            "涵盖：市场主要矛盾、资金态度、关键催化因素。"
        ),
    )
    战略行动: str = Field(
        description="给交易员的操作建议，用中文分步骤描述，包含建仓策略和时机判断。",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="对建议的信心：0.0~1.0。基于证据强度、分析师一致性，使用两位小数。",
    )
    risk_level: Optional[RiskLevelCN] = Field(
        default=None,
        description="风险等级：低 / 中 / 高。",
    )


def render_research_plan_cn(plan: ResearchPlanCN) -> str:
    """将 ResearchPlanCN 渲染为中文 markdown，便于下游存储与解析。"""
    parts = [
        f"**评级**: {plan.rating.value}",
        "",
        f"**核心洞察**: {plan.核心洞察}",
        "",
        f"**战略行动**: {plan.战略行动}",
    ]
    if plan.confidence_score is not None:
        parts += ["", f"**置信度**: {plan.confidence_score}"]
    if plan.risk_level is not None:
        parts += ["", f"**风险等级**: {plan.risk_level.value}"]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 交易员（Trader）输出结构
# ---------------------------------------------------------------------------


class TraderProposalCN(BaseModel):
    """交易员的交易建议。daily_stock_analysis 风格：
    包含操作建议 + 关键点位（理想买入/二次买入/止损/止盈）。
    """

    操作建议: AShareAction = Field(
        description="交易方向。严格从「买入 / 持有 / 卖出」选一个。",
    )
    核心理由: str = Field(
        description=(
            "支持该行动的中文理由，2-4 句，锚定在分析师报告和研究计划中的证据。"
        ),
    )

    # 点位信息
    理想买入: Optional[float] = Field(
        default=None,
        description="首次建仓理想价格（标的计价货币）。通常在支撑位上方或回调支撑位附近。",
    )
    二次买入: Optional[float] = Field(
        default=None,
        description="第二档加仓价格。若跌破理想买入价，但仍看多，可在更低支撑位补仓。",
    )
    止损价格: Optional[float] = Field(
        default=None,
        description="无条件止损价格。建议在入场价的 -5%~-10% 或最近支撑位下方。",
    )
    止盈目标: Optional[float] = Field(
        default=None,
        description="止盈目标价格。参考技术面阻力位或估值模型目标价。",
    )

    # 辅助信息
    支撑位: Optional[float] = Field(
        default=None,
        description="关键支撑位价格（近期低点 / 均线支撑）。",
    )
    阻力位: Optional[float] = Field(
        default=None,
        description="关键阻力位价格（近期高点 / 均线压力）。",
    )
    建议仓位: Optional[str] = Field(
        default=None,
        description="仓位建议，如「轻仓 3%」「半仓参与」等。",
    )
    持仓周期: Optional[str] = Field(
        default=None,
        description="持有周期建议，如「3-6 个月」「1-2 周」。",
    )


def render_trader_proposal_cn(proposal: TraderProposalCN) -> str:
    """将 TraderProposalCN 渲染为中文 markdown。"""
    parts = [
        f"**操作建议**: {proposal.操作建议.value}",
        "",
        f"**核心理由**: {proposal.核心理由}",
    ]
    if proposal.理想买入 is not None:
        parts.extend(["", f"**理想买入价**: {proposal.理想买入}"])
    if proposal.二次买入 is not None:
        parts.extend(["", f"**二次买入价**: {proposal.二次买入}"])
    if proposal.止损价格 is not None:
        parts.extend(["", f"**止损价格**: {proposal.止损价格}"])
    if proposal.止盈目标 is not None:
        parts.extend(["", f"**止盈目标**: {proposal.止盈目标}"])
    if proposal.支撑位 is not None:
        parts.extend(["", f"**支撑位**: {proposal.支撑位}"])
    if proposal.阻力位 is not None:
        parts.extend(["", f"**阻力位**: {proposal.阻力位}"])
    if proposal.建议仓位:
        parts.extend(["", f"**建议仓位**: {proposal.建议仓位}"])
    if proposal.持仓周期:
        parts.extend(["", f"**持仓周期**: {proposal.持仓周期}"])
    parts.extend([
        "",
        f"最终交易建议：**{proposal.操作建议.value}**",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 组合经理（Portfolio Manager）输出结构（核心决策）
# ---------------------------------------------------------------------------


class PortfolioDecisionCN(BaseModel):
    """组合经理的最终投资决策。daily_stock_analysis 风格：

    **核心输出字段**（必须填）：
    - 评级、核心洞察、操作建议、趋势预测、策略点位
    - 理想买入、二次买入、止损价格、止盈目标
    """

    # ----------------- 文字描述类 -----------------
    评级: AShareRating = Field(
        description="最终投资评级。严格从「强烈买入 / 买入 / 持有 / 减仓 / 卖出」选一个。",
    )
    核心洞察: str = Field(
        description=(
            "2-4 句简洁中文行动总结。包含：市场主要矛盾、资金态度、关键催化事件、"
            "对标的的方向性判断。"
        ),
    )
    投资逻辑: str = Field(
        description=(
            "详细的中文投资论证，锚定在分析师辩论、研究计划和交易建议中的证据。"
        ),
    )
    趋势预测: str = Field(
        description="对标的未来 1-4 周的趋势判断与催化因素，用中文描述。",
    )
    策略点位: str = Field(
        description="重要的技术关键点位：支撑、阻力、关键均线价位，用中文解释。",
    )

    # ----------------- 价格点位类（必填） -----------------
    理想买入: float = Field(
        description=(
            "REQUIRED. 首次建仓理想价格（标的计价货币）。"
            "参考：当前价 × 0.95~1.00 或支撑位上方。"
            "必须给出具体数值，如 21.50。"
        ),
    )
    二次买入: float = Field(
        description=(
            "REQUIRED. 第二档加仓价格（标的计价货币）。"
            "参考：当前价 × 0.90~0.93。"
            "必须给出具体数值，如 19.80。"
        ),
    )
    止损价格: float = Field(
        description=(
            "REQUIRED. 无条件止损价格。"
            "参考：当前价 × 0.88~0.92 或最近支撑位下方。"
            "必须给出具体数值，如 18.20。"
        ),
    )
    止盈目标: float = Field(
        description=(
            "REQUIRED. 止盈目标价格。"
            "参考：当前价 × 1.15~1.25 或阻力位。"
            "必须给出具体数值，如 25.80。"
        ),
    )

    # ----------------- 辅助信息类 -----------------
    持仓周期: Optional[str] = Field(
        default=None,
        description="建议持有周期，如「3-6 个月」「1-2 周」。",
    )
    置信度: Optional[float] = Field(
        default=None,
        description="对最终决策的信心：0.0~1.0，保留两位小数。",
    )
    风险等级: Optional[RiskLevelCN] = Field(
        default=None,
        description="整体风险等级：低 / 中 / 高。",
    )
    风险提示: Optional[str] = Field(
        default=None,
        description="为什么给出这个风险等级的中文说明。",
    )

    # ----------------- 维度子评分 -----------------
    技术面评分: Optional[float] = Field(
        default=None,
        description="技术面评分 0.0~1.0，越高越看涨。",
    )
    基本面评分: Optional[float] = Field(
        default=None,
        description="基本面评分 0.0~1.0，越高越看涨。",
    )
    情绪面评分: Optional[float] = Field(
        default=None,
        description="市场情绪 / 舆情评分 0.0~1.0，越高越积极。",
    )
    政策面评分: Optional[float] = Field(
        default=None,
        description="政策面评分 0.0~1.0，越高越有利。",
    )


def render_pm_decision_cn(decision: PortfolioDecisionCN) -> str:
    """将 PortfolioDecisionCN 渲染为中文 markdown。"""
    parts = [
        f"**评级**: {decision.评级.value}",
        "",
        f"**核心洞察**: {decision.核心洞察}",
        "",
        f"**投资逻辑**: {decision.投资逻辑}",
        "",
        f"**趋势预测**: {decision.趋势预测}",
        "",
        f"**策略点位**: {decision.策略点位}",
    ]
    # 价格点位（必填）
    parts.extend(["", f"**理想买入价**: {decision.理想买入}"])
    parts.extend(["", f"**二次买入价**: {decision.二次买入}"])
    parts.extend(["", f"**止损价格**: {decision.止损价格}"])
    parts.extend(["", f"**止盈目标**: {decision.止盈目标}"])
    if decision.持仓周期:
        parts.extend(["", f"**持仓周期**: {decision.持仓周期}"])
    if decision.置信度 is not None:
        parts.extend(["", f"**置信度**: {decision.置信度}"])
    if decision.风险等级 is not None:
        parts.extend(["", f"**风险等级**: {decision.风险等级.value}"])
    if decision.风险提示:
        parts.extend(["", f"**风险提示**: {decision.风险提示}"])
    # 维度评分
    if decision.技术面评分 is not None:
        parts.extend(["", f"**技术面评分**: {decision.技术面评分}"])
    if decision.基本面评分 is not None:
        parts.extend(["", f"**基本面评分**: {decision.基本面评分}"])
    if decision.情绪面评分 is not None:
        parts.extend(["", f"**情绪面评分**: {decision.情绪面评分}"])
    if decision.政策面评分 is not None:
        parts.extend(["", f"**政策面评分**: {decision.政策面评分}"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 兼容性：保留原有英文类名与函数，以避免破坏其它引用点
# ---------------------------------------------------------------------------

# 为已有的代码保留兼容别名（其它模块可能仍在 import PortfolioDecision / render_pm_decision）
PortfolioRating = AShareRating
TraderAction = AShareAction
RiskLevel = RiskLevelCN
ResearchPlan = ResearchPlanCN
TraderProposal = TraderProposalCN
PortfolioDecision = PortfolioDecisionCN
render_research_plan = render_research_plan_cn
render_trader_proposal = render_trader_proposal_cn
render_pm_decision = render_pm_decision_cn
