"""Utilities for working with structured LLM output.

This module provides a unified interface for working with structured output
across different LLM providers. It handles the provider-specific variations
in how structured output is requested and parsed.
"""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class StructuredOutputNotSupported(Exception):
    """Exception raised when structured output is not supported by the LLM."""
    pass


def get_structured_llm(
    llm: Any,
    schema: Type[T],
    provider: Optional[str] = None,
) -> Any:
    """
    Get an LLM wrapped with structured output capabilities.

    Args:
        llm: The base LLM instance
        schema: The Pydantic schema to use for structured output
        provider: Optional provider hint ('openai', 'anthropic', 'gemini')

    Returns:
        An LLM that will return structured output according to the schema

    Raises:
        StructuredOutputNotSupported: If the provider doesn't support structured output
    """
    # Check if LLM supports native structured output
    if hasattr(llm, "with_structured_output"):
        try:
            return llm.with_structured_output(schema)
        except Exception as e:
            raise StructuredOutputNotSupported(f"Provider does not support structured output: {e}")
    
    # For providers without native support, return None to indicate fallback is needed
    raise StructuredOutputNotSupported("Provider does not have with_structured_output method")


def parse_structured_output(
    result: Any,
    schema: Type[T],
    provider: Optional[str] = None,
) -> T:
    """
    Parse the LLM output into the specified schema.

    Args:
        result: The raw output from the LLM
        schema: The Pydantic schema to parse into
        provider: Optional provider hint

    Returns:
        The parsed Pydantic object
    """
    if isinstance(result, schema):
        return result

    if provider == "anthropic":
        # Handle Anthropic tool call format
        if hasattr(result, 'tool_calls') and result.tool_calls:
            return schema(**result.tool_calls[0].args)

    if isinstance(result, dict):
        try:
            return schema(**result)
        except Exception:
            pass

    # Fallback: try to parse as JSON
    try:
        import json
        if isinstance(result, str):
            # Try to find JSON in the text
            json_match = None
            for start in ["{", "【", "```json", "```"]:
                idx = result.find(start)
                if idx != -1:
                    json_str = result[idx:]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            return schema(**parsed)
                    except json.JSONDecodeError:
                        pass
            
            # Try parsing entire string
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return schema(**parsed)
    except (json.JSONDecodeError, TypeError):
        pass

    # Last resort: try to extract fields from text
    if isinstance(result, str):
        return _extract_from_text(result, schema)

    raise ValueError(f"Unable to parse result into {schema.__name__}: {type(result)}")


