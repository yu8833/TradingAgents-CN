# TradingAgents/graph/signal_processing.py
# 🔥 2026-06-12 重大修复：多维度价格提取
#    之前问题：target_price 会错误匹配止损位/下跌目标位，导致目标价低于当前价
#    解决方案：区分 target_price（与决策方向一致的核心目标价）、stop_loss_price（止损位）、
#              entry_price（入场/出场建议价）、price_target_optimistic/pessimistic（情景目标）

from langchain_openai import ChatOpenAI

# 导入统一日志系统和图处理模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_graph_module
logger = get_logger("graph.signal_processing")


class SignalProcessor:
    """Processes trading signals to extract actionable decisions.

    🔥 多维度价格语义：
    - target_price: 与决策方向一致的核心目标价
      * 买入/超配: 预期上涨目标价
      * 持有: 合理估值中枢
      * 卖出/低配: 下跌目标价（股价可能到达的位置，会低于当前价，这是正常的）
    - stop_loss_price: 止损位（强制离场价格，通常低于当前价，不应被当作 target_price）
    - entry_price: 建议入场/出场价格
    - price_target_optimistic: 乐观情景目标价
    - price_target_pessimistic: 悲观情景目标价
    """

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    @log_graph_module("signal_processing")
    def process_signal(self, full_signal: str, stock_symbol: str = None) -> dict:
        """
        Process a full trading signal to extract structured decision information.

        Args:
            full_signal: Complete trading signal text
            stock_symbol: Stock symbol to determine currency type

        Returns:
            Dictionary containing extracted decision information
        """

        # 验证输入参数
        if not full_signal or not isinstance(full_signal, str) or len(full_signal.strip()) == 0:
            logger.error(f"❌ [SignalProcessor] 输入信号为空或无效")
            return self._build_decision_dict('持有', None, 0.5, 0.5, '输入信号无效，默认持有建议')

        # 清理和验证信号内容
        signal_text = full_signal.strip()
        if len(signal_text) == 0:
            logger.error(f"❌ [SignalProcessor] 信号内容为空")
            return self._build_decision_dict('持有', None, 0.5, 0.5, '信号内容为空，默认持有建议')

        # 检测股票类型和货币
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(stock_symbol)
        is_china = market_info['is_china']
        currency = market_info['currency_name']
        currency_symbol = market_info['currency_symbol']

        logger.info(f"🔍 [SignalProcessor] 股票={stock_symbol}, 市场={market_info['market_name']}, 货币={currency}")

        # =========================================================================
        # 🔥 第一步：语义化提取所有价格类型（LLM辅助，带明确的prompt约束）
        # =========================================================================
        messages = [
            (
                "system",
                f"""您是一位专业的金融分析助手，负责从交易员的分析报告中提取结构化的投资决策信息。

⚠️ 关键约束：必须严格区分以下价格类型，不得混淆

请从提供的分析报告中提取以下信息，并以JSON格式返回：
{{
    "action": "买入/持有/卖出",
    "target_price": 数字({currency}核心目标价) **或null**,
    "stop_loss_price": 数字({currency}止损位价格) **或null**,
    "entry_price": 数字({currency}建议入场/出场价格) **或null**,
    "price_target_optimistic": 数字({currency}乐观情景目标价) **或null**,
    "price_target_pessimistic": 数字({currency}悲观情景目标价) **或null**,
    "confidence": 数字(0-1之间,默认0.7),
    "risk_score": 数字(0-1之间,默认0.5),
    "reasoning": "决策的主要理由摘要"
}}

🔥 🔥 🔥 目标价(target_price)提取规则（极其重要）：

**如果报告中明确提到了目标价格**，根据action类型提取：
1. action="买入"或"超配/overweight"：target_price = 上涨目标价/第一目标位（应高于当前价）
   查找关键词："第一目标"、"目标价"、"预期"、"上涨至"、"看到"、"反弹目标"
2. action="持有"或"hold"：target_price = 合理估值中枢或持有区间的上限
   查找关键词："合理估值"、"估值中枢"、"持有区间"（取区间上限）、明确"目标价"
3. action="卖出"或"低配/underweight"：target_price = 下跌目标价/悲观目标（可低于当前价）

**如果报告中没有明确提到目标价格**，target_price 必须返回 null：
⚠️ 禁止捏造、估算或假设任何数字！当报告中没有明确写出"目标价X元"时，必须返回 null。

**价格与目标价的区分（极其重要）**：
- "持有区间：22.00-24.50" → target_price = 24.50（区间上限）
- "止损位：22.10" → 放在 stop_loss_price，不是 target_price
- "支撑位：22.00" → 放在 price_target_pessimistic 或 stop_loss_price
- "若跌破22.10则离场" → stop_loss_price = 22.10

**绝对禁止**：
- 绝对禁止凭空捏造"15.0"、"20.0"等没有在报告中出现的数字
- 绝对禁止将"止损位"数字填入 target_price
- 绝对禁止将"支撑位"数字在"买入"时填入 target_price

**返回格式**：
- 有明确价格 → 数字，如 24.50
- 没有明确价格 → null（不是0，不是估算值）

股票代码 {stock_symbol or '未知'} 是{market_info['market_name']}，使用{currency}计价。
所有价格在报告中没有明确提及时必须留空（null），禁止捏造。""",
            ),
            ("human", signal_text),
        ]

        try:
            response = self.quick_thinking_llm.invoke(messages).content
            logger.debug(f"🔍 [SignalProcessor] LLM原始响应: {str(response)[:300]}...")

            # 尝试解析JSON响应
            import json
            import re

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                decision_data = json.loads(json_text)

                # 验证和标准化 action
                action = self._normalize_action(decision_data.get('action', '持有'))

                # 提取并验证各价格字段
                prices = self._extract_and_validate_prices(
                    decision_data, signal_text, action
                )

                # 提取置信度和风险评分
                confidence = float(decision_data.get('confidence', 0.7))
                risk_score = float(decision_data.get('risk_score', 0.5))

                # 推理摘要
                reasoning = decision_data.get('reasoning', '基于综合分析的投资建议')

                # 构建最终结果
                result = self._build_decision_dict(
                    action, prices.get('target_price'), confidence, risk_score, reasoning,
                    stop_loss_price=prices.get('stop_loss_price'),
                    entry_price=prices.get('entry_price'),
                    price_target_optimistic=prices.get('price_target_optimistic'),
                    price_target_pessimistic=prices.get('price_target_pessimistic'),
                )

                # =========================================================================
                # 🔥 后验验证：防止LLM捏造价格
                # 如果 target_price 不在原始文本中出现，则设为 null
                # =========================================================================
                result = self._validate_price_in_text(result, signal_text)

                logger.info(
                    f"✅ [SignalProcessor] 处理结果: action={result['action']}, "
                    f"target_price={result['target_price']}, stop_loss={result.get('stop_loss_price')}, "
                    f"confidence={result['confidence']:.2f}",
                    extra={'stock_symbol': stock_symbol, **{k: v for k, v in result.items()}}
                )
                return result
            else:
                # 回退到简单文本提取
                logger.warning(f"⚠️ [SignalProcessor] 无法解析JSON，回退到简单提取")
                return self._extract_semantic_decision(signal_text, stock_symbol)

        except Exception as e:
            logger.error(f"❌ [SignalProcessor] 信号处理错误: {e}", exc_info=True,
                         extra={'stock_symbol': stock_symbol})
            # 回退到简单提取
            return self._extract_semantic_decision(signal_text, stock_symbol)

    # =========================================================================
    # 辅助方法：标准化 action
    # =========================================================================
    def _normalize_action(self, action_str: str) -> str:
        """将各种action表述标准化为 买入/持有/卖出"""
        if not action_str:
            return '持有'

        action_str = str(action_str).strip().lower()

        action_map = {
            'buy': '买入', '买入': '买入', '购买': '买入', 'purchase': '买入',
            'b': '买入', 'overweight': '买入', '超配': '买入', '增持': '买入',
            'hold': '持有', '持有': '持有', '保持': '持有', '中性': '持有',
            'h': '持有', '观望': '持有',
            'sell': '卖出', '卖出': '卖出', '出售': '卖出', 'dispose': '卖出',
            's': '卖出', 'underweight': '卖出', '低配': '卖出', '减仓': '卖出',
        }

        if action_str in action_map:
            return action_map[action_str]

        # 模糊匹配
        for key in action_map:
            if key in action_str:
                return action_map[key]

        return '持有'

    # =========================================================================
    # 辅助方法：提取和验证价格字段
    # =========================================================================
    def _extract_and_validate_prices(self, decision_data: dict, signal_text: str, action: str) -> dict:
        """从LLM响应和原始文本中提取多种价格类型，带语义验证"""
        import re

        prices = {}

        # 第一步：尝试从JSON中提取各价格
        for field_name in ['target_price', 'stop_loss_price', 'entry_price',
                           'price_target_optimistic', 'price_target_pessimistic']:
            val = decision_data.get(field_name)
            if self._is_valid_price(val):
                prices[field_name] = float(val)
                logger.debug(f"🔍 [SignalProcessor] JSON提取 {field_name}: {val}")

        # 第二步：如果target_price缺失，用规则从文本中提取（带语义区分）
        if 'target_price' not in prices or prices.get('target_price') is None:
            extracted_target = self._extract_price_by_semantics(signal_text, action, 'target')
            if extracted_target:
                prices['target_price'] = extracted_target
                logger.info(f"🔍 [SignalProcessor] 文本提取 target_price: {extracted_target} (action={action})")

        # 第三步：如果stop_loss_price缺失，从文本中提取止损位
        if 'stop_loss_price' not in prices:
            extracted_stop = self._extract_price_by_semantics(signal_text, action, 'stop_loss')
            if extracted_stop:
                prices['stop_loss_price'] = extracted_stop
                logger.info(f"🔍 [SignalProcessor] 文本提取 stop_loss_price: {extracted_stop}")

        # 第四步：尝试提取乐观/悲观情景目标价
        if 'price_target_optimistic' not in prices:
            optimistic = self._extract_price_by_semantics(signal_text, action, 'optimistic')
            if optimistic:
                prices['price_target_optimistic'] = optimistic

        if 'price_target_pessimistic' not in prices:
            pessimistic = self._extract_price_by_semantics(signal_text, action, 'pessimistic')
            if pessimistic:
                prices['price_target_pessimistic'] = pessimistic

        # 第五步：验证 target_price 语义合理性（防止将止损位误识别为目标价）
        if ('target_price' in prices and 'stop_loss_price' in prices
                and prices['target_price'] is not None and prices['stop_loss_price'] is not None):
            # 如果target_price等于stop_loss_price，说明LLM把止损位当成了目标价
            if abs(prices['target_price'] - prices['stop_loss_price']) < 0.05:
                logger.warning(
                    f"⚠️ [SignalProcessor] target_price({prices['target_price']}) ≈ stop_loss_price({prices['stop_loss_price']})，"
                    f"可能是止损位被误识别为目标价。尝试重新提取..."
                )
                # 尝试从文本中找到另一个更高的数字作为目标价
                alternative = self._extract_price_by_semantics(signal_text, action, 'target_force')
                if alternative and alternative != prices['stop_loss_price']:
                    # 如果找到了不同的价格，而且这个价格更符合action方向，则替换
                    if action == '买入' and alternative > prices['stop_loss_price']:
                        prices['target_price'] = alternative
                        logger.info(f"✅ [SignalProcessor] 修正 target_price: {alternative} (原止损位 {prices['stop_loss_price']})")
                    elif action == '卖出' and alternative < prices['target_price']:
                        # 卖出的话target_price应该更低（下跌目标），如果找到比当前推测更低的，可能才是真正的目标
                        pass

        # 第六步：如果仍然没有target_price，尝试智能推算
        if 'target_price' not in prices or prices.get('target_price') is None:
            estimated = self._smart_price_estimation(signal_text, action, True)
            if estimated:
                prices['target_price'] = estimated
                logger.info(f"🔍 [SignalProcessor] 智能推算 target_price: {estimated}")

        return prices

    # =========================================================================
    # 辅助方法：按语义提取价格（区分目标价、止损位、乐观目标、悲观目标）
    # =========================================================================
    def _extract_price_by_semantics(self, text: str, action: str, price_type: str) -> float:
        """
        基于语义从文本中提取特定类型的价格

        🔥 核心逻辑：
        1. 根据 action（买入/持有/卖出）选择优先级不同的匹配模式
        2. 对每个匹配结果，检查其上下文是否有排除关键词（如"买入"场景排除"下跌/悲观/支撑"等）
        3. 返回第一个通过筛选的价格

        Args:
            text: 分析报告文本
            action: 决策类型（买入/持有/卖出），用于指导价格方向判断
            price_type: 'target' | 'stop_loss' | 'entry' | 'optimistic' | 'pessimistic' | 'target_force'

        Returns:
            提取到的价格，找不到返回None
        """
        import re

        # 价格数字通用模式
        price_num_pattern = r'(\d+(?:\.\d+)?)'

        # 🔥 定义各场景下的排除关键词
        # 注意：只排除**紧邻匹配位置**出现的强方向词，范围缩小到前后各20字符
        # 避免因为报告前面出现"支撑"一词导致后面"目标价"被错误过滤
        downward_keywords_strong = ['下跌目标', '悲观目标', '个月目标', '目标位下跌', '目标价格下跌']
        upward_keywords_strong = ['第一目标', '目标价', '上涨目标', '上看', '反弹', '建仓', '买入']

        patterns = []

        if price_type in ['target', 'target_force']:
            if action == '买入':
                # 🔥 买入：只匹配上涨方向的目标
                # 优先级1：明确的目标价关键词（报告中最显著的位置）
                # 优先级2：明确上涨关键词
                # 🔥 注意：不匹配"乐观"（那是 optimistic_target 的事）
                patterns = [
                    # 优先级1：明确的"目标价"关键词
                    (r'目标价位?[^0-9]{0,20}[¥\$元]?\s*' + price_num_pattern, downward_keywords_strong),
                    (r'目标[^0-9]{0,10}[：:]?\s*[¥\$元]?\s*' + price_num_pattern, downward_keywords_strong),
                    # 优先级2：明确上涨关键词的目标
                    (r'第一目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'上涨目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'上涨至[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'上看[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'反弹目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    # 优先级3：阻力位/上轨（也表示上涨目标）
                    (r'阻力位[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'布林带上轨[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                ]
            elif action == '持有':
                # 🔥 持有：优先找合理估值/中枢价格/明确目标价
                patterns = [
                    # 优先级1：目标价关键词（排除明确下跌方向）
                    (r'目标价位?[^0-9]{0,20}[¥\$元]?\s*' + price_num_pattern, downward_keywords_strong),
                    (r'目标[^0-9]{0,10}[：:]?\s*[¥\$元]?\s*' + price_num_pattern, downward_keywords_strong),
                    # 优先级2：估值相关
                    (r'合理估值[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'估值中枢[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'合理价位[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'价值区间[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    # 优先级3：预期价格
                    (r'预期[^0-9]*[¥\$元]?\s*' + price_num_pattern, downward_keywords_strong),
                ]
            else:  # 卖出
                # 🔥 卖出：只匹配下跌方向的目标
                patterns = [
                    # 优先级1：明确的下跌目标关键词
                    (r'下跌目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'悲观[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'个月目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'最坏[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'最低[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    # 优先级2：支撑位/下轨（表示下跌目标），排除紧邻含上涨关键词的
                    (r'支撑位[^0-9]*[¥\$元]?\s*' + price_num_pattern, upward_keywords_strong),
                    (r'布林带下轨[^0-9]*[¥\$元]?\s*' + price_num_pattern, upward_keywords_strong),
                    # 优先级3：目标价关键词（排除明确上涨方向）
                    (r'目标价位?[^0-9]*[¥\$元]?\s*' + price_num_pattern, upward_keywords_strong),
                ]

            # target_force模式：强制匹配（用于当LLM错误时的修正逻辑）
            if price_type == 'target_force':
                patterns = [
                    (r'目标价位?[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'第一目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'第二目标[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                    (r'看到[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                ]

        elif price_type == 'stop_loss':
            # 止损位：找止损/红线/跌破等关键词
            patterns = [
                (r'止损(?:位|线|点|价格)?[^0-9]{0,15}[¥\$元]?\s*' + price_num_pattern, None),
                (r'止损[^0-9]*设(?:在|定)?[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'跌破[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'跌破[^0-9]*[¥\$元]?(\d+(?:\.\d+)?)', None),
                (r'强制[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'红线[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'止盈(?:位|线|点)?[^0-9]{0,15}[¥\$元]?\s*' + price_num_pattern, None),
                (r'离场[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
            ]

        elif price_type == 'entry':
            # 入场/出场：找建议入场/主要战区/建仓价格
            patterns = [
                (r'入场[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'建仓[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'主要战区[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'建议[^0-9]*入场[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'区间[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
            ]

        elif price_type == 'optimistic':
            # 乐观情景：找乐观/最高/最好情况
            patterns = [
                (r'乐观[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'最好[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'最高[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
            ]

        elif price_type == 'pessimistic':
            # 悲观情景：找悲观/最低/最坏情况
            patterns = [
                (r'悲观[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'最坏[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
                (r'最低[^0-9]*[¥\$元]?\s*' + price_num_pattern, None),
            ]

        # 🔥 执行匹配：找到所有候选，逐个过滤
        CONTEXT_WINDOW = 20  # 前后各20字符（缩小范围，避免误杀）

        for pattern_info in patterns:
            # 支持 (pattern, exclude_keywords) 元组形式，或纯 pattern 形式
            if isinstance(pattern_info, tuple):
                pattern, exclude_keywords = pattern_info
            else:
                pattern, exclude_keywords = pattern_info, None

            # 找到所有匹配（不只是第一个）
            try:
                matches = list(re.finditer(pattern, text))
            except Exception:
                continue

            for match in matches:
                try:
                    price = float(match.group(1))
                    if price <= 0:
                        continue

                    # 🔥 排除关键词过滤：只检查匹配位置紧邻的上下文
                    if exclude_keywords:
                        start = max(0, match.start() - CONTEXT_WINDOW)
                        end = min(len(text), match.end() + CONTEXT_WINDOW)
                        context = text[start:end].lower()

                        has_exclude = False
                        for kw in exclude_keywords:
                            if kw.lower() in context:
                                logger.debug(
                                    f"  🔍 过滤[{price_type}]: 匹配 {price} 但紧邻上下文含排除关键词 '{kw}'"
                                )
                                has_exclude = True
                                break

                        if has_exclude:
                            continue

                    logger.debug(f"  ✅ 提取[{price_type}]: {price} (pattern: {pattern[:60]})")
                    return price
                except (ValueError, IndexError, Exception):
                    continue

        return None

    # =========================================================================
    # 辅助方法：验证价格是否有效
    # =========================================================================
    def _is_valid_price(self, val) -> bool:
        """检查价格是否有效"""
        if val is None:
            return False
        if isinstance(val, (int, float)):
            return val > 0
        if isinstance(val, str):
            val = val.strip()
            if val.lower() in ['none', 'null', '']:
                return False
            try:
                return float(val.replace('¥', '').replace('$', '').replace('元', '').replace(' ', '')) > 0
            except (ValueError, TypeError):
                return False
        return False

    # =========================================================================
    # 辅助方法：构建标准化 decision dict（支持多维度价格）
    # =========================================================================
    def _build_decision_dict(self, action, target_price, confidence, risk_score, reasoning,
                           stop_loss_price=None, entry_price=None,
                           price_target_optimistic=None, price_target_pessimistic=None) -> dict:
        """构建标准化的决策字典，包含多维度价格字段"""
        decision = {
            'action': action,
            'target_price': target_price,
            'confidence': float(confidence),
            'risk_score': float(risk_score),
            'reasoning': reasoning,
            # 🔥 新增的多维度价格字段
            'stop_loss_price': stop_loss_price,
            'entry_price': entry_price,
            'price_target_optimistic': price_target_optimistic,
            'price_target_pessimistic': price_target_pessimistic,
        }

        # 清理无效的价格值（None/null），保持简洁
        cleaned = {}
        for k, v in decision.items():
            if v is None:
                cleaned[k] = None
            else:
                cleaned[k] = v

        return cleaned

    # =========================================================================
    # 辅助方法：智能推算目标价（备用方案）
    # =========================================================================
    def _smart_price_estimation(self, text: str, action: str, is_china: bool) -> float:
        """智能价格推算方法（作为最终备用方案）"""
        import re

        current_price = None
        percentage_change = None

        # 提取当前价格
        current_price_patterns = [
            r'当前价[格位]?[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',
            r'现价[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',
            r'股价[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',
            r'价格[：:]?\s*[¥\$]?(\d+(?:\.\d+)?)',
        ]

        for pattern in current_price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    current_price = float(match.group(1))
                    break
                except ValueError:
                    continue

        # 提取涨跌幅信息
        percentage_patterns = [
            r'上涨\s*(\d+(?:\.\d+)?)%',
            r'涨幅\s*(\d+(?:\.\d+)?)%',
            r'增长\s*(\d+(?:\.\d+)?)%',
            r'(\d+(?:\.\d+)?)%\s*的?上涨',
        ]

        for pattern in percentage_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    percentage_change = float(match.group(1)) / 100
                    break
                except ValueError:
                    continue

        # 基于动作和信息推算目标价
        if current_price and percentage_change:
            if action == '买入':
                return round(current_price * (1 + percentage_change), 2)
            elif action == '卖出':
                return round(current_price * (1 - percentage_change), 2)

        # 如果有当前价格但没有涨跌幅，使用默认估算
        if current_price:
            if action == '买入':
                multiplier = 1.15 if is_china else 1.12
                return round(current_price * multiplier, 2)
            elif action == '卖出':
                multiplier = 0.90 if is_china else 0.92
                return round(current_price * multiplier, 2)
            else:  # 持有
                return current_price

        return None

    # =========================================================================
    # 辅助方法：后验验证 - 防止LLM捏造价格
    # =========================================================================
    def _validate_price_in_text(self, result: dict, text: str) -> dict:
        """
        🔥 防御性验证：确保 LLM 返回的 target_price 在原始文本中确实存在
        如果 LLM 捏造了价格（如 15.0），将其设为 null 并记录警告

        验证逻辑：
        - 对于 target_price：必须在文本中找到该数字，且与"目标"/"预期"/"上涨"/"持有区间"等语义相关
        - 对于 stop_loss_price：必须在文本中找到该数字，且与"止损"/"跌破"/"离场"等语义相关
        """
        import re

        # 需要验证的价格字段及其在原文中的关联关键词
        price_fields = {
            'target_price': ['目标', '预期', '上涨', '持有区间', '第一目标', '反弹', '估值', '阻力'],
            'stop_loss_price': ['止损', '跌破', '离场', '红线', '强制', '止盈'],
            'entry_price': ['入场', '建仓', '建议', '区间'],
            'price_target_optimistic': ['乐观'],
            'price_target_pessimistic': ['悲观'],
        }

        for field_name, keywords in price_fields.items():
            price = result.get(field_name)
            if price is None:
                continue

            # 检查该数字是否在原文的合理上下文中出现
            price_str = f"{price:.2f}".rstrip('0').rstrip('.')  # 格式化：24.5, 22.1
            price_str_full = f"{price:.2f}"  # 完整格式：24.50, 22.10

            # 尝试多种格式匹配
            found = False
            for fmt_price in [price_str, price_str_full, str(price)]:
                # 匹配价格 + 前后各20字符的上下文
                pattern = re.escape(fmt_price)
                for match in re.finditer(pattern, text):
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].lower()

                    # 检查上下文是否包含关联关键词
                    for kw in keywords:
                        if kw.lower() in context:
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

            if not found:
                logger.warning(
                    f"⚠️ [SignalProcessor] {field_name}={price} 在原始文本中无明确对应上下文，"
                    f"可能为LLM捏造，设为 null（关键词：{keywords}）"
                )
                result[field_name] = None

        return result

    # =========================================================================
    # 辅助方法：语义化文本决策提取（最终回退方案）
    # =========================================================================
    def _extract_semantic_decision(self, text: str, stock_symbol: str = None) -> dict:
        """语义化的文本提取方法（最终回退方案）"""
        import re

        logger.info(f"🔍 [SignalProcessor] 使用语义化文本提取作为回退方案")

        # 提取动作
        action = '持有'
        if re.search(r'买入|BUY|超配|增持', text, re.IGNORECASE):
            action = '买入'
        elif re.search(r'卖出|SELL|低配|减仓', text, re.IGNORECASE):
            action = '卖出'

        # 提取目标价（区分语义）
        target_price = self._extract_price_by_semantics(text, action, 'target')
        stop_loss_price = self._extract_price_by_semantics(text, action, 'stop_loss')
        entry_price = self._extract_price_by_semantics(text, action, 'entry')
        optimistic = self._extract_price_by_semantics(text, action, 'optimistic')
        pessimistic = self._extract_price_by_semantics(text, action, 'pessimistic')

        # 如果仍然没有目标价，使用智能推算
        if not target_price:
            from tradingagents.utils.stock_utils import StockUtils
            market_info = StockUtils.get_market_info(stock_symbol)
            is_china = market_info['is_china']
            target_price = self._smart_price_estimation(text, action, is_china)

        result = self._build_decision_dict(
            action, target_price, 0.7, 0.5,
            '基于综合分析的投资建议（备用提取）',
            stop_loss_price=stop_loss_price, entry_price=entry_price,
            price_target_optimistic=optimistic, price_target_pessimistic=pessimistic
        )

        logger.info(f"✅ [SignalProcessor] 回退方案提取完成: action={result['action']}, target={result['target_price']}")
        return result
