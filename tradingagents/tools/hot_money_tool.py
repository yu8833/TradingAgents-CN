#!/usr/bin/env python3
"""
游资追踪与解禁监控工具
用于获取龙虎榜数据和解禁股数据，帮助分析游资动向和限售股解禁情况
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class HotMoneyAnalyzer:
    """游资追踪与解禁监控分析器"""

    def __init__(self):
        """初始化游资分析器"""
        self.ak = None
        self._initialize_akshare()

    def _initialize_akshare(self):
        """初始化AKShare连接"""
        try:
            import akshare as ak
            self.ak = ak
            logger.info("✅ AKShare游资模块初始化成功")
        except ImportError as e:
            logger.error(f"❌ AKShare未安装: {e}")
            self.ak = None

    def _is_available(self) -> bool:
        """检查AKShare是否可用"""
        return self.ak is not None

    def _format_money_value(self, value: float) -> str:
        """格式化金额显示（万元/亿元）"""
        if value is None or value == 0:
            return "0"
        if abs(value) >= 1e8:
            return f"{value / 1e8:.2f}亿"
        elif abs(value) >= 1e4:
            return f"{value / 1e4:.2f}万"
        else:
            return f"{value:.2f}"

    def _safe_get_value(self, row: Any, key: str, default: Any = None) -> Any:
        """安全获取字典值"""
        try:
            if hasattr(row, 'get'):
                return row.get(key, default)
            elif isinstance(row, dict):
                return row.get(key, default)
            return default
        except Exception:
            return default


def get_stock_hot_money(stock_code: str, days: int = 30) -> str:
    """
    获取个股龙虎榜数据

    Args:
        stock_code: 股票代码，如 "600519"
        days: 查询天数，默认30天

    Returns:
        str: 格式化的龙虎榜数据
    """
    logger.info(f"[游资工具] 开始获取 {stock_code} 的龙虎榜数据，查询天数: {days}")

    try:
        import akshare as ak
        import pandas as pd

        # 标准化股票代码
        stock_code = stock_code.strip().zfill(6)
        logger.info(f"[游资工具] 标准化后的股票代码: {stock_code}")

        # 计算查询日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        logger.info(f"[游资工具] 查询日期范围: {start_date} 至 {end_date}")

        # 调用akshare获取龙虎榜明细数据
        try:
            # stock_lhb_detail_em 返回历史龙虎榜明细数据
            lhb_df = ak.stock_lhb_detail_em(symbol=stock_code)

            if lhb_df is None or lhb_df.empty:
                logger.warning(f"[游资工具] ⚠️ {stock_code} 未找到龙虎榜数据")
                return f"❌ {stock_code} 近期没有龙虎榜数据"

            logger.info(f"[游资工具] 📊 获取到 {len(lhb_df)} 条龙虎榜记录")

            # 按日期排序
            if '日期' in lhb_df.columns:
                lhb_df = lhb_df.sort_values('日期', ascending=False)

            # 构建格式化报告
            report = f"""
=== 🏆 {stock_code} 龙虎榜数据 ===
查询天数: 最近{days}天
数据来源: 东方财富龙虎榜
查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总记录数: {len(lhb_df)} 条