def _extract_from_text(text: str, schema: Type[T]) -> T:
    """
    Extract structured data from unstructured text output.

    This is a fallback for providers that don't support structured output
    or when the output format is unexpected.
    """
    import re
    from pydantic import ValidationError
    
    data: dict[str, Any] = {}
    required_fields = []
    
    for field_name, field_info in schema.model_fields.items():
        field_type = field_info.annotation
        is_required = field_info.is_required() if hasattr(field_info, 'is_required') else not field_info.default
        
        # Try to find the field in the text
        if field_name == "rating" or field_name == "recommendation":
            # Look for rating keywords (case insensitive)
            rating_patterns = [
                r"\*\*Rating\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell)",
                r"\*\*建议\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell|买入|增持|持有|减持|卖出)",
                r"(Buy|Overweight|Hold|Underweight|Sell)",
                r"(买入|增持|持有|减持|卖出)"
            ]
            for pattern in rating_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).capitalize()
                    # Map Chinese to English
                    chinese_map = {"买入": "Buy", "增持": "Overweight", "持有": "Hold", "减持": "Underweight", "卖出": "Sell"}
                    if value in chinese_map:
                        value = chinese_map[value]
                    if value in ["Buy", "Overweight", "Hold", "Underweight", "Sell"]:
                        data[field_name] = value
                        break
        
        elif field_name == "action":
            # Look for action keywords
            action_patterns = [
                r"\*\*Action\*\*:\s*(Buy|Hold|Sell)",
                r"(Buy|Hold|Sell)",
                r"(买入|持有|卖出)"
            ]
            for pattern in action_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).capitalize()
                    chinese_map = {"买入": "Buy", "持有": "Hold", "卖出": "Sell"}
                    if value in chinese_map:
                        value = chinese_map[value]
                    if value in ["Buy", "Hold", "Sell"]:
                        data[field_name] = value
                        break
        
        elif field_name in ["executive_summary", "rationale", "investment_thesis", "reasoning", "strategic_actions"]:
            # Look for these fields in the text (usually after **FieldName**:)
            patterns = [
                rf"\*\*{field_name.replace('_', ' ').title()}\*\*:\s*(.+?)(?=\n\*\*|$)",
                rf"\*\*{field_name}\*\*:\s*(.+?)(?=\n\*\*|$)",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    data[field_name] = match.group(1).strip()
                    break
            
            # If not found, try to extract from section after field name
            if field_name not in data:
                # Look for text after field keywords
                keywords = {
                    "executive_summary": ["摘要", "总结", "executive"],
                    "rationale": ["理由", "逻辑", "原因"],
                    "investment_thesis": ["投资逻辑", "投资理由", "thesis"],
                    "reasoning": ["推理", "逻辑"],
                    "strategic_actions": ["策略", "行动", "建议"]
                }
                if field_name in keywords:
                    for kw in keywords[field_name]:
                        pattern = rf"{kw}[：:]\s*(.+?)(?=\n\*\*|\n\n|$)"
                        match = re.search(pattern, text, re.DOTALL)
                        if match:
                            data[field_name] = match.group(1).strip()
                            break
        
        elif field_name in ["price_target", "entry_price", "stop_loss"]:
            # Look for numbers that could be prices
            price_keywords = {
                "price_target": ["目标价", "目标价格", "目标", "Price Target"],
                "entry_price": ["入场价", "Entry", "入场"],
                "stop_loss": ["止损", "Stop", "止损价"]
            }
            for kw in price_keywords.get(field_name, []):
                pattern = rf"{kw}[：:\s]*([\d.]+)"
                match = re.search(pattern, text)
                if match:
                    try:
                        data[field_name] = float(match.group(1))
                        break
                    except ValueError:
                        pass
        
        elif field_name == "time_horizon":
            match = re.search(r"(Time\s+Horizon|时间周期|持有期|期限)[：:\s]*([\w\s-]+)", text)
            if match:
                data[field_name] = match.group(2).strip()
        
        elif field_name == "position_sizing":
            match = re.search(r"(Position\s+Sizing|仓位|头寸|持仓)[：:\s]*([\w\s%]+)", text)
            if match:
                data[field_name] = match.group(2).strip()
    
    # If we have a rating/recommendation, provide defaults for missing required fields
    if "rating" in data or "recommendation" in data:
        field_name = "rating" if "rating" in data else "recommendation"
        if field_name not in data:
            # Use a default if not found
            data[field_name] = "Hold"
    
    # Try to create the schema instance
    try:
        return schema(**data)
    except ValidationError as e:
        # If validation fails, create with only valid fields and defaults
        valid_data = {}
        for k, v in data.items():
            if k in schema.model_fields:
                valid_data[k] = v
        
        # Provide defaults for missing required fields
        for field_name, field_info in schema.model_fields.items():
            if field_name not in valid_data:
                if field_name in ["rating", "recommendation", "action"]:
                    valid_data[field_name] = "Hold"
                elif field_name in ["price_target", "entry_price", "stop_loss"]:
                    valid_data[field_name] = None
                elif field_name in ["executive_summary", "rationale", "investment_thesis", "reasoning", "strategic_actions"]:
                    valid_data[field_name] = text[:500] if text else "无法从分析中提取详细信息"
                elif field_name == "time_horizon":
                    valid_data[field_name] = "1-3个月"
                elif field_name == "position_sizing":
                    valid_data[field_name] = "待定"
        
        return schema(**valid_data)


def get_format_instructions(schema: Type[T]) -> str:
    """
    Get format instructions for the given schema.

    Args:
        schema: The Pydantic schema

    Returns:
        Format instructions string for the prompt
    """
    parser = PydanticOutputParser(pydantic_object=schema)
    return parser.get_format_instructions()