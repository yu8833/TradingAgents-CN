"""
Vibe-Research 融合模块 API 路由
提供复盘（大盘指数/市场情绪/资金流/短线情绪/成交额榜）、资讯雷达、板块、AI对话等接口
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
import json
import os
import asyncio

from app.core.response import ok
from app.services.newsradar import get_radar_cached, fetch_radar
from app.services.market_overview import (
    get_overview, get_short_term_emotion, get_turnover_top, get_global_indices
)
from app.services import vibe_astock as astock

router = APIRouter(prefix="/api/vibe", tags=["Vibe-Research"])
logger = logging.getLogger("webapi")


# ---------------------------------------------------------------------------
# 复盘模块
# ---------------------------------------------------------------------------

@router.get("/indices")
async def indices():
    """A股大盘指数实时行情（上证/深证成指/创业板指/沪深300）"""
    try:
        data = astock.index_quote()
        return ok(data)
    except Exception as e:
        logger.error(f"大盘指数异常: {e}")
        return ok([])


@router.get("/global-indices")
async def global_indices():
    """全球指数快照（美股/港股），分级TTL缓存"""
    try:
        data = await get_global_indices()
        return ok(data)
    except Exception as e:
        logger.error(f"全球指数异常: {e}")
        return ok([])


@router.get("/market/overview")
async def market_overview():
    """市场情绪 + 板块资金流（Redis分级TTL缓存）"""
    try:
        data = await get_overview()
        return ok(data)
    except Exception as e:
        logger.error(f"市场总览异常: {e}")
        return ok({"sentiment": {}, "sectors": [], "updated": ""})


@router.get("/market/emotion")
async def market_emotion():
    """短线情绪（连板梯队/封板率/炸板率/晋级率），分级TTL缓存"""
    try:
        data = await get_short_term_emotion()
        return ok(data)
    except Exception as e:
        logger.error(f"短线情绪异常: {e}")
        return ok({})


@router.get("/market/turnover-top")
async def market_turnover_top():
    """全市场成交额Top20，分级TTL缓存"""
    try:
        data = await get_turnover_top()
        return ok(data)
    except Exception as e:
        logger.error(f"成交额榜异常: {e}")
        return ok({"stocks": [], "updated": ""})


@router.get("/quotes")
async def quotes(codes: str):
    """批量个股实时行情（逗号分隔代码）"""
    try:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        if not code_list:
            return ok([])
        data = astock.tencent_quote(code_list)
        # 转为前端友好的数组格式
        out = []
        for code, q in data.items():
            item = {
                "code": code,
                "name": q.get("name", ""),
                "is_st": q.get("is_st", False),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "change_amt": q.get("change_amt"),
                "pe_ttm": q.get("pe_ttm"),
                "pb": q.get("pb"),
                "mcap_yi": q.get("mcap_yi"),
                "float_mcap_yi": q.get("float_mcap_yi"),
                "amount_wan": q.get("amount_wan"),
                "turnover_pct": q.get("turnover_pct"),
            }
            # 将数据校验结果返回给前端
            validation = q.get("_validation")
            if validation:
                item["_validation"] = validation
            # ST股票强制风险提示
            if q.get("is_st"):
                if not validation:
                    item["_validation"] = {"passed": True, "errors": [], "warnings": []}
                item["_validation"]["warnings"].append("⚠️ ST股票：存在退市风险，投资需谨慎")
            out.append(item)
        return ok(out)
    except Exception as e:
        logger.error(f"批量行情异常: {e}")
        return ok([])


# ---------------------------------------------------------------------------
# 资讯模块
# ---------------------------------------------------------------------------

@router.get("/radar")
async def radar():
    """资讯雷达：12赛道公开RSS资讯（Redis分级缓存）"""
    try:
        data = await get_radar_cached(force=False)
        return ok(data)
    except Exception as e:
        logger.error(f"资讯雷达异常: {e}")
        raise HTTPException(500, f"资讯雷达异常: {e}")


@router.post("/radar/refresh")
async def radar_refresh():
    """强制刷新资讯雷达（抓取全部RSS源）"""
    try:
        data = fetch_radar()
        return ok(data)
    except Exception as e:
        logger.error(f"资讯雷达刷新异常: {e}")
        raise HTTPException(500, f"资讯雷达刷新异常: {e}")


@router.get("/announcements")
async def announcements(code: str, limit: int = 15):
    """个股近期公告（东财公开接口）"""
    try:
        data = astock.announcements(code, limit)
        return ok(data)
    except Exception as e:
        logger.error(f"个股公告异常: {e}")
        return ok([])


@router.get("/announcements/batch")
async def announcements_batch(codes: str, limit: int = 10):
    """批量获取多只股票公告（逗号分隔代码）"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return ok([])
    
    results = []
    for code in code_list[:20]:
        try:
            anns = astock.announcements(code, limit)
            for item in anns:
                item["stock_code"] = code
                results.append(item)
        except Exception as e:
            logger.warning(f"获取股票 {code} 公告失败: {e}")
    
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return ok(results[:limit * 3])


@router.get("/news")
async def stock_news(code: str, limit: int = 20, since: str = ""):
    """个股新闻（东财），支持 since 参数增量更新"""
    try:
        data = astock.stock_news(code, limit)
        if since:
            data = [item for item in data if item.get("发布时间", "") > since]
        return ok(data)
    except Exception as e:
        logger.error(f"个股新闻异常: {e}")
        return ok([])