"""

            # 遍历每条记录，按日期分组显示
            current_date = None
            date_count = 0

            for idx, row in lhb_df.iterrows():
                date = lhb_df.loc[idx, '日期'] if '日期' in lhb_df.columns else None
                if date is None:
                    continue

                date_str = str(date)

                # 新日期分组
                if date_str != current_date:
                    if current_date is not None:
                        report += "\n"
                    current_date = date_str
                    date_count = 0

                date_count += 1

                # 提取关键字段
                try:
                    stock_name = str(row.get('股票名称', '未知')) if '股票名称' in lhb_df.columns else str(row.get('代码', stock_code))
                    reason = str(row.get('龙虎榜净买额类别', row.get('上榜原因', '未知'))) if '龙虎榜净买额类别' in lhb_df.columns or '上榜原因' in lhb_df.columns else '未知'

                    # 金额字段
                    net_buy = row.get('龙虎榜净买额', 0) if '龙虎榜净买额' in lhb_df.columns else 0
                    close_price = row.get('收盘价', 0) if '收盘价' in lhb_df.columns else 0
                    change_pct = row.get('涨跌幅', 0) if '涨跌幅' in lhb_df.columns else 0

                    # 格式化涨跌幅
                    try:
                        change_str = f"{float(change_pct):.2f}%" if change_pct else "0.00%"
                    except (ValueError, TypeError):
                        change_str = "0.00%"

                    # 格式化金额
                    try:
                        net_buy_str = f"{float(net_buy) / 1e4:.2f}万" if net_buy else "0"
                    except (ValueError, TypeError):
                        net_buy_str = "0"

                    # 格式化价格
                    try:
                        price_str = f"{float(close_price):.2f}" if close_price else "0.00"
                    except (ValueError, TypeError):
                        price_str = "0.00"

                    # 显示当日汇总
                    if date_count == 1:
                        report += f"📅 {date_str}\n"
                        report += f"   股票: {stock_name} | 价格: {price_str} | 涨跌幅: {change_str}\n"
                        report += f"   上榜原因: {reason}\n"

                    # 如果有营业部买卖数据，显示汇总
                    if '龙虎榜净买额' in lhb_df.columns or '买卖总额' in lhb_df.columns:
                        buy_amount = row.get('买入金额', row.get('龙虎榜买入金额', 0))
                        sell_amount = row.get('卖出金额', row.get('龙虎榜卖出金额', 0))

                        try:
                            buy_str = f"{float(buy_amount) / 1e4:.2f}万" if buy_amount else "0"
                            sell_str = f"{float(sell_amount) / 1e4:.2f}万" if sell_amount else "0"
                        except (ValueError, TypeError):
                            buy_str = "0"
                            sell_str = "0"

                        report += f"   买入: {buy_str} | 卖出: {sell_str} | 净买: {net_buy_str}\n"

                except Exception as e:
                    logger.warning(f"[游资工具] 解析第{idx}行数据异常: {e}")
                    continue

            # 添加统计摘要
            report += f"""
=== 📊 数据统计 ===
总上榜次数: {len(lhb_df)}
数据记录: {len(lhb_df)} 条

注: 龙虎榜数据反映机构或游资在特定股票上的买卖行为，
可用于跟踪市场热点和资金动向。
"""

            logger.info(f"[游资工具] ✅ {stock_code} 龙虎榜数据获取成功，共 {len(lhb_df)} 条记录")
            return report.strip()

        except Exception as e:
            logger.error(f"[游资工具] ❌ 获取 {stock_code} 龙虎榜数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ 获取 {stock_code} 龙虎榜数据失败: {str(e)}"

    except ImportError as e:
        logger.error(f"[游资工具] ❌ AKShare模块未安装: {e}")
        return "❌ 错误: AKShare模块未安装，请执行 pip install akshare"
    except Exception as e:
        logger.error(f"[游资工具] ❌ 获取龙虎榜数据异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ 获取龙虎榜数据异常: {str(e)}"


def get_stock_lockup(stock_code: str, days: int = 30) -> str:
    """
    获取个股解禁数据

    Args:
        stock_code: 股票代码，如 "600519"
        days: 查询天数，默认30天

    Returns:
        str: 格式化的解禁数据
    """
    logger.info(f"[解禁工具] 开始获取 {stock_code} 的解禁数据，查询天数: {days}")

    try:
        import akshare as ak
        import pandas as pd

        # 标准化股票代码
        stock_code = stock_code.strip().zfill(6)
        logger.info(f"[解禁工具] 标准化后的股票代码: {stock_code}")

        # 计算查询日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        logger.info(f"[解禁工具] 查询日期范围: {start_date} 至 {end_date}")

        # 调用akshare获取解禁详情数据
        try:
            # stock_restricted_release_detail_em 返回解禁股详情数据
            lockup_df = ak.stock_restricted_release_detail_em(symbol=stock_code)

            if lockup_df is None or lockup_df.empty:
                logger.warning(f"[解禁工具] ⚠️ {stock_code} 未找到解禁数据")
                return f"❌ {stock_code} 近期没有解禁数据"

            logger.info(f"[解禁工具] 📊 获取到 {len(lockup_df)} 条解禁记录")

            # 构建格式化报告
            report = f"""
