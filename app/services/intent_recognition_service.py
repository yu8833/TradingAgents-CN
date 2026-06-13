"""
意图识别服务 - 自然语言交易意图解析
"""
import re
import logging
from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class IntentResult(BaseModel):
    """意图解析结果"""
    stock_symbol: Optional[str] = None  # 解析出的股票代码
    stock_name: Optional[str] = None  # 解析出的股票名称
    intent_type: str = "unknown"  # "analyze" / "portfolio" / "screening" / "unknown"
    period: Optional[str] = None  # "short" / "medium" / "long" / None
    confidence: float = 0.0  # 置信度 0-1
    raw_input: str = ""  # 原始输入
    suggestions: List[str] = []  # 可能的候选（多股票时）


class IntentRecognitionService:
    """
    自然语言意图识别服务
    支持股票代码、名称解析、投资周期识别、意图类型识别
    """

    # 短线关键词
    SHORT_TERM_KEYWORDS = [
        "今天", "明日", "本周", "这周", "短期", "短线",
        "快买快卖", "打板", "追板", "涨停", "日内",
        "当天", "今日", "这几天的", "这几天"
    ]

    # 中线关键词
    MEDIUM_TERM_KEYWORDS = [
        "中期", "一周", "一个月", "波段", "中线",
        "一两周", "两三周", "持有一月", "持有几周",
        "中期持有", "这段时间"
    ]

    # 长线关键词
    LONG_TERM_KEYWORDS = [
        "长期", "长线", "价值投资", "持有一年", "长期持有",
        "价值", "长期持有", "几年", "好多年", "养老"
    ]

    # 分析意图关键词
    ANALYZE_KEYWORDS = [
        "分析", "调研", "看看", "怎么样", "好吗", "如何",
        "好不好", "能买吗", "可以买吗", "走势", "行情",
        "研判", "评价", "解读", "研究", "评估"
    ]

    # 持仓意图关键词
    PORTFOLIO_KEYWORDS = [
        "持仓", "我的股票", "亏了多少", "赚了多少",
        "盈亏", "我的持仓", "账户", "亏钱", "赚钱",
        "还持有", "还拿着", "现在持有什么"
    ]

    # 选股意图关键词
    SCREENING_KEYWORDS = [
        "选股", "筛选", "哪些股票", "找股票", "推荐股票",
        "买什么", "什么股票好", "值得买", "优质的"
    ]

    # 常见股票简称映射
    STOCK_ALIASES: Dict[str, str] = {
        "招行": "600036.SH",
        "茅台": "600519.SH",
        "平安": "601318.SH",
        "万科": "000002.SZ",
        "格力": "000651.SZ",
        "美的": "000333.SZ",
        "中石油": "601857.SH",
        "中石化": "600028.SH",
        "工行": "601398.SH",
        "建行": "601939.SH",
        "农行": "601288.SH",
        "中行": "601988.SH",
        "交行": "601328.SH",
        "兴业": "601166.SH",
        "浦发": "600000.SH",
        "民生": "600016.SH",
        "华夏": "600015.SH",
        "平安银行": "000001.SZ",
        "宁波银行": "002142.SZ",
        "泸州老窖": "000568.SZ",
        "五粮液": "000858.SZ",
        "伊利": "600887.SH",
        "海天": "603288.SH",
        "恒瑞": "600276.SH",
        "长春高新": "000661.SZ",
        "比亚迪": "002594.SZ",
        "宁德时代": "300750.SZ",
        "隆基": "601012.SH",
        "通威": "600438.SH",
        "三一": "600031.SH",
        "中联重科": "000157.SZ",
        "中车": "601766.SH",
        "中国中铁": "601390.SH",
        "中国铁建": "601186.SH",
        "建筑": "601668.SH",
        "中建": "601668.SH",
        "铁建": "601186.SH",
        "中铁": "601390.SH",
    }

    def __init__(self):
        """初始化意图识别服务"""
        self._stock_name_to_code: Dict[str, str] = {}
        self._stock_code_to_name: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """
        初始化股票名称数据库
        使用akshare获取A股股票列表
        """
        if self._initialized:
            return

        try:
            import akshare as ak
            logger.info("正在从akshare获取股票列表...")

            # 获取A股股票代码和名称
            df = ak.stock_info_a_code_name()

            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    'code': 'symbol',
                    '代码': 'symbol',
                    'name': 'name',
                    '名称': 'name'
                })

                # 建立名称->代码映射
                for _, row in df.iterrows():
                    symbol = str(row['symbol']).zfill(6)
                    name = str(row['name']).strip()

                    if name and symbol:
                        # 全名映射
                        self._stock_name_to_code[name] = symbol
                        # 简称映射（取前2-4个字）
                        if len(name) >= 2:
                            short_names = [name[:2], name[:3], name]
                            for sn in short_names:
                                if sn != name:  # 避免覆盖全名
                                    if sn not in self._stock_name_to_code or len(sn) > len(self._stock_name_to_code.get(sn, "")):
                                        self._stock_name_to_code[sn] = symbol
                        self._stock_code_to_name[symbol] = name

                # 添加常见简称
                self._stock_name_to_code.update(self.STOCK_ALIASES)

                logger.info(f"股票名称数据库初始化完成，共加载 {len(self._stock_code_to_name)} 只股票")
                self._initialized = True
            else:
                logger.warning("akshare返回空数据，使用内置简称映射")
                self._stock_name_to_code.update(self.STOCK_ALIASES)
                self._initialized = True

        except Exception as e:
            logger.error(f"初始化股票名称数据库失败: {e}，使用内置简称映射")
            self._stock_name_to_code.update(self.STOCK_ALIASES)
            self._initialized = True

    def _extract_stock_code(self, text: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        从文本中提取股票代码（支持嵌入在句子中的代码）
        Returns:
            (stock_symbol, stock_name, suggestions)
        """
        # 1. 精确匹配带后缀的代码，如 600519.SH, 000001.SZ
        suffix_pattern = r"(\d{6})\.(SH|SZ|BJ)"
        match = re.search(suffix_pattern, text)
        if match:
            code = match.group(1).zfill(6)
            suffix = match.group(2)
            return f"{code}.{suffix}", self._stock_code_to_name.get(f"{code}.{suffix}", None), []

        # 2. 提取6位数字代码（嵌入在文本中的）
        embedded_code_pattern = r"(?<!\d)(\d{6})(?!\d)"
        match = re.search(embedded_code_pattern, text)
        if match:
            code = match.group(1).zfill(6)
            # 根据代码前缀判断市场
            if code.startswith(('60', '68', '90')):
                suffix = "SH"
            elif code.startswith(('00', '30', '20')):
                suffix = "SZ"
            elif code.startswith(('8', '4')):
                suffix = "BJ"
            else:
                suffix = "SZ"  # 默认深圳
            full_code = f"{code}.{suffix}"
            return full_code, self._stock_code_to_name.get(full_code, None), []

        return None, None, []

    def _parse_stock_code(self, text: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        解析股票代码或名称
        Returns:
            (stock_symbol, stock_name, suggestions)
        """
        text = text.strip()
        suggestions = []

        # 0. 尝试从文本中提取嵌入的股票代码
        code, name, sugg = self._extract_stock_code(text)
        if code:
            return code, name, sugg

        # 1. 精确匹配带后缀的代码，如 600519.SH, 000001.SZ
        suffix_pattern = r"^(\d{6})\.(SH|SZ|BJ)$"
        match = re.match(suffix_pattern, text)
        if match:
            code = match.group(1).zfill(6)
            suffix = match.group(2)
            return f"{code}.{suffix}", self._stock_code_to_name.get(f"{code}.{suffix}", None), []

        # 2. 纯6位数字代码
        if re.match(r"^\d{6}$", text):
            code = text.zfill(6)
            # 根据代码前缀判断市场
            if code.startswith(('60', '68', '90')):
                suffix = "SH"
            elif code.startswith(('00', '30', '20')):
                suffix = "SZ"
            elif code.startswith(('8', '4')):
                suffix = "BJ"
            else:
                suffix = "SZ"  # 默认深圳
            full_code = f"{code}.{suffix}"
            return full_code, self._stock_code_to_name.get(full_code, None), []

        # 3. 中文名称/简称匹配
        # 精确匹配
        if text in self._stock_name_to_code:
            code = self._stock_name_to_code[text]
            return code, self._stock_code_to_name.get(code, text), []

        # 模糊匹配 - 包含关系
        fuzzy_matches = []
        for name_key, code in self._stock_name_to_code.items():
            if name_key in text:
                fuzzy_matches.append((name_key, code, len(name_key)))

        if fuzzy_matches:
            # 按名称长度降序排列，优先返回完整匹配
            fuzzy_matches.sort(key=lambda x: -x[2])
            best_match = fuzzy_matches[0]
            suggestions = [f"{m[1]} ({m[0]})" for m in fuzzy_matches[:5]]
            return best_match[1], best_match[0], suggestions

        return None, None, []

    def _recognize_period(self, text: str) -> Tuple[Optional[str], float]:
        """
        识别投资周期
        Returns:
            (period, confidence)
        """
        text = text.lower()

        # 短线匹配
        for keyword in self.SHORT_TERM_KEYWORDS:
            if keyword in text:
                return "short", 0.9

        # 中线匹配
        for keyword in self.MEDIUM_TERM_KEYWORDS:
            if keyword in text:
                return "medium", 0.9

        # 长线匹配
        for keyword in self.LONG_TERM_KEYWORDS:
            if keyword in text:
                return "long", 0.9

        return None, 0.0

    def _recognize_intent_type(self, text: str) -> Tuple[str, float]:
        """
        识别意图类型
        Returns:
            (intent_type, confidence)
        """
        text_lower = text.lower()
        scores = {
            "analyze": 0.0,
            "portfolio": 0.0,
            "screening": 0.0
        }

        # 分析意图
        for keyword in self.ANALYZE_KEYWORDS:
            if keyword in text_lower:
                scores["analyze"] += 0.3
                if "吗" in text or "?" in text:
                    scores["analyze"] += 0.2

        # 持仓意图
        for keyword in self.PORTFOLIO_KEYWORDS:
            if keyword in text_lower:
                scores["portfolio"] += 0.4

        # 选股意图
        for keyword in self.SCREENING_KEYWORDS:
            if keyword in text_lower:
                scores["screening"] += 0.4

        # 归一化置信度
        max_score = max(scores.values())
        if max_score > 0:
            max_score = min(max_score, 1.0)

        # 返回最高分的意图类型
        best_intent = max(scores, key=scores.get)
        return best_intent if scores[best_intent] > 0 else "unknown", max_score

    def parse_intent(self, user_input: str) -> IntentResult:
        """
        解析用户输入的交易意图

        Args:
            user_input: 用户输入的自然语言

        Returns:
            IntentResult: 意图解析结果
        """
        if not user_input or not user_input.strip():
            return IntentResult(
                raw_input=user_input,
                confidence=0.0
            )

        original_input = user_input
        user_input = user_input.strip()

        # 解析股票代码
        stock_symbol, stock_name, suggestions = self._parse_stock_code(user_input)

        # 识别周期
        period, period_conf = self._recognize_period(user_input)

        # 识别意图类型
        intent_type, intent_conf = self._recognize_intent_type(user_input)

        # 综合置信度
        confidence = max(period_conf * 0.2, intent_conf * 0.5)
        if stock_symbol:
            confidence = max(confidence, 0.7)
        if suggestions:
            confidence = min(confidence, 0.6)

        return IntentResult(
            stock_symbol=stock_symbol,
            stock_name=stock_name,
            intent_type=intent_type,
            period=period,
            confidence=round(confidence, 2),
            raw_input=original_input,
            suggestions=suggestions
        )


# 全局单例
_intent_service: Optional[IntentRecognitionService] = None


async def get_intent_recognition_service() -> IntentRecognitionService:
    """获取意图识别服务实例（单例）"""
    global _intent_service
    if _intent_service is None:
        _intent_service = IntentRecognitionService()
        await _intent_service.initialize()
    return _intent_service


def parse_intent(user_input: str) -> IntentResult:
    """
    解析用户输入的交易意图（便捷函数）

    Args:
        user_input: 用户输入的自然语言

    Returns:
        IntentResult: 意图解析结果
    """
    service = IntentRecognitionService()
    service._stock_name_to_code = service.STOCK_ALIASES.copy()
    service._initialized = True
    return service.parse_intent(user_input)