@router.get("/news/batch")
async def news_batch(codes: str, limit: int = 10, since: str = ""):
    """批量获取多只股票新闻（逗号分隔代码），自动去重，支持 since 增量更新"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return ok([])

    # 使用标题去重，同一新闻关联多只股票时合并股票代码
    seen = {}
    for code in code_list[:20]:
        try:
            news = astock.stock_news(code, limit)
            for item in news:
                # since 过滤：只保留发布时间 > since 的新闻
                if since and item.get("发布时间", "") <= since:
                    continue
                title = item.get("新闻标题", "").strip()
                if not title:
                    continue
                if title not in seen:
                    item["stock_codes"] = [code]
                    seen[title] = item
                else:
                    if code not in seen[title]["stock_codes"]:
                        seen[title]["stock_codes"].append(code)
                    # 保留更早的发布时间
                    if item.get("发布时间", "") < seen[title].get("发布时间", ""):
                        seen[title]["发布时间"] = item["发布时间"]
        except Exception as e:
            logger.warning(f"获取股票 {code} 新闻失败: {e}")

    results = list(seen.values())
    results.sort(key=lambda x: x.get("发布时间", ""), reverse=True)
    return ok(results[:limit * 3])


# ---------------------------------------------------------------------------
# 板块模块
# ---------------------------------------------------------------------------

@router.get("/sectors")
async def sectors():
    """板块中心：热门赛道产业链骨架（静态数据）"""
    sectors_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sectors.json")
    try:
        with open(sectors_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ok(data)
    except Exception as e:
        logger.error(f"板块数据读取异常: {e}")
        raise HTTPException(500, f"板块数据读取异常: {e}")


# ---------------------------------------------------------------------------
# AI 对话模块（复用系统已配置的 LLM）
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: str = ""


def _get_llm_config():
    """从系统配置中获取第一个可用的 LLM 配置（有 API Key 的）"""
    try:
        from app.core.unified_config import unified_config
        from app.services.config_service import ConfigService
        cs = ConfigService()

        llm_configs = unified_config.get_llm_configs()
        quick_model = unified_config.get_quick_analysis_model()

        # 默认 api_base 映射
        default_base = {
            "deepseek": "https://api.deepseek.com",
            "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai": "https://api.openai.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }

        # 优先找快速分析模型
        for cfg in llm_configs:
            if cfg.model_name == quick_model and cfg.enabled:
                api_key = cs._get_env_api_key(cfg.provider)
                if api_key:
                    return {
                        "model": cfg.model_name,
                        "api_base": cfg.api_base or default_base.get(cfg.provider, ""),
                        "api_key": api_key,
                        "temperature": cfg.temperature,
                        "max_tokens": cfg.max_tokens,
                    }

        # 回退：找第一个有 API Key 的启用配置
        for cfg in llm_configs:
            if cfg.enabled:
                api_key = cs._get_env_api_key(cfg.provider)
                if api_key:
                    return {
                        "model": cfg.model_name,
                        "api_base": cfg.api_base or default_base.get(cfg.provider, ""),
                        "api_key": api_key,
                        "temperature": cfg.temperature,
                        "max_tokens": cfg.max_tokens,
                    }

        return None
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        return None


SYSTEM_PROMPT = (
    "你是一个专业的A股投研助理。你可以基于用户提供的客观数据进行分析和总结。\n"
    "硬性规则：\n"
    "- 只做信息整理、数据解读与多视角分析\n"
    "- 不推荐任何具体买卖、不预测涨跌与价位、不给买卖时机、不承诺收益\n"
    "- 需要基于用户提供的客观数据回答，不要编造数字\n"
    "- 回答使用中文，简洁专业\n"
)


@router.post("/chat")
async def chat(req: ChatRequest):
    """AI 对话（流式 NDJSON）。复用系统已配置的 LLM。"""
    cfg = _get_llm_config()
    if not cfg or not cfg.get("api_key"):
        def err_gen():
            yield json.dumps({"type": "error", "message": "系统尚未配置 AI 模型或 API Key，请先在设置中配置。"}, ensure_ascii=False) + "\n"
        return StreamingResponse(err_gen(), media_type="application/x-ndjson")

    import requests

    messages = [{"role": "system", "content": SYSTEM_PROMPT + (f"\n当前页面上下文：\n{req.context}" if req.context else "")}]
    messages.extend({"role": m.role, "content": m.content} for m in req.messages)

    api_base = cfg["api_base"].rstrip("/")
    if not api_base.endswith("/chat/completions"):
        api_base = api_base + "/chat/completions"

    def gen():
        try:
            resp = requests.post(
                api_base,
                json={
                    "model": cfg["model"],
                    "messages": messages,
                    "temperature": cfg.get("temperature", 0.7),
                    "max_tokens": cfg.get("max_tokens", 4000),
                    "stream": True,
                },
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                stream=True,
                timeout=120,
            )
            if resp.status_code != 200:
                err_msg = resp.text[:500]
                yield json.dumps({"type": "error", "message": f"AI 服务返回错误 ({resp.status_code}): {err_msg}"}, ensure_ascii=False) + "\n"
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                chunk = line[6:]
                if chunk.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(chunk)
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content", "")
                    if text:
                        yield json.dumps({"type": "delta", "text": text}, ensure_ascii=False) + "\n"
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue

            yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
        except requests.exceptions.Timeout:
            yield json.dumps({"type": "error", "message": "AI 响应超时，请稍后重试。"}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "message": f"对话失败：{e}"}, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")
