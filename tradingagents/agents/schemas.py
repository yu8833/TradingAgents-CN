"""Pydantic schemas used by agents that produce structured output.

The framework's primary artifact is still prose: each agent's natural-language
reasoning is what users read in the saved markdown reports and what the
downstream agents read as context.  Structured output is layered onto the
three decision-making agents (Research Manager, Trader, Portfolio Manager)
so that:

- Their outputs follow consistent section headers across runs and providers
- Each provider's native structured-output mode is used (json_schema for
  OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic)
- Schema field descriptions become the model's output instructions, freeing
  the prompt body to focus on context and the rating-scale guidance
- A render helper turns the parsed Pydantic instance back into the same
  markdown shape the rest of the system already consumes, so display,
  memory log, and saved reports keep working unchanged
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared rating types
# ---------------------------------------------------------------------------


class PortfolioRating(str, Enum):
    """5-tier rating used by the Research Manager and Portfolio Manager."""

    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"


class TraderAction(str, Enum):
    """3-tier transaction direction used by the Trader.

    The Trader's job is to translate the Research Manager's investment plan
    into a concrete transaction proposal: should the desk execute a Buy, a
    Sell, or sit on Hold this round.  Position sizing and the nuanced
    Overweight / Underweight calls happen later at the Portfolio Manager.
    """

    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


# ---------------------------------------------------------------------------
# Research Manager
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Structured investment plan produced by the Research Manager.

    Hand-off to the Trader: the recommendation pins the directional view,
    the rationale captures which side of the bull/bear debate carried the
    argument, and the strategic actions translate that into concrete
    instructions the trader can execute against.
    """

    recommendation: PortfolioRating = Field(
        description=(
            "The investment recommendation. Exactly one of Buy / Overweight / "
            "Hold / Underweight / Sell. Reserve Hold for situations where the "
            "evidence on both sides is genuinely balanced; otherwise commit to "
            "the side with the stronger arguments."
        ),
    )
    rationale: str = Field(
        description=(
            "Conversational summary of the key points from both sides of the "
            "debate, ending with which arguments led to the recommendation. "
            "Speak naturally, as if to a teammate."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete steps for the trader to implement the recommendation, "
            "including position sizing guidance consistent with the rating."
        ),
    )