=== 🔓 {stock_code} 限售股解禁数据 ===
查询天数: 最近{days}天
数据来源: 东方财富限售股解禁明细
查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总记录数: {len(lockup_df)} 条

"""

            # 遍历数据并格式化显示
            for idx, row in lockup_df.iterrows():
                try:
                    # 解析各字段
                    date = row.get('解禁日期', row.get('日期', '未知'))
                    stock_name = row.get('股票名称', stock_code)
                    # 处理代码格式
                    code = row.get('代码', stock_code)
                    if isinstance(code, float):
                        code = str(int(code)).zfill(6)
                    else:
                        code = str(code).zfill(6)

                    # 解禁数量
                    restricted_shares = row.get('解禁数量', row.get('解禁股数', 0))
                    # 流通股份数
                    circulating_shares = row.get('流通股份数', 0)
                    # 解禁市值
                    market_cap = row.get('市值', row.get('解禁市值', 0))

                    # 解禁股类型
                    share_type = row.get('解禁股类型', row.get('股份类型', '未知'))

                    # 计算解禁比例（如果数据允许）
                    try:
                        if restricted_shares and circulating_shares and float(circulating_shares) > 0:
                            ratio = float(restricted_shares) / float(circulating_shares) * 100
                            ratio_str = f"{ratio:.2f}%"
                        else:
                            ratio_str = "未知"
                    except (ValueError, TypeError, ZeroDivisionError):
                        ratio_str = "未知"

                    # 格式化数量
                    try:
                        shares_str = f"{float(restricted_shares) / 1e8:.4f}亿股" if restricted_shares else "0"
                    except (ValueError, TypeError):
                        shares_str = "未知"

                    # 格式化市值
                    try:
                        if market_cap:
                            if abs(float(market_cap)) >= 1e8:
                                cap_str = f"{float(market_cap) / 1e8:.2f}亿元"
                            elif abs(float(market_cap)) >= 1e4:
                                cap_str = f"{float(market_cap) / 1e4:.2f}万元"
                            else:
                                cap_str = f"{float(market_cap):.2f}元"
                        else:
                            cap_str = "未知"
                    except (ValueError, TypeError):
                        cap_str = "未知"

                    report += f"📅 解禁日期: {date}\n"
                    report += f"   股票: {stock_name}({code})\n"
                    report += f"   解禁数量: {shares_str}\n"
                    report += f"   解禁市值: {cap_str}\n"
                    report += f"   股份类型: {share_type}\n"
                    report += f"   解禁比例: {ratio_str}\n"
                    report += "---\n"

                except Exception as e:
                    logger.warning(f"[解禁工具] 解析第{idx}行数据异常: {e}")
                    continue

            # 添加统计摘要
            total_restricted = 0
            total_market_cap = 0

            try:
                if '解禁数量' in lockup_df.columns:
                    total_restricted = lockup_df['解禁数量'].sum()
                if '市值' in lockup_df.columns:
                    total_market_cap = lockup_df['市值'].sum()
                elif '解禁市值' in lockup_df.columns:
                    total_market_cap = lockup_df['解禁市值'].sum()
            except Exception:
                pass

            try:
                total_str = f"{float(total_restricted) / 1e8:.4f}亿股" if total_restricted else "未知"
            except (ValueError, TypeError):
                total_str = "未知"

            try:
                if total_market_cap:
                    if abs(float(total_market_cap)) >= 1e8:
                        cap_total_str = f"{float(total_market_cap) / 1e8:.2f}亿元"
                    else:
                        cap_total_str = f"{float(total_market_cap):.2f}元"
                else:
                    cap_total_str = "未知"
            except (ValueError, TypeError):
                cap_total_str = "未知"

            report += f"""
