"""Data quality assessment utilities for analyst reports.

This module provides tools to assess the quality of data used in analysis,
helping to identify low-confidence reports and reduce reliance on them.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class DataQualityGrade(str, Enum):
    """Grades for data quality assessment."""
    
    A = "A"  # High confidence - complete and reliable data
    B = "B"  # Good confidence - mostly complete data
    C = "C"  # Medium confidence - some gaps or inconsistencies
    D = "D"  # Low confidence - significant gaps
    F = "F"  # Very low confidence - unreliable or missing data


class DataQualityReport:
    """Represents the quality assessment of a data source."""
    
    def __init__(
        self,
        grade: DataQualityGrade,
        confidence_score: float,
        issues: list[str] = None,
        recommendations: list[str] = None,
    ):
        self.grade = grade
        self.confidence_score = confidence_score
        self.issues = issues or []
        self.recommendations = recommendations or []
    
    def __str__(self):
        return f"DataQualityReport(grade={self.grade}, confidence={self.confidence_score:.2f}, issues={self.issues})"


def assess_report_quality(
    report_content: str,
    report_type: str = "general",
    expected_fields: Optional[list[str]] = None,
) -> DataQualityReport:
    """
    Assess the quality of an analyst report.
    
    Args:
        report_content: The content of the report to assess
        report_type: Type of report (e.g., 'market', 'fundamentals', 'sentiment', 'news')
        expected_fields: List of expected fields for this report type
    
    Returns:
        DataQualityReport with grade and confidence score
    """
    issues = []
    recommendations = []
    confidence_score = 1.0
    
    if not report_content or len(report_content.strip()) < 50:
        issues.append("报告内容过短或为空")
        confidence_score -= 0.5
    
    if "无法获取" in report_content or "缺失" in report_content or "无数据" in report_content:
        issues.append("报告中包含缺失数据的提示")
        confidence_score -= 0.2
    
    if "历史教训表明" in report_content or "类似标的上" in report_content:
        issues.append("报告包含主观臆测，缺少数据支撑")
        confidence_score -= 0.15
    
    if "可能" in report_content or "或许" in report_content or "大概" in report_content:
        # 这些词如果太多可能表示不确定性
        count = report_content.count("可能") + report_content.count("或许") + report_content.count("大概")
        if count > 5:
            issues.append(f"报告包含过多不确定表述（{count}次）")
            confidence_score -= min(count * 0.02, 0.2)
    
    if expected_fields:
        missing_fields = []
        for field in expected_fields:
            if field.lower() not in report_content.lower():
                missing_fields.append(field)
        
        if missing_fields:
            issues.append(f"缺少预期字段: {', '.join(missing_fields)}")
            confidence_score -= len(missing_fields) * 0.05
    
    if report_type == "fundamentals":
        fundamental_keywords = ["营收", "净利润", "市盈率", "市净率", "资产负债", "现金流"]
        found_count = sum(1 for kw in fundamental_keywords if kw in report_content)
        if found_count < 3:
            issues.append(f"基本面报告缺少关键财务指标（仅找到{found_count}个）")
            confidence_score -= 0.1
    
    if report_type == "market":
        technical_keywords = ["均线", "MACD", "RSI", "成交量", "支撑位", "阻力位"]
        found_count = sum(1 for kw in technical_keywords if kw in report_content)
        if found_count < 3:
            issues.append(f"市场报告缺少关键技术指标（仅找到{found_count}个）")
            confidence_score -= 0.1
    
    confidence_score = max(0.0, min(1.0, confidence_score))
    
    if confidence_score >= 0.9:
        grade = DataQualityGrade.A
    elif confidence_score >= 0.75:
        grade = DataQualityGrade.B
    elif confidence_score >= 0.6:
        grade = DataQualityGrade.C
    elif confidence_score >= 0.4:
        grade = DataQualityGrade.D
    else:
        grade = DataQualityGrade.F
    
    if grade in [DataQualityGrade.D, DataQualityGrade.F]:
        recommendations.append("此报告可信度较低，建议减少依赖")
        recommendations.append("考虑从其他数据源获取补充信息")
    
    return DataQualityReport(
        grade=grade,
        confidence_score=confidence_score,
        issues=issues,
        recommendations=recommendations,
    )


def get_quality_weight(grade: DataQualityGrade) -> float:
    """
    Get the weight to apply to a report based on its quality grade.
    
    Args:
        grade: The data quality grade
        
    Returns:
        Weight factor (0.0 to 1.0)
    """
    weights = {
        DataQualityGrade.A: 1.0,
        DataQualityGrade.B: 0.85,
        DataQualityGrade.C: 0.65,
        DataQualityGrade.D: 0.35,
        DataQualityGrade.F: 0.1,
    }
    return weights.get(grade, 0.5)


def format_quality_report(report: DataQualityReport) -> str:
    """Format a data quality report for inclusion in prompts."""
    lines = [
        f"📊 数据质量评估: {report.grade.value} (可信度: {report.confidence_score:.1%})"
    ]
    
    if report.issues:
        lines.append("\n⚠️ 发现的问题:")
        for issue in report.issues:
            lines.append(f"  - {issue}")
    
    if report.recommendations:
        lines.append("\n💡 建议:")
        for rec in report.recommendations:
            lines.append(f"  - {rec}")
    
    return "\n".join(lines)