def render_research_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan to markdown for storage and the trader's prompt context."""
    return "\n".join([
        f"**Recommendation**: {plan.recommendation.value}",
        "",
        f"**Rationale**: {plan.rationale}",
        "",
        f"**Strategic Actions**: {plan.strategic_actions}",
    ])


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Structured transaction proposal produced by the Trader.

    The trader reads the Research Manager's investment plan and the analyst
    reports, then turns them into a concrete transaction: what action to
    take, the reasoning that justifies it, and the practical levels for
    entry, stop-loss, and sizing.
    """

    action: TraderAction = Field(
        description="The transaction direction. Exactly one of Buy / Hold / Sell.",
    )
    reasoning: str = Field(
        description=(
            "The case for this action, anchored in the analysts' reports and "
            "the research plan. Two to four sentences."
        ),
    )
    entry_price: Optional[float] = Field(
        default=None,
        description="Optional entry price target in the instrument's quote currency.",
    )
    stop_loss: Optional[float] = Field(
        default=None,
        description="Optional stop-loss price in the instrument's quote currency.",
    )
    position_sizing: Optional[str] = Field(
        default=None,
        description="Optional sizing guidance, e.g. '5% of portfolio'.",
    )


def render_trader_proposal(proposal: TraderProposal) -> str:
    """Render a TraderProposal to markdown.

    The trailing ``FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`` line is
    preserved for backward compatibility with the analyst stop-signal text
    and any external code that greps for it.
    """
    parts = [
        f"**Action**: {proposal.action.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Entry Price**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Position Sizing**: {proposal.position_sizing}"])
    parts.extend([
        "",
        f"FINAL TRANSACTION PROPOSAL: **{proposal.action.value.upper()}**",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager
# ---------------------------------------------------------------------------


class RiskControlDecision(BaseModel):
    """Structured risk control assessment produced by the Risk Manager phase.

    The Risk Manager's job is to set risk constraints, not to make the final
    trading decision. This schema captures position sizing limits, stop-loss
    levels, and worst-case scenarios that the Portfolio Manager must respect.
    """

    max_position_size: float = Field(
        description=(
            "Maximum recommended position size as percentage of portfolio "
            "(e.g., 5.0 means 5% max). This is a hard limit the Portfolio Manager "
            "must respect."
        ),
    )
    recommended_position_size: float = Field(
        description=(
            "Recommended position size as percentage of portfolio, considering "
            "the risk/reward profile (e.g., 3.0 means 3% recommended). "
            "This is softer guidance, not a hard limit."
        ),
    )
    stop_loss_level: float = Field(
        description=(
            "Recommended stop-loss as percentage decline from entry price "
            "(e.g., 5.0 means -5% stop-loss). This protects against catastrophic losses."
        ),
    )
    max_acceptable_loss: float = Field(
        description=(
            "Maximum acceptable loss as percentage of portfolio "
            "(e.g., 0.5 means max 0.5% of total portfolio). "
            "The position size must respect this constraint."
        ),
    )
    worst_case_scenario: str = Field(
        description=(
            "Description of the worst-case scenario that could unfold, "
            "including estimated loss magnitude (e.g., '连续2日跌停板，损失约4%')."
        ),
    )
    risk_rating: PortfolioRating = Field(
        description=(
            "Risk assessment rating. Exactly one of Buy / Overweight / Hold / "
            "Underweight / Sell, chosen based on the RISK PROFILE (not upside potential). "
            "Buy = low risk, Sell = high risk."
        ),
    )
    risk_mitigation: str = Field(
        description=(
            "Specific risk mitigation strategies (e.g., '分批建仓，避免一次性all-in'). "
            "Two to four sentences."
        ),
    )


def render_risk_control_decision(decision: RiskControlDecision) -> str:
    """Render a RiskControlDecision to markdown for storage."""
    risk_rating_cn = {
        "Buy": "低风险（买入级）",
        "Overweight": "较低风险（增持级）",
        "Hold": "中等风险（持有级）",
        "Underweight": "较高风险（减持级）",
        "Sell": "高风险（卖出级）",
    }.get(decision.risk_rating.value, decision.risk_rating.value)

    return "\n".join([
        f"**风险等级：{risk_rating_cn}**",
        "",
        f"**Risk Rating**: {decision.risk_rating.value}",
        "",
        f"**风险等级说明**：综合评估该股票的风险状况为{risk_rating_cn}，基于以下风险控制参数得出。",
        "",
        f"**Max Position Size**: {decision.max_position_size}%",
        "",
        f"**Recommended Position Size**: {decision.recommended_position_size}%",
        "",
        f"**Stop Loss Level**: -{decision.stop_loss_level}%",
        "",
        f"**Max Acceptable Loss**: {decision.max_acceptable_loss}%",
        "",
        f"**Worst Case Scenario**: {decision.worst_case_scenario}",
        "",
        f"**Risk Mitigation**: {decision.risk_mitigation}",
    ])


class PortfolioDecision(BaseModel):
    """Structured output produced by the Portfolio Manager.

    The model fills every field as part of its primary LLM call; no separate
    extraction pass is required. Field descriptions double as the model's
    output instructions, so the prompt body only needs to convey context and
    the rating-scale guidance.
    """

    rating: PortfolioRating = Field(
        description=(
            "The final position rating. Exactly one of Buy / Overweight / Hold / "
            "Underweight / Sell, picked based on the analysts' debate."
        ),
    )
    executive_summary: str = Field(
        description=(
            "A concise action plan covering entry strategy, position sizing, "
            "key risk levels, and time horizon. Two to four sentences."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Detailed reasoning anchored in specific evidence from the analysts' "
            "debate. If prior lessons are referenced in the prompt context, "
            "incorporate them; otherwise rely solely on the current analysis."
        ),
    )
    price_target: Optional[float] = Field(
        default=None,
        description="Optional target price in the instrument's quote currency.",
    )
    time_horizon: Optional[str] = Field(
        default=None,
        description="Optional recommended holding period, e.g. '3-6 months'.",
    )


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render a PortfolioDecision back to the markdown shape the rest of the system expects.

    Memory log, CLI display, and saved report files all read this markdown,
    so the rendered output preserves the exact section headers (``**Rating**``,
    ``**Executive Summary**``, ``**Investment Thesis**``) that downstream
    parsers and the report writers already handle.
    """
    rating_cn = {
        "Buy": "买入",
        "Overweight": "增持",
        "Hold": "持有",
        "Underweight": "减持",
        "Sell": "卖出",
    }.get(decision.rating.value, decision.rating.value)

    parts = [
        f"**最终定性评级：{rating_cn}**",
        "",
        f"**最终交易决策：{rating_cn}**",
        "",
        f"**Rating**: {decision.rating.value}",
        "",
        f"**操作说明**：{decision.executive_summary}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    if decision.time_horizon:
        parts.extend(["", f"**Time Horizon**: {decision.time_horizon}"])
    return "\n".join(parts)