=== 📊 数据统计 ===
总解禁次数: {len(lockup_df)}
总解禁数量: {total_str}
总解禁市值: {cap_total_str}

注: 限售股解禁通常会对股价形成一定压力，尤其是解禁数量较大时。
需结合市场情绪和股东减持意愿综合分析。
"""

            logger.info(f"[解禁工具] ✅ {stock_code} 解禁数据获取成功，共 {len(lockup_df)} 条记录")
            return report.strip()

        except Exception as e:
            logger.error(f"[解禁工具] ❌ 获取 {stock_code} 解禁数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ 获取 {stock_code} 解禁数据失败: {str(e)}"

    except ImportError as e:
        logger.error(f"[解禁工具] ❌ AKShare模块未安装: {e}")
        return "❌ 错误: AKShare模块未安装，请执行 pip install akshare"
    except Exception as e:
        logger.error(f"[解禁工具] ❌ 获取解禁数据异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ 获取解禁数据异常: {str(e)}"


def get_market_hot_money(days: int = 5) -> str:
    """
    获取近期市场游资活跃榜

    Args:
        days: 查询天数，默认5天

    Returns:
        str: 格式化的市场游资活跃数据
    """
    logger.info(f"[游资工具] 开始获取市场游资活跃榜，查询天数: {days}")

    try:
        import akshare as ak
        import pandas as pd

        # 计算查询日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        logger.info(f"[游资工具] 查询日期范围: {start_date} 至 {end_date}")

        # 获取龙虎榜成交数据
        try:
            # stock_lhb_yyt_net_em 返回龙虎榜营业部成交排行
            # stock_lhb_hsgt_em 返回沪股通/深股通龙虎榜数据
            # stock_lhb_hsgt_list_em 返回龙虎榜个股沪股通/深股通数据

            report = f"""
