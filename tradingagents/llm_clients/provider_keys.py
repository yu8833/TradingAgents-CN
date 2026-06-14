"""provider_keys 兼容层
为旧代码提供统一的 provider key 相关工具
新 tradingagents 模块中此功能分散在各 LLM client 中
"""

import os
from typing import Dict, Optional

# provider 名称标准化映射
# 左侧为各种可能的写法（不区分大小写），右侧为标准化后的名称
_CANONICAL_MAP: Dict[str, str] = {
    "openai": "openai",
    "gpt": "openai",
    "gpt-4": "openai",
    "gpt-3.5": "openai",
    "chatgpt": "openai",
    "azure": "azure",
    "azure-openai": "azure",
    "azure_openai": "azure",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "claude-3": "anthropic",
    "google": "google",
    "gemini": "google",
    "bard": "google",
    "zhipu": "zhipu",
    "glm": "zhipu",
    "智谱": "zhipu",
    "deepseek": "deepseek",
    "qianfan": "qianfan",
    "百度": "qianfan",
    "dashscope": "dashscope",
    "qwen": "dashscope",
    "阿里": "dashscope",
    "alibabacloud": "dashscope",
    "qianwen": "dashscope",
    "302ai": "302ai",
    "aihubmix": "aihubmix",
    "moonshot": "moonshot",
    "kimi": "moonshot",
    "siliconflow": "siliconflow",
    "openrouter": "openrouter",
    "oneapi": "oneapi",
    "newapi": "newapi",
}

# 标准 provider 名称集合
CANONICAL_PROVIDERS = set(_CANONICAL_MAP.values())

# 别名表 - 供外部直接访问
canonical_aliases = _CANONICAL_MAP


def normalize_provider_key(provider: Optional[str]) -> str:
    """标准化 provider 名称

    Args:
        provider: provider 名称（可能是各种格式）

    Returns:
        标准化后的 provider 名称，如果无法识别则原样返回（小写）
    """
    if not provider:
        return "openai"
    p = str(provider).lower().strip()
    if p in _CANONICAL_MAP:
        return _CANONICAL_MAP[p]
    # 部分匹配
    for alias, canonical in _CANONICAL_MAP.items():
        if alias in p or p in alias:
            return canonical
    return p


def default_backend_url(provider_key: Optional[str]) -> str:
    """获取 provider 的默认后端 API URL

    Args:
        provider_key: 标准化后的 provider 名称

    Returns:
        默认 API 端点 URL
    """
    provider = normalize_provider_key(provider_key)
    urls = {
        "openai": "https://api.openai.com/v1",
        "google": "https://generativelanguage.googleapis.com/v1beta",
        "anthropic": "https://api.anthropic.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "dashscope": "https://dashscope.aliyuncs.com/api/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        "moonshot": "https://api.moonshot.cn/v1",
        "302ai": "https://api.302.ai/v1",
        "aihubmix": "https://aihubmix.com/v1",
        "azure": "https://example.openai.azure.com/openai/deployments",
        "siliconflow": "https://api.siliconflow.cn/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "qianfan": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
        "oneapi": "http://localhost:3000/v1",
    }
    return urls.get(provider, "https://api.openai.com/v1")


def env_key_for_provider(provider_key: Optional[str]) -> str:
    """获取对应 provider 的 API key 环境变量名称

    Args:
        provider_key: 标准化后的 provider 名称

    Returns:
        对应的环境变量名称
    """
    provider = normalize_provider_key(provider_key)
    env_map = {
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "zhipu": "ZHIPUAI_API_KEY",
        "moonshot": "MOONSHOT_API_KEY",
        "302ai": "AI302_API_KEY",
        "aihubmix": "AIHUBMIX_API_KEY",
        "azure": "AZURE_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "qianfan": "QIANFAN_API_KEY",
        "oneapi": "ONEAPI_API_KEY",
    }
    return env_map.get(provider, f"{provider.upper()}_API_KEY")


def get_api_key(provider_key: Optional[str]) -> Optional[str]:
    """从环境变量获取指定 provider 的 API key

    Args:
        provider_key: 标准化后的 provider 名称

    Returns:
        API key 字符串，如果未设置则返回 None
    """
    env_var = env_key_for_provider(provider_key)
    return os.environ.get(env_var)