=== 🔥 市场游资活跃榜 ===
查询天数: 最近{days}天
数据来源: 东方财富龙虎榜
查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

            # 方法1: 获取龙虎榜营业部排行
            try:
                # stock_lhb_trader_em 返回营业部排行榜
                trader_df = ak.stock_lhb_trader_em()

                if trader_df is not None and not trader_df.empty:
                    logger.info(f"[游资工具] 📊 获取到营业部排行榜 {len(trader_df)} 条记录")

                    report += "📊 营业部交易排行 (Top 20):\n"
                    report += "-" * 60 + "\n"

                    # 显示前20名
                    for idx, row in trader_df.head(20).iterrows():
                        try:
                            trader_name = row.get('营业部名称', row.get('交易席位', '未知'))
                            buy_amount = row.get('买入金额', 0)
                            sell_amount = row.get('卖出金额', 0)
                            net_amount = row.get('净买额', 0)

                            # 格式化金额
                            try:
                                buy_str = f"{float(buy_amount) / 1e4:.2f}万" if buy_amount else "0"
                                sell_str = f"{float(sell_amount) / 1e4:.2f}万" if sell_amount else "0"
                                net_str = f"{float(net_amount) / 1e4:.2f}万" if net_amount else "0"
                            except (ValueError, TypeError):
                                buy_str = sell_str = net_str = "0"

                            report += f"{idx + 1}. {trader_name}\n"
                            report += f"   买入: {buy_str} | 卖出: {sell_str} | 净买: {net_str}\n"

                        except Exception as e:
                            logger.warning(f"[游资工具] 解析营业部排行第{idx}行异常: {e}")
                            continue

                    report += "\n"

            except Exception as e:
                logger.warning(f"[游资工具] 获取营业部排行榜失败: {e}")

            # 方法2: 获取龙虎榜个股排行
            try:
                # stock_lhb_detail_em 可以获取所有龙虎榜明细
                # 按股票代码分组统计
                lhb_df = ak.stock_lhb_detail_em(symbol="")

                if lhb_df is not None and not lhb_df.empty:
                    logger.info(f"[游资工具] 📊 获取到龙虎榜明细 {len(lhb_df)} 条记录")

                    # 按股票代码分组统计
                    if '代码' in lhb_df.columns:
                        # 根据可用列选择聚合字段
                        agg_dict = {'股票名称': 'first'}
                        if '龙虎榜净买额' in lhb_df.columns:
                            agg_dict['龙虎榜净买额'] = 'sum'
                        elif '成交量' in lhb_df.columns:
                            agg_dict['成交量'] = 'sum'

                        stock_stats = lhb_df.groupby('代码').agg(agg_dict).reset_index()

                        # 按净买额排序
                        if '龙虎榜净买额' in stock_stats.columns:
                            stock_stats = stock_stats.sort_values('龙虎榜净买额', ascending=False)
                        elif '成交量' in stock_stats.columns:
                            stock_stats = stock_stats.sort_values('成交量', ascending=False)

                        report += "📈 龙虎榜活跃个股 (Top 20):\n"
                        report += "-" * 60 + "\n"

                        for idx, row in stock_stats.head(20).iterrows():
                            try:
                                code = str(row.get('代码', '未知')).zfill(6)
                                name = row.get('股票名称', f'股票{code}')
                                net_buy = row.get('龙虎榜净买额', 0)
                                close_price = row.get('收盘价', 0)
                                change_pct = row.get('涨跌幅', 0)

                                try:
                                    net_str = f"{float(net_buy) / 1e4:.2f}万" if net_buy else "0"
                                except (ValueError, TypeError):
                                    net_str = "0"

                                try:
                                    change_str = f"{float(change_pct):.2f}%" if change_pct else "0.00%"
                                except (ValueError, TypeError):
                                    change_str = "0.00%"

                                report += f"{idx + 1}. {name}({code})\n"
                                report += f"   涨跌幅: {change_str} | 龙虎榜净买: {net_str}\n"

                            except Exception as e:
                                logger.warning(f"[游资工具] 解析个股排行第{idx}行异常: {e}")
                                continue

            except Exception as e:
                logger.warning(f"[游资工具] 获取龙虎榜个股排行失败: {e}")

            # 方法3: 获取近期龙虎榜汇总
            try:
                # stock_lhb_em 返回龙虎榜汇总数据
                summary_df = ak.stock_lhb_em()

                if summary_df is not None and not summary_df.empty:
                    logger.info(f"[游资工具] 📊 获取到龙虎榜汇总 {len(summary_df)} 条记录")

                    report += "\n📋 近期龙虎榜汇总:\n"
                    report += "-" * 60 + "\n"

                    for idx, row in summary_df.head(10).iterrows():
                        try:
                            date = row.get('日期', '未知')
                            stock_name = row.get('股票名称', '未知')
                            code = str(row.get('代码', '未知')).zfill(6)
                            reason = row.get('上榜原因', row.get('类别', '未知'))
                            close_price = row.get('收盘价', 0)
                            change_pct = row.get('涨跌幅', 0)

                            try:
                                change_str = f"{float(change_pct):.2f}%" if change_pct else "0.00%"
                            except (ValueError, TypeError):
                                change_str = "0.00%"

                            try:
                                price_str = f"{float(close_price):.2f}" if close_price else "0.00"
                            except (ValueError, TypeError):
                                price_str = "0.00"

                            report += f"📅 {date} | {stock_name}({code}) | {reason}\n"
                            report += f"   价格: {price_str} | 涨跌幅: {change_str}\n"

                        except Exception as e:
                            logger.warning(f"[游资工具] 解析龙虎榜汇总第{idx}行异常: {e}")
                            continue

            except Exception as e:
                logger.warning(f"[游资工具] 获取龙虎榜汇总失败: {e}")

            report += f"""
=== 📊 分析提示 ===
龙虎榜数据反映当日活跃营业部和机构的交易情况，
可结合以下因素分析:
1. 机构和游资的买卖方向
2. 涨停股的连板情况
3. 营业部交易席位的活跃度
4. 个股上榜原因和基本面
"""

            logger.info(f"[游资工具] ✅ 市场游资活跃榜获取成功")
            return report.strip()

        except Exception as e:
            logger.error(f"[游资工具] ❌ 获取市场游资数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ 获取市场游资活跃榜失败: {str(e)}"

    except ImportError as e:
        logger.error(f"[游资工具] ❌ AKShare模块未安装: {e}")
        return "❌ 错误: AKShare模块未安装，请执行 pip install akshare"
    except Exception as e:
        logger.error(f"[游资工具] ❌ 获取市场游资活跃榜异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ 获取市场游资活跃榜异常: {str(e)}"


def create_hot_money_tool():
    """创建游资追踪工具函数"""

    def get_stock_hot_money_func(stock_code: str, days: int = 30) -> str:
        """
        获取个股龙虎榜数据

        Args:
            stock_code (str): 股票代码，如 "600519"
            days (int): 查询天数，默认30天

        Returns:
            str: 格式化的龙虎榜数据
        """
        if not stock_code:
            return "❌ 错误: 未提供股票代码"
        return get_stock_hot_money(stock_code, days)

    def get_stock_lockup_func(stock_code: str, days: int = 30) -> str:
        """
        获取个股解禁数据

        Args:
            stock_code (str): 股票代码，如 "600519"
            days (int): 查询天数，默认30天

        Returns:
            str: 格式化的解禁数据
        """
        if not stock_code:
            return "❌ 错误: 未提供股票代码"
        return get_stock_lockup(stock_code, days)

    def get_market_hot_money_func(days: int = 5) -> str:
        """
        获取近期市场游资活跃榜

        Args:
            days (int): 查询天数，默认5天

        Returns:
            str: 格式化的市场游资活跃数据
        """
        return get_market_hot_money(days)

    # 设置工具属性
    get_stock_hot_money_func.name = "get_stock_hot_money"
    get_stock_hot_money_func.description = """
游资追踪工具 - 获取个股龙虎榜数据

功能:
- 获取指定股票的历史龙虎榜明细
- 显示上榜原因、买卖金额、涨跌幅等信息
- 帮助跟踪游资和机构的交易动向

参数:
- stock_code: 股票代码 (如 "600519", "000001")
- days: 查询天数，默认30天

返回格式化的龙虎榜数据，便于LLM分析
"""

    get_stock_lockup_func.name = "get_stock_lockup"
    get_stock_lockup_func.description = """
解禁监控工具 - 获取个股限售股解禁数据

功能:
- 获取指定股票的限售股解禁详情
- 显示解禁日期、解禁数量、解禁市值等信息
- 帮助评估解禁对股价的潜在影响

参数:
- stock_code: 股票代码 (如 "600519", "000001")
- days: 查询天数，默认30天

返回格式化的解禁数据，便于LLM分析
"""

    get_market_hot_money_func.name = "get_market_hot_money"
    get_market_hot_money_func.description = """
市场游资活跃榜 - 获取近期市场游资动向

功能:
- 获取近期龙虎榜营业部交易排行
- 获取龙虎榜活跃个股排行
- 获取近期龙虎榜汇总信息
- 帮助把握市场热点和资金流向

参数:
- days: 查询天数，默认5天

返回格式化的游资活跃数据，便于LLM分析
"""

    return {
        'get_stock_hot_money': get_stock_hot_money_func,
        'get_stock_lockup': get_stock_lockup_func,
        'get_market_hot_money': get_market_hot_money_func
    }
