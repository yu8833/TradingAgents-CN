<template>
  <div class="report-detail">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 报告内容 -->
    <div v-else-if="report" class="report-content">
      <!-- 报告头部 -->
      <el-card class="report-header" shadow="never">
        <div class="header-content">
          <div class="title-section">
            <h1 class="report-title">
              <el-icon><Document /></el-icon>
              {{ report.stock_name || report.stock_symbol }} 分析报告
            </h1>
            <div class="report-meta">
              <el-tag type="primary">{{ report.stock_symbol }}</el-tag>
              <el-tag v-if="report.stock_name && report.stock_name !== report.stock_symbol" type="info">{{ report.stock_name }}</el-tag>
              <el-tag type="success">{{ getStatusText(report.status) }}</el-tag>
              <span class="meta-item">
                <el-icon><Calendar /></el-icon>
                {{ formatTime(report.created_at) }}
              </span>
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ formatAnalysts(report.analysts) }}
              </span>
              <span v-if="report.model_info && report.model_info !== 'Unknown'" class="meta-item">
                <el-icon><Cpu /></el-icon>
                <el-tooltip :content="getModelDescription(report.model_info)" placement="top">
                  <el-tag type="info" style="cursor: help;">{{ report.model_info }}</el-tag>
                </el-tooltip>
              </span>
            </div>
          </div>
          
          <div class="action-section">
            <el-button
              v-if="canApplyToTrading"
              type="success"
              @click="applyToTrading"
            >
              <el-icon><ShoppingCart /></el-icon>
              应用到交易
            </el-button>
            <el-dropdown trigger="click" @command="downloadReport">
              <el-button type="primary">
                <el-icon><Download /></el-icon>
                下载报告
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="markdown">
                    <el-icon><document /></el-icon> Markdown
                  </el-dropdown-item>
                  <el-dropdown-item command="docx">
                    <el-icon><document /></el-icon> Word 文档
                  </el-dropdown-item>
                  <el-dropdown-item command="pdf">
                    <el-icon><document /></el-icon> PDF
                  </el-dropdown-item>
                  <el-dropdown-item command="json" divided>
                    <el-icon><document /></el-icon> JSON (原始数据)
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="goBack">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 策略点位 & 价格区间（daily_stock_analysis 风格） -->
      <el-card class="strategy-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Promotion /></el-icon>
            <span>策略点位</span>
            <el-tag v-if="pickField(report, ['评级', 'action', '操作建议'])" :type="getDecisionActionTagType(pickField(report, ['评级', 'action', '操作建议']))" size="small" style="margin-left: 12px;">操作建议：{{ pickField(report, ['评级', 'action', '操作建议']) }}</el-tag>
            <el-tag type="info" size="small" style="margin-left: 12px;">仅供参考</el-tag>
          </div>
        </template>
        <div class="strategy-grid">
          <div class="price-block buy-block">
            <div class="price-label">💰 理想买入价</div>
            <div class="price-value">{{ formatPriceValue(report, ['理想买入', 'ideal_buy', 'target_price']) }}</div>
            <div class="price-sub">首次建仓参考价</div>
          </div>
          <div class="price-block add-block">
            <div class="price-label">📈 二次买入价</div>
            <div class="price-value">{{ formatPriceValue(report, ['二次买入', 'second_buy']) }}</div>
            <div class="price-sub">回调加仓参考</div>
          </div>
          <div class="price-block stop-block">
            <div class="price-label">🛑 止损价格</div>
            <div class="price-value">{{ formatPriceValue(report, ['止损价格', 'stop_loss', 'stop_loss_price']) }}</div>
            <div class="price-sub">无条件离场参考</div>
          </div>
          <div class="price-block target-block">
            <div class="price-label">🎯 止盈目标价</div>
            <div class="price-value">{{ formatPriceValue(report, ['止盈目标', 'target_price', 'price_target']) }}</div>
            <div class="price-sub">减仓/获利参考</div>
          </div>
          <div class="price-block support-block">
            <div class="price-label">📉 支撑位</div>
            <div class="price-value">{{ formatPriceValue(report, ['支撑位', 'support_level']) }}</div>
            <div class="price-sub">下方关键支撑</div>
          </div>
          <div class="price-block resistance-block">
            <div class="price-label">📈 阻力位</div>
            <div class="price-value">{{ formatPriceValue(report, ['阻力位', 'resistance_level']) }}</div>
            <div class="price-sub">上方压力参考</div>
          </div>
        </div>

        <!-- 文本洞察 - 卡片式布局，鼠标悬停显示维度说明 -->
        <div v-if="hasAnyInsight(report)" class="insights-block">
          <div class="block-title">
            <el-icon :size="18"><Reading /></el-icon>
            <span class="block-title-text">核心洞察</span>
            <el-tooltip content="AI 基于多维度分析提炼的关键结论，用于快速把握报告要点" placement="top" :show-after="200">
              <el-icon class="help-icon" :size="14"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <div class="insight-grid">
            <div
              v-for="item in insightItems"
              :key="item.key"
              :class="['insight-card', `insight-${item.key}`]"
            >
              <el-tooltip :content="item.tooltip" placement="top" :show-after="200" effect="light">
                <div class="insight-card-header">
                  <div class="insight-card-icon">{{ item.icon }}</div>
                  <div class="insight-card-text-wrap">
                    <div class="insight-card-title">{{ item.title }}</div>
                    <div class="insight-card-subtitle">{{ item.subtitle }}</div>
                  </div>
                </div>
              </el-tooltip>
              <div class="insight-card-body" v-html="renderInsightFull(item.fullText || item.text)"></div>
            </div>
          </div>
        </div>

        <!-- 综合评分 - 卡片式进度条布局，悬停显示维度解释 -->
        <div v-if="hasAnyScore(report)" class="dimension-block">
          <div class="block-title">
            <el-icon :size="18"><DataAnalysis /></el-icon>
            <span class="block-title-text">多维度评分</span>
            <el-tooltip content="每个维度得分基于 AI 对该维度信息的综合评估，用于辅助判断整体价值分布" placement="top" :show-after="200">
              <el-icon class="help-icon" :size="14"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <div class="dimension-grid">
            <div
              v-for="dim in dimensionItems"
              :key="dim.key"
              :class="['dimension-card', `dim-${dim.key}`]"
            >
              <el-tooltip :content="dim.tooltip" placement="top" :show-after="200" effect="light">
                <div class="dimension-card-header">
                  <div class="dimension-icon">{{ dim.icon }}</div>
                  <div class="dimension-text-wrap">
                    <div class="dimension-name">{{ dim.name }}</div>
                    <div class="dimension-subtitle">{{ dim.subtitle }}</div>
                  </div>
                </div>
              </el-tooltip>
              <template v-if="dim.type === 'progress'">
                <div class="dimension-progress">
                  <el-progress
                    :percentage="dim.value"
                    :color="dim.color"
                    :stroke-width="12"
                    :show-text="false"
                  />
                </div>
                <div class="dimension-value">
                  <span class="score-number">{{ dim.value }}</span>
                  <span class="score-unit">/ 100</span>
                </div>
                <div class="dimension-label" :style="{ color: dim.color[0] }">
                  <el-icon :size="14"><TrendCharts /></el-icon>
                  <span>{{ dim.label }}</span>
                </div>
              </template>
              <template v-else>
                <div class="dimension-risk">
                  <el-icon
                    v-for="n in 5"
                    :key="n"
                    :size="20"
                    :class="['risk-star', { active: n <= dim.stars }]"
                    :color="n <= dim.stars ? dim.starColor : '#DCDFE6'"
                  >
                    <StarFilled />
                  </el-icon>
                </div>
                <div class="dimension-value">
                  <span class="score-number" :style="{ color: dim.starColor }">{{ dim.text }}</span>
                </div>
                <div class="dimension-label" :style="{ color: dim.starColor }">
                  <el-icon :size="14"><WarningFilled /></el-icon>
                  <span>{{ dim.label }}</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 报告模块 - 带统一的 markdown 样式 -->
      <el-card class="modules-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Files /></el-icon>
            <span>分析师报告</span>
            <span class="header-tip">以下内容由 AI 分角色撰写，仅供参考</span>
          </div>
        </template>

        <el-tabs v-model="activeModule" type="border-card" class="report-tabs">
          <el-tab-pane
            v-for="moduleName in reportModuleKeys"
            :key="moduleName"
            :label="getModuleDisplayName(moduleName)"
            :name="moduleName"
          >
            <div class="module-content">
              <div v-if="typeof report.reports[moduleName] === 'string'" class="markdown-body">
                <div v-html="renderMarkdown(report.reports[moduleName] as string)"></div>
              </div>
              <div v-else class="json-content">
                <pre>{{ JSON.stringify(report.reports[moduleName], null, 2) }}</pre>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-result
        icon="error"
        title="报告加载失败"
        sub-title="请检查报告ID是否正确或稍后重试"
      >
        <template #extra>
          <el-button type="primary" @click="goBack">返回列表</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElInputNumber } from 'element-plus'
import { paperApi } from '@/api/paper'
import { stocksApi } from '@/api/stocks'
import { configApi, type LLMConfig } from '@/api/config'
import {
  Document,
  Calendar,
  User,
  Download,
  Back,
  InfoFilled,
  TrendCharts,
  Files,
  ShoppingCart,
  WarningFilled,
  DataAnalysis,
  Warning,
  StarFilled,
  List,
  Check,
  Cpu,
  QuestionFilled,
  ArrowDown,
  Reading,
  MoreFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { marked } from 'marked'
import { getMarketByStockCode } from '@/utils/market'
import type { CurrencyAmount } from '@/api/paper'

type ReportModuleContent = string | Record<string, unknown>

type ReportDetailData = {
  id: string
  analysis_id?: string
  stock_symbol: string
  stock_name?: string
  status: string
  created_at: string
  analysis_date?: string
  analysts: string[]
  model_info?: string
  recommendation?: string
  risk_level?: string
  confidence_score?: number
  key_points?: string[]
  summary?: string
  reports: Record<string, ReportModuleContent>
}

// 路由和认证
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 配置 marked 以获得更完整的 Markdown 支持
marked.setOptions({ breaks: true, gfm: true })

// 响应式数据
const loading = ref(true)
const report = ref<ReportDetailData | null>(null)
const activeModule = ref('')
const llmConfigs = ref<LLMConfig[]>([]) // 存储所有模型配置
const reportModuleKeys = computed<string[]>(() => report.value ? Object.keys(report.value.reports || {}) : [])

// 获取模型配置列表
const fetchLLMConfigs = async () => {
  try {
    const systemConfig = await configApi.getSystemConfig()
    llmConfigs.value = systemConfig.llm_configs || []
  } catch (error) {
    console.error('获取模型配置失败:', error)
  }
}

// 获取报告详情
const fetchReportDetail = async () => {
  loading.value = true
  try {
    const reportId = route.params.id as string

    const response = await fetch(`/api/reports/${reportId}/detail`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const result = await response.json()

    if (result.success) {
      report.value = result.data

      // 设置默认激活的模块
      const reports = result.data.reports || {}
      const moduleNames = Object.keys(reports)
      if (moduleNames.length > 0) {
        activeModule.value = moduleNames[0]
      }
    } else {
      throw new Error(result.message || '获取报告详情失败')
    }
  } catch (error) {
    console.error('获取报告详情失败:', error)
    ElMessage.error('获取报告详情失败')
  } finally {
    loading.value = false
  }
}

// 下载报告
const downloadReport = async (format: string = 'markdown') => {
  try {
    if (!report.value) return
    const currentReport = report.value

    // 显示加载提示
    const loadingMsg = ElMessage({
      message: `正在生成${getFormatName(format)}格式报告...`,
      type: 'info',
      duration: 0
    })

    const response = await fetch(`/api/reports/${currentReport.id}/download?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    loadingMsg.close()

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `HTTP ${response.status}`)
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    // 根据格式设置文件扩展名
    const ext = getFileExtension(format)
    a.download = `${currentReport.stock_symbol}_分析报告_${currentReport.analysis_date || currentReport.created_at}.${ext}`

    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    ElMessage.success(`${getFormatName(format)}报告下载成功`)
  } catch (error: any) {
    console.error('下载报告失败:', error)

    // 显示详细错误信息
    if (error.message && error.message.includes('pandoc')) {
      ElMessage.error({
        message: 'PDF/Word 导出需要安装 pandoc 工具',
        duration: 5000
      })
    } else {
      ElMessage.error(`下载报告失败: ${error.message || '未知错误'}`)
    }
  }
}

// 辅助函数：获取格式名称
const getFormatName = (format: string): string => {
  const names: Record<string, string> = {
    'markdown': 'Markdown',
    'docx': 'Word',
    'pdf': 'PDF',
    'json': 'JSON'
  }
  return names[format] || format
}

// 辅助函数：获取文件扩展名
const getFileExtension = (format: string): string => {
  const extensions: Record<string, string> = {
    'markdown': 'md',
    'docx': 'docx',
    'pdf': 'pdf',
    'json': 'json'
  }
  return extensions[format] || 'txt'
}

// 判断是否可以应用到交易
const canApplyToTrading = computed(() => {
  if (!report.value) return false
  const rec = report.value.recommendation || ''
  // 检查是否包含买入或卖出建议
  return rec.includes('买入') || rec.includes('卖出') || rec.toLowerCase().includes('buy') || rec.toLowerCase().includes('sell')
})

// 解析投资建议
const parseRecommendation = () => {
  if (!report.value) return null

  const rec = report.value.recommendation || ''
  const traderPlan = report.value.reports?.trader_investment_plan || ''

  // 解析操作类型
  let action: 'buy' | 'sell' | null = null
  if (rec.includes('买入') || rec.toLowerCase().includes('buy')) {
    action = 'buy'
  } else if (rec.includes('卖出') || rec.toLowerCase().includes('sell')) {
    action = 'sell'
  }

  if (!action) return null

  // 解析目标价格（从recommendation或trader_investment_plan中提取）
  let targetPrice: number | null = null
  const traderPlanText = typeof traderPlan === 'string' ? traderPlan : ''
  const priceMatch = rec.match(/目标价[格]?[：:]\s*([0-9.]+)/) ||
                     traderPlanText.match(/目标价[格]?[：:]\s*([0-9.]+)/)
  if (priceMatch) {
    targetPrice = parseFloat(priceMatch[1])
  }

  return {
    action,
    targetPrice,
    confidence: report.value.confidence_score || 0,
    riskLevel: report.value.risk_level || '中等'
  }
}

// 辅助函数：根据股票代码获取对应货币的现金金额
const getCashByCurrency = (account: any, stockSymbol: string): number => {
  const cash = account.cash

  // 兼容旧格式（单一数字）
  if (typeof cash === 'number') {
    return cash
  }

  // 新格式（多货币对象）
  if (typeof cash === 'object' && cash !== null) {
    // 根据股票代码判断市场类型
    const marketType = getMarketByStockCode(stockSymbol)

    // 映射市场类型到货币
    const currencyMap: Record<string, keyof CurrencyAmount> = {
      'A股': 'CNY',
      '港股': 'HKD',
      '美股': 'USD'
    }

    const currency = currencyMap[marketType] || 'CNY'
    return cash[currency] || 0
  }

  return 0
}

// 应用到模拟交易
const applyToTrading = async () => {
  const recommendation = parseRecommendation()
  if (!recommendation) {
    ElMessage.warning('无法解析投资建议，请检查报告内容')
    return
  }
  if (!report.value) return
  const currentReport = report.value

  try {
    // 获取账户信息
    const accountRes = await paperApi.getAccount()
    if (!accountRes.success || !accountRes.data) {
      ElMessage.error('获取账户信息失败')
      return
    }

    const account = accountRes.data.account
    const positions = accountRes.data.positions

    // 查找当前持仓
    const currentPosition = positions.find(p => p.code === currentReport.stock_symbol)

    // 获取当前实时价格
    let currentPrice = 10 // 默认价格
    try {
      const quoteRes = await stocksApi.getQuote(currentReport.stock_symbol)
      if (quoteRes.success && quoteRes.data && quoteRes.data.price) {
        currentPrice = quoteRes.data.price
      }
    } catch (error) {
      console.warn('获取实时价格失败，使用默认价格')
    }

    // 获取对应货币的可用资金
    const availableCash = getCashByCurrency(account, currentReport.stock_symbol)

    // 计算建议交易数量
    let suggestedQuantity = 0
    let maxQuantity = 0

    if (recommendation.action === 'buy') {
      // 买入：根据可用资金和当前价格计算
      maxQuantity = Math.floor(availableCash / currentPrice / 100) * 100 // 100股为单位
      const suggested = Math.floor(maxQuantity * 0.2) // 建议使用20%资金
      suggestedQuantity = Math.floor(suggested / 100) * 100 // 向下取整到100的倍数
      suggestedQuantity = Math.max(100, suggestedQuantity) // 至少100股
    } else {
      // 卖出：根据当前持仓计算
      if (!currentPosition || currentPosition.quantity === 0) {
        ElMessage.warning('当前没有持仓，无法卖出')
        return
      }
      maxQuantity = currentPosition.quantity
      suggestedQuantity = Math.floor(maxQuantity / 100) * 100 // 向下取整到100的倍数
      suggestedQuantity = Math.max(100, suggestedQuantity) // 至少100股
    }

    // 用户可修改的价格和数量（使用reactive）
    const tradeForm = reactive({
      price: currentPrice,
      quantity: suggestedQuantity
    })

    // 显示可编辑的确认对话框
    const actionText = recommendation.action === 'buy' ? '买入' : '卖出'
    const actionColor = recommendation.action === 'buy' ? '#67C23A' : '#F56C6C'

    // 创建一个响应式的消息组件
    const MessageComponent = {
      setup() {
        // 计算预计金额
        const estimatedAmount = computed(() => {
          return (tradeForm.price * tradeForm.quantity).toFixed(2)
        })

        return () => h('div', { style: 'line-height: 2;' }, [
          // 风险提示横幅
          h('div', {
            style: 'background-color: #FEF0F0; border: 1px solid #F56C6C; border-radius: 4px; padding: 12px; margin-bottom: 16px;'
          }, [
            h('div', { style: 'color: #F56C6C; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center;' }, [
              h('span', { style: 'font-size: 16px; margin-right: 6px;' }, '⚠️'),
              h('span', '风险提示')
            ]),
            h('div', { style: 'color: #606266; font-size: 12px; line-height: 1.6;' }, [
              h('p', { style: 'margin: 4px 0;' }, '• 本交易基于AI分析结果，仅供参考，不构成投资建议'),
              h('p', { style: 'margin: 4px 0;' }, '• 模拟交易使用虚拟资金，与实盘存在显著差异'),
              h('p', { style: 'margin: 4px 0;' }, '• 股票投资存在市场风险，可能导致本金损失'),
              h('p', { style: 'margin: 4px 0;' }, '• 请勿将模拟结果作为实盘投资决策依据')
            ])
          ]),
          h('p', [
            h('strong', '股票代码：'),
            h('span', currentReport.stock_symbol)
          ]),
          h('p', [
            h('strong', '操作类型：'),
            h('span', { style: `color: ${actionColor}; font-weight: bold;` }, actionText)
          ]),
          recommendation.targetPrice ? h('p', [
            h('strong', '目标价格：'),
            h('span', { style: 'color: #E6A23C;' }, `${recommendation.targetPrice.toFixed(2)}元`),
            h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(仅供参考)')
          ]) : null,
          h('p', [
            h('strong', '当前价格：'),
            h('span', `${currentPrice.toFixed(2)}元`)
          ]),
          h('div', { style: 'margin: 16px 0;' }, [
            h('p', { style: 'margin-bottom: 8px;' }, [
              h('strong', '交易价格：'),
              h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(可修改)')
            ]),
            h(ElInputNumber, {
              modelValue: tradeForm.price,
              'onUpdate:modelValue': (val?: number) => { tradeForm.price = val ?? tradeForm.price },
              min: 0.01,
              max: 9999,
              precision: 2,
              step: 0.01,
              style: 'width: 200px;',
              controls: true
            })
          ]),
          h('div', { style: 'margin: 16px 0;' }, [
            h('p', { style: 'margin-bottom: 8px;' }, [
              h('strong', '交易数量：'),
              h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(可修改，100股为单位)')
            ]),
            h(ElInputNumber, {
              modelValue: tradeForm.quantity,
              'onUpdate:modelValue': (val?: number) => { tradeForm.quantity = val ?? tradeForm.quantity },
              min: 100,
              max: maxQuantity,
              step: 100,
              style: 'width: 200px;',
              controls: true
            })
          ]),
          h('p', [
            h('strong', '预计金额：'),
            h('span', { style: 'color: #409EFF; font-weight: bold;' }, `${estimatedAmount.value}元`)
          ]),
          h('p', [
            h('strong', '模型置信度：'),
            h('span', `${(recommendation.confidence * 100).toFixed(1)}%`),
            h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(不代表实际成功率)')
          ]),
          h('p', [
            h('strong', '风险评估：'),
            h('span', recommendation.riskLevel),
            h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(实际风险可能更高)')
          ]),
          recommendation.action === 'buy' ? h('p', { style: 'color: #909399; font-size: 12px; margin-top: 12px;' },
            `可用资金：${availableCash.toFixed(2)}元，最大可买：${maxQuantity}股`
          ) : null,
          recommendation.action === 'sell' ? h('p', { style: 'color: #909399; font-size: 12px; margin-top: 12px;' },
            `当前持仓：${maxQuantity}股`
          ) : null
        ])
      }
    }

    await ElMessageBox({
      title: '确认交易',
      message: h(MessageComponent),
      confirmButtonText: '确认下单',
      cancelButtonText: '取消',
      type: 'warning',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          // 验证输入
          if (tradeForm.quantity < 100 || tradeForm.quantity % 100 !== 0) {
            ElMessage.error('交易数量必须是100的整数倍')
            return
          }
          if (tradeForm.quantity > maxQuantity) {
            ElMessage.error(`交易数量不能超过${maxQuantity}股`)
            return
          }
          if (tradeForm.price <= 0) {
            ElMessage.error('交易价格必须大于0')
            return
          }

          // 检查资金是否充足
          if (recommendation.action === 'buy') {
            const totalAmount = tradeForm.price * tradeForm.quantity
            if (totalAmount > availableCash) {
              ElMessage.error('可用资金不足')
              return
            }
          }
        }
        done()
      }
    })

    // 执行交易
    const orderRes = await paperApi.placeOrder({
      code: currentReport.stock_symbol,
      side: recommendation.action,
      quantity: tradeForm.quantity,
      analysis_id: currentReport.analysis_id || currentReport.id
    })

    if (orderRes.success) {
      ElMessage.success(`${actionText}订单已提交成功！`)
      // 可选：跳转到模拟交易页面
      setTimeout(() => {
        router.push({ name: 'PaperTradingHome' })
      }, 1500)
    } else {
      ElMessage.error(orderRes.message || '下单失败')
    }

  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('应用到交易失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 返回列表
const goBack = () => {
  router.push('/reports')
}

// 工具函数
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    completed: '已完成',
    processing: '生成中',
    failed: '失败'
  }
  return statusMap[status] || status
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

// 将分析师英文名称转换为中文
const formatAnalysts = (analysts: string[]) => {
  const analystNameMap: Record<string, string> = {
    'market': '市场分析师',
    'fundamentals': '基本面分析师',
    'news': '新闻分析师',
    'social': '社交媒体分析师',
    'policy': '政策分析师',
    'hot_money': '游资追踪师',
    'lockup': '解禁追踪师'
  }

  return analysts.map(analyst => analystNameMap[analyst] || analyst).join('、')
}

// 获取模型的详细描述（从后端配置中获取）
const getModelDescription = (modelInfo: string) => {
  if (!modelInfo || modelInfo === 'Unknown') {
    return '未知模型'
  }

  // 1. 优先从后端配置中查找精确匹配
  const config = llmConfigs.value.find(c => c.model_name === modelInfo)
  if (config?.description) {
    return config.description
  }

  // 2. 尝试模糊匹配（处理版本号等变化）
  const fuzzyConfig = llmConfigs.value.find(c =>
    modelInfo.toLowerCase().includes(c.model_name.toLowerCase()) ||
    c.model_name.toLowerCase().includes(modelInfo.toLowerCase())
  )
  if (fuzzyConfig?.description) {
    return fuzzyConfig.description
  }

  // 3. 根据模型名称前缀提供通用描述
  const modelLower = modelInfo.toLowerCase()
  if (modelLower.includes('gpt')) {
    return `OpenAI ${modelInfo} - 强大的语言模型`
  } else if (modelLower.includes('claude')) {
    return `Anthropic ${modelInfo} - 高性能推理模型`
  } else if (modelLower.includes('qwen')) {
    return `阿里通义千问 ${modelInfo} - 中文优化模型`
  } else if (modelLower.includes('glm')) {
    return `智谱 ${modelInfo} - 综合性能优秀`
  } else if (modelLower.includes('deepseek')) {
    return `DeepSeek ${modelInfo} - 高性价比模型`
  } else if (modelLower.includes('ernie')) {
    return `百度文心 ${modelInfo} - 中文能力强`
  } else if (modelLower.includes('spark')) {
    return `讯飞星火 ${modelInfo} - 专业模型`
  } else if (modelLower.includes('moonshot')) {
    return `Moonshot ${modelInfo} - 长上下文模型`
  } else if (modelLower.includes('yi')) {
    return `零一万物 ${modelInfo} - 高性能模型`
  }

  // 4. 默认返回
  return `${modelInfo} - AI 大语言模型`
}

const getModuleDisplayName = (moduleName: string) => {
  // 统一与单股分析的中文标签映射（完整的13个报告）
  const nameMap: Record<string, string> = {
    // 分析师团队 (7个) - A股特有：政策分析师、游资追踪师、解禁监控师
    market_report: '📈 市场技术分析',
    sentiment_report: '💭 市场情绪分析',
    news_report: '📰 新闻事件分析',
    fundamentals_report: '💰 基本面分析',
    policy_report: '🏛️ 政策分析师',
    hot_money_report: '🔥 游资追踪师',
    lockup_report: '🔒 解禁监控师',

    // 研究团队 (3个)
    bull_researcher: '🐂 看涨研究员',
    bear_researcher: '🐻 看跌研究员',
    research_team_decision: '🔬 研究经理',

    // 交易团队 (1个)
    trader_investment_plan: '💼 交易员计划',

    // 风险管理团队 (4个)
    risky_analyst: '🔥 激进风险评估',
    safe_analyst: '🛡️ 保守风险评估',
    neutral_analyst: '⚖️ 中性风险评估',
    risk_management_decision: '🎯 风险经理',

    // 最终决策 (1个)
    final_trade_decision: '🎯 最终投资决策',

    // 兼容旧字段
    investment_plan: '📋 投资建议',
    investment_debate_state: '🔬 研究团队（旧）',
    risk_debate_state: '⚖️ 风险管理（旧）',
    detailed_analysis: '📄 详细分析'
  }
  // 未匹配到时，做一个友好的回退：下划线转空格
  return nameMap[moduleName] || moduleName.replace(/_/g, ' ')
}

const renderMarkdown = (content: string) => {
  if (!content) return ''
  try {
    return String(marked.parse(content))
  } catch (e) {
    return `<pre style="white-space: pre-wrap; font-family: inherit;">${content}</pre>`
  }
}

// 专门用于 insight 卡片的内容渲染
// —— 把 AI 生成的中文段落转成清晰易读的 HTML（清洗 Markdown 杂项、分段、加粗）
const renderInsight = (text: string) => {
  if (!text) return '<span class="insight-empty">暂无数据</span>'

  let html = String(text)

  // 预处理 1：跳过分隔线行 (--, ===, --- 等整行)
  html = html.replace(/(^|\n)[\-=_]{2,}(\n|$)/g, '\n')

  // 预处理 2：移除表格行 (Markdown 表格语法: |...|)
  //           连续的表格行整段删除
  html = html.split('\n').map(line => {
    const trimmed = line.trim()
    if (trimmed.startsWith('|') || trimmed.startsWith('｜')) return ''
    // 表格的分隔线行: | --- | --- |
    if (/^\s*\|?\s*:?-+:?\s*\|/.test(line)) return ''
    return line
  }).join('\n')

  // 预处理 3：跳过纯图片/纯链接行
  html = html.split('\n').map(line => {
    const trimmed = line.trim()
    if (trimmed.startsWith('![') && trimmed.includes(']')) return ''
    if (/^https?:\/\/\S+$/.test(trimmed)) return ''
    return line
  }).join('\n')

  // 预处理 4：跳过开头的套话段落
  html = html.replace(/^[\s\S]{0,200}(好的|数据已获取|下面我将|开始分析|尊敬的)[^\n]*\n/, '')

  // 1. 转义 HTML（要在内容清洗之后做，避免破坏标签）
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 2. 处理 **加粗**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 3. 处理行内 `代码`
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // 4. 把 Markdown 标题 (### ## #) 转为加粗的段落小标题
  html = html.split('\n').map(line => {
    const m = line.match(/^#{1,6}\s+(.+)$/)
    if (m) {
      let title = m[1].trim()
      // 清理：去掉 "一、二、" "1. 2." 前缀
      title = title.replace(/^[一二三四五六七八九十][、\.]\s*/, '')
      title = title.replace(/^\d+[\.、]\s*/, '')
      // 清理 emoji 前缀
      title = title.replace(/^[\u{1F000}-\u{1FFFF}]\s*/u, '')
      return `\n\n<strong class="insight-subtitle">${title}</strong>\n\n`
    }
    return line
  }).join('\n')

  // 5. 如果文本没有换行，按中文句号分段
  if (!html.includes('\n')) {
    const sentences = html.split(/([。！？]+)/)
    const paragraphs: string[] = []
    let currentParagraph = ''

    for (let i = 0; i < sentences.length; i += 2) {
      const sentence = sentences[i] + (sentences[i + 1] || '')
      if (sentence.trim()) {
        currentParagraph += sentence
        if (currentParagraph.length > 100) {
          paragraphs.push(currentParagraph.trim())
          currentParagraph = ''
        }
      }
    }
    if (currentParagraph.trim()) {
      paragraphs.push(currentParagraph.trim())
    }
    html = paragraphs.join('\n\n')
  }

  // 6. 按行处理：智能识别段落 / 列表 / 小标题
  const lines = html.split(/\r?\n/)
  const result: string[] = []
  let inList = false
  let currentParagraph = ''

  for (let raw of lines) {
    const line = raw.trim()

    if (!line) {
      // 空行 - 段落分隔
      if (currentParagraph) {
        result.push(`<p class="insight-paragraph">${currentParagraph}</p>`)
        currentParagraph = ''
      }
      if (inList) {
        result.push('</ul>')
        inList = false
      }
      continue
    }

    // 识别小标题行（以 strong/strong 标签开头的）
    const strongMatch = line.match(/^<strong[^>]*>(.+?)<\/strong>/)
    if (strongMatch && line.length <= 80) {
      if (currentParagraph) {
        result.push(`<p class="insight-paragraph">${currentParagraph}</p>`)
        currentParagraph = ''
      }
      if (inList) {
        result.push('</ul>')
        inList = false
      }
      result.push(`<div class="insight-heading">${line}</div>`)
      continue
    }

    // 列表项：1. / 2. / • / - / —
    const listMatch = line.match(/^(\d+[\.、]\s*|[•\-—·]\s*)(.+)/)
    if (listMatch) {
      if (currentParagraph) {
        result.push(`<p class="insight-paragraph">${currentParagraph}</p>`)
        currentParagraph = ''
      }
      if (!inList) {
        result.push('<ul class="insight-list">')
        inList = true
      }
      result.push(`<li>${listMatch[2]}</li>`)
      continue
    }

    // 普通文本 - 累积到当前段落
    if (inList) {
      result.push('</ul>')
      inList = false
    }
    currentParagraph += (currentParagraph ? ' ' : '') + line
  }

  // 处理最后的剩余内容
  if (currentParagraph) {
    result.push(`<p class="insight-paragraph">${currentParagraph}</p>`)
  }
  if (inList) {
    result.push('</ul>')
  }

  return result.join('\n')
}

// 渲染完整洞察内容（用于 popover 显示）
const renderInsightFull = (text: string) => {
  if (!text) return '<span class="insight-empty">暂无数据</span>'
  
  // 使用 renderInsight 的逻辑，但不截断
  let html = String(text)
  
  // 预处理：跳过分隔线行
  html = html.replace(/(^|\n)[\-=_]{2,}(\n|$)/g, '\n')
  
  // 移除表格行
  html = html.split('\n').map(line => {
    const trimmed = line.trim()
    if (trimmed.startsWith('|') || trimmed.startsWith('｜')) return ''
    if (/^\s*\|?\s*:?-+:?\s*\|/.test(line)) return ''
    return line
  }).join('\n')
  
  // 跳过纯图片/纯链接行
  html = html.split('\n').map(line => {
    const trimmed = line.trim()
    if (trimmed.startsWith('![') && trimmed.includes(']')) return ''
    if (/^https?:\/\/\S+$/.test(trimmed)) return ''
    return line
  }).join('\n')
  
  // 跳过开头的套话段落
  html = html.replace(/^[\s\S]{0,200}(好的|数据已获取|下面我将|开始分析|尊敬的)[^\n]*\n/, '')
  
  // 转义 HTML
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 处理 Markdown 加粗
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>')
  
  // 处理行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  
  // 把 Markdown 标题转为加粗的段落小标题
  html = html.split('\n').map(line => {
    const m = line.match(/^#{1,6}\s+(.+)$/)
    if (m) {
      let title = m[1].trim()
      title = title.replace(/^[一二三四五六七八九十][、\.]\s*/, '')
      title = title.replace(/^\d+[\.、]\s*/, '')
      title = title.replace(/^[\u{1F000}-\u{1FFFF}]\s*/u, '')
      return `\n\n<div class="insight-heading-full">${title}</div>\n`
    }
    return line
  }).join('\n')
  
  // 按行处理：智能识别段落 / 列表
  const lines = html.split(/\r?\n/)
  const result: string[] = []
  let inList = false
  let currentParagraph = ''
  
  for (let raw of lines) {
    const line = raw.trim()
    
    if (!line) {
      if (currentParagraph) {
        result.push(`<p class="insight-paragraph-full">${currentParagraph}</p>`)
        currentParagraph = ''
      }
      if (inList) {
        result.push('</ul>')
        inList = false
      }
      continue
    }
    
    // 检查是否是列表项
    const listMatch = line.match(/^([\-\*\•]|\d+[\.、])\s+(.+)$/)
    if (listMatch) {
      if (currentParagraph) {
        result.push(`<p class="insight-paragraph-full">${currentParagraph}</p>`)
        currentParagraph = ''
      }
      if (!inList) {
        result.push('<ul class="insight-list-full">')
        inList = true
      }
      result.push(`<li>${listMatch[2]}</li>`)
      continue
    }
    
    // 普通文本 - 累积到当前段落
    if (inList) {
      result.push('</ul>')
      inList = false
    }
    currentParagraph += (currentParagraph ? ' ' : '') + line
  }
  
  // 处理最后的剩余内容
  if (currentParagraph) {
    result.push(`<p class="insight-paragraph-full">${currentParagraph}</p>`)
  }
  if (inList) {
    result.push('</ul>')
  }
  
  return result.join('\n')
}

// 置信度评分相关函数
// 将后端返回的 0-1 小数转换为 0-100 的百分制
const normalizeConfidenceScore = (score: number) => {
  // 如果已经是 0-100 的范围，直接返回
  if (score > 1) {
    return Math.round(score)
  }
  // 如果是 0-1 的小数，转换为百分制
  return Math.round(score * 100)
}

const getConfidenceColor = (score: number) => {
  if (score >= 80) return '#67C23A' // 较高 - 绿色
  if (score >= 60) return '#409EFF' // 中上 - 蓝色
  if (score >= 40) return '#E6A23C' // 中等 - 橙色
  return '#F56C6C' // 较低 - 红色
}

const getConfidenceLabel = (score: number) => {
  if (score >= 80) return '较高'
  if (score >= 60) return '中上'
  if (score >= 40) return '中等'
  return '较低'
}

// 风险等级相关函数
const getRiskStars = (riskLevel: string) => {
  const riskMap: Record<string, number> = {
    '低': 1,
    '中低': 2,
    '中等': 3,
    '中高': 4,
    '高': 5
  }
  return riskMap[riskLevel] || 3
}

const getRiskColor = (riskLevel: string) => {
  const colorMap: Record<string, string> = {
    '低': '#67C23A',      // 绿色
    '中低': '#95D475',    // 浅绿色
    '中等': '#E6A23C',    // 橙色
    '中高': '#F56C6C',    // 红色
    '高': '#F56C6C'       // 深红色
  }
  return colorMap[riskLevel] || '#E6A23C'
}

// 工具函数：从 report 或其 decision / reports 子对象中取值
// —— 优先取 report 顶层（后端 extract_structured_fields 已经处理好了）
// —— 取不到时，直接从对应模块的文本中截取
const pickField = (report: any, candidates: string[], maxChars: number = 1200): any => {
  if (!report) return null

  // 1) 先在顶层 / decision / reports 中找精确字段名
  const directSources = [report, report.decision || {}, report.reports || {}]
  for (const src of directSources) {
    if (!src || typeof src !== 'object') continue
    for (const key of candidates) {
      const v = src[key]
      if (v !== null && v !== undefined && v !== '' && v !== 'None') {
        return v
      }
    }
  }

  // 2) 在 reports 所有文本型模块中搜索"章节标题"匹配
  const moduleMap = report.reports || {}
  const moduleTexts = Object.values(moduleMap).filter(v => typeof v === 'string')
  for (const moduleText of moduleTexts) {
    for (const key of candidates) {
      try {
        const re = new RegExp(
          '(?:^|\\n)[#*_]*\\s*(?:\\d+[.、]\\s*)?' + key.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&') +
          '[*_]*\\s*[:：]?\\s*(?:\\n|[:：])?\\s*([\\s\\S]{0,' + maxChars + '}?)(?=\\n\\s*#+|\\n\\s*\\n|$)',
        )
        const m = moduleText.match(re)
        if (m && m[1] && m[1].trim()) {
          return m[1].trim().substring(0, maxChars)
        }
      } catch (e) {
        continue
      }
    }
  }

  // 3) 终极回退：从对应模块直接截取内容（最保险）
  // 注意：每个字段使用不同的优先模块，避免重复
  const fallbackMap: { [key: string]: string[] } = {
    '核心洞察': ['final_trade_decision', 'research_team_decision'],
    '投资逻辑': ['investment_plan', 'trader_investment_plan', 'bull_researcher', 'bear_researcher'],
    '趋势预测': ['market_report', 'trader_investment_plan'],
    '策略点位': ['trader_investment_plan', 'investment_plan'],
    '情绪分析': ['sentiment_report', 'news_report', 'hot_money_report'],
    '市场情绪': ['sentiment_report', 'news_report', 'hot_money_report'],
    '舆情分析': ['sentiment_report', 'news_report'],
    '情绪面分析': ['sentiment_report', 'news_report'],
    '风险提示': ['risk_management_decision', 'risky_analyst', 'safe_analyst', 'neutral_analyst'],
  }

  const smartTruncate = (text: string, limit: number): string => {
    if (!text) return ''
    // 第一步：逐行清洗
    const skipList = ['数据已获取', '下面我将', '分析报告', '分析时段', '参考日期', '报告', '总结如下']
    const rawLines = text.trim().split('\n')
    const cleanedLines: string[] = []
    for (const ln of rawLines) {
      const stripped = ln.trim()
      if (!stripped) continue
      // 跳过分隔线
      if (/^[-=_]{2,}$/.test(stripped)) continue
      // 跳过表格行
      if (stripped.startsWith('|') || stripped.startsWith('｜')) continue
      // 跳过 markdown 标题
      if (/^#{1,6}\s+/.test(stripped)) continue
      // 跳过套话行
      let skipLine = false
      for (const pat of skipList) {
        if (stripped.includes(pat) && stripped.length < 120) {
          skipLine = true
          break
        }
      }
      if (skipLine) continue
      // 移除 **/emoji/列表标记
      let cleaned = stripped
        .replace(/\*+/g, '')
        .replace(/^[\u{1F000}-\u{1FFFF}]\s*/u, '')
        .replace(/^(\d+[\.、]\s*|[•\-—·]\s*)/, '')
        .trim()
      if (cleaned.length < 8 && !/[。！？：]/.test(cleaned)) continue
      cleanedLines.push(cleaned)
    }

    // 第二步：合并成段落
    const paragraph = cleanedLines.join(' ')
      .replace(/\s{2,}/g, ' ').trim()

    if (paragraph.length <= limit) return paragraph

    // 第三步：句子级挑选（短限制 = 更激进）
    if (limit <= 350) {
      // 拆分成句子
      const parts = paragraph.split(/([。！？；])/)
      const sentences: string[] = []
      for (let i = 0; i < parts.length - 1; i += 2) {
        const sent = (parts[i] + parts[i + 1]).trim()
        if (sent.length >= 10) sentences.push(sent)
      }
      // 处理最后一句（无标点）
      if (parts.length % 2 === 1 && parts[parts.length - 1].trim().length >= 10) {
        sentences.push(parts[parts.length - 1].trim())
      }
      if (sentences.length === 0) {
        // 没有句号，按字符截断
        return paragraph.substring(0, limit)
      }
      // 评分 + 挑选
      const highValueKws = ['结论', '核心', '总结', '主要', '建议', '看好', '买入', '卖出',
        '评级', '预测', '趋势', '风险', '关键', '显著', '拐点', '确立', '利好', '利空',
        '正面', '负面', '机会', '信号', '逻辑', '重点']
      const scored = sentences.map((s, idx) => {
        let score = 0
        for (const kw of highValueKws) if (s.includes(kw)) score += 10
        score += Math.max(0, 10 - idx) // 靠前加分
        if (s.length < 12) score -= 5
        return { score, sent: s, idx }
      })
      // 按评分挑选句子，保持原顺序
      scored.sort((a, b) => b.score - a.score)
      const selected: number[] = []
      let total = 0
      for (const item of scored) {
        if (total + item.sent.length <= limit) {
          selected.push(item.idx)
          total += item.sent.length
          if (total >= limit - 20) break
        }
      }
      if (selected.length < 2) {
        // 不足2句，按顺序补充
        for (let i = 0; i < sentences.length; i++) {
          if (selected.includes(i)) continue
          if (total + sentences[i].length <= limit) {
            selected.push(i)
            total += sentences[i].length
            if (selected.length >= 3) break
          }
        }
      }
      selected.sort((a, b) => a - b)
      const resultText = selected.map(i => sentences[i]).join('')
      if (resultText.length > limit) {
        const pos = resultText.lastIndexOf('。', limit)
        if (pos > limit / 2) return resultText.substring(0, pos + 1)
        return resultText.substring(0, limit)
      }
      return resultText
    }

    // 长限制：保留段落，在句号处截断
    const pos = paragraph.lastIndexOf('。', limit)
    if (pos > limit / 2) return paragraph.substring(0, pos + 1)
    return paragraph.substring(0, limit)
  }

  for (const key of candidates) {
    const moduleKeys = fallbackMap[key]
    if (!moduleKeys) continue
    for (const mk of moduleKeys) {
      const text = moduleMap[mk]
      if (typeof text === 'string' && text.trim()) {
        return smartTruncate(text, maxChars)
      }
    }
  }

  // 4) 最后兜底：从所有模块中找第一个有内容的
  for (const v of Object.values(moduleMap)) {
    if (typeof v === 'string' && v.trim() && v.trim().length > 20) {
      return smartTruncate(v, Math.min(maxChars, 500))
    }
  }

  return null
}

const formatPriceValue = (report: any, candidates: string[]): string => {
  const val = pickField(report, candidates)
  if (val === null || val === undefined || val === '') return '--'
  
  let num: number | null = null
  
  if (typeof val === 'number') {
    num = val
  } else if (typeof val === 'string') {
    const cleaned = val.replace(/[¥$￥,，]/g, '').trim()
    const match = cleaned.match(/^\s*(\d+(\.\d+)?)\s*$/)
    if (match) {
      num = parseFloat(match[1])
    } else {
      const found = cleaned.match(/(\d+(\.\d+)?)/)
      if (found) {
        num = parseFloat(found[1])
      }
    }
  }
  
  if (num !== null && !isNaN(num)) {
    return num.toFixed(2)
  }
  return '--'
}

const formatPct = (val: any): string => {
  if (val === null || val === undefined || val === '') return '0'
  const num = Number(val)
  if (isNaN(num)) return String(val)
  if (num <= 1) return Math.round(num * 100).toString()
  return Math.round(num).toString()
}

const hasAnyScore = (report: any): boolean => {
  const keys = ['置信度', 'confidence', 'confidence_score',
    '技术面评分', 'technical_score',
    '基本面评分', 'fundamental_score',
    '情绪面评分', 'sentiment_score',
    '政策面评分', 'policy_score',
    '风险等级', 'risk_level']
  return keys.some(k => pickField(report, [k]) !== null)
}

// 洞察文本是否存在
const hasAnyInsight = (report: any): boolean => {
  const keys = ['核心洞察', '投资逻辑', '趋势预测', '策略点位', '风险提示', '情绪分析']
  return keys.some(k => pickField(report, [k]) !== null)
}

// 6 类洞察卡片的统一数据（新增情绪分析，保持对称）
const insightItems = computed(() => {
  if (!report.value) return []
  const defs = [
    { key: 'core',       title: '核心洞察', icon: '💡',
      subtitle: '一句话把握报告要点',
      candidates: ['核心洞察'],
      maxChars: 400,
      tooltip: '模型从所有分析维度中提炼的最具代表性结论，通常是影响评级与操作建议的核心原因。',
    },
    { key: 'logic',      title: '投资逻辑', icon: '📊',
      subtitle: '为什么看好或看空',
      candidates: ['投资逻辑'],
      maxChars: 400,
      tooltip: 'AI 对该标的给出买入/持有/卖出建议的底层依据，综合公司基本面、行业周期、估值与市场情绪等信息。',
    },
    { key: 'sentiment',  title: '情绪分析', icon: '🔥',
      subtitle: '市场情绪与舆论热度',
      candidates: ['情绪分析', '市场情绪', '舆情分析', '情绪面分析'],
      maxChars: 400,
      tooltip: '基于新闻热度、社交媒体讨论、资金流向（北向资金、主力净流入）、板块热度等信息得出的市场情绪判断。',
    },
    { key: 'trend',      title: '趋势预测', icon: '📈',
      subtitle: '短期 / 中期走势判断',
      candidates: ['趋势预测'],
      maxChars: 400,
      tooltip: '基于技术指标与近期行情的方向性判断。仅作参考，不构成投资建议——实际走势受宏观消息、资金流向等多重因素影响。',
    },
    { key: 'strategy',   title: '策略点位', icon: '🎯',
      subtitle: '入场 / 加仓 / 离场参考',
      candidates: ['策略点位'],
      maxChars: 400,
      tooltip: '与上方价格卡片互为补充，提供交易上的具体执行建议，包括理想买入区间、加仓位置、止损止盈参考线。',
    },
    { key: 'risk',       title: '风险提示', icon: '⚠️',
      subtitle: '需要重点关注的风险',
      candidates: ['风险提示'],
      maxChars: 400,
      tooltip: '可能影响投资结果的风险因素，例如行业政策变化、财报不及预期、估值偏高、市场波动放大、流动性风险等。',
    },
  ]
  const result = defs
    .map(d => {
      // 获取完整内容：优先从后端的 _full 字段获取，否则从 report 模块中直接取
      let fullText = null
      for (const key of d.candidates) {
        const fullKey = key + '_full'
        const v = report.value?.[fullKey]
        if (v !== null && v !== undefined && v !== '' && v !== 'None') {
          fullText = v
          break
        }
      }
      // 如果没有 _full 字段，尝试从原始 report 模块中提取完整内容
      if (!fullText) {
        const moduleMap = report.value?.reports || {}
        const fallbackMap: { [key: string]: string[] } = {
          '核心洞察': ['final_trade_decision', 'research_team_decision', 'trader_investment_plan'],
          '投资逻辑': ['investment_plan', 'trader_investment_plan', 'research_team_decision', 'final_trade_decision'],
          '趋势预测': ['market_report', 'trader_investment_plan', 'final_trade_decision'],
          '策略点位': ['trader_investment_plan', 'investment_plan', 'final_trade_decision'],
          '情绪分析': ['sentiment_report', 'news_report', 'hot_money_report', 'market_report'],
          '市场情绪': ['sentiment_report', 'news_report', 'hot_money_report'],
          '舆情分析': ['sentiment_report', 'news_report'],
          '情绪面分析': ['sentiment_report', 'news_report'],
          '风险提示': ['risk_management_decision', 'risky_analyst', 'safe_analyst', 'neutral_analyst', 'final_trade_decision'],
        }
        for (const key of d.candidates) {
          const moduleKeys = fallbackMap[key] || []
          for (const mk of moduleKeys) {
            const moduleText = moduleMap[mk]
            if (typeof moduleText === 'string' && moduleText.trim()) {
              // 从模块中提取匹配字段的内容（最多400字）
              const re = new RegExp(
                '(?:^|\\n)[#*_]*\\s*(?:\\d+[.、]\\s*)?' + key.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&') +
                '[*_]*\\s*[:：]?\\s*(?:\\n|[:：])?\\s*([\\s\\S]{0,' + d.maxChars + '}?)(?=\\n\\s*#+|\\n\\s*\\n|$)',
              )
              const m = moduleText.match(re)
              if (m && m[1] && m[1].trim()) {
                fullText = m[1].trim()
                break
              }
            }
          }
          if (fullText) break
        }
      }
      // 最终兜底：如果还是没有，使用原有的截断内容
      if (!fullText) {
        fullText = pickField(report.value, d.candidates, d.maxChars || 400)
      }
      return { ...d, fullText }
    })
    .filter(d => d.fullText !== null && d.fullText !== undefined && d.fullText !== '')
  return result
})

// 多维度评分卡片的统一数据
const dimensionItems = computed(() => {
  if (!report.value) return []

  // 统一配色 + 分级标签（越高越积极）
  const scoreMeta = (v: number) => {
    if (v >= 80) return { color: ['#22c55e', '#4ade80', '#86efac'], label: '优秀 / 强势' }
    if (v >= 65) return { color: ['#3b82f6', '#60a5fa', '#93c5fd'], label: '良好' }
    if (v >= 50) return { color: ['#0ea5e9', '#38bdf8', '#7dd3fc'], label: '中性偏正面' }
    if (v >= 35) return { color: ['#f59e0b', '#fbbf24', '#fcd34d'], label: '中性' }
    return { color: ['#ef4444', '#f87171', '#fca5a5'], label: '偏弱 / 需警惕' }
  }

  const items: any[] = []

  const confVal = pickField(report.value, ['置信度', 'confidence', 'confidence_score'])
  if (confVal !== null) {
    const v = Math.round(Number(confVal) <= 1 ? Number(confVal) * 100 : Number(confVal))
    const meta = scoreMeta(v)
    items.push({
      key: 'confidence', name: '置信度', icon: '🎯',
      subtitle: '模型对本次结论的信心',
      type: 'progress', value: v, color: meta.color, label: meta.label,
      tooltip: '模型综合各维度证据的一致性、数据完整度、历史回测表现得出的置信度。越高表示模型对结论的把握越强，但不代表实际收益的确定性。',
    })
  }

  const techVal = pickField(report.value, ['技术面评分', 'technical_score'])
  if (techVal !== null) {
    const v = Math.round(Number(techVal) <= 1 ? Number(techVal) * 100 : Number(techVal))
    const meta = scoreMeta(v)
    items.push({
      key: 'technical', name: '技术面', icon: '📊',
      subtitle: 'K 线 / 均线 / MACD / RSI',
      type: 'progress', value: v, color: meta.color, label: meta.label,
      tooltip: '综合 K 线形态、MA/EMA 均线排列、MACD 金叉死叉、RSI 强弱、BOLL 轨道位置、成交量变化等指标得出的技术形态评分。',
    })
  }

  const fundVal = pickField(report.value, ['基本面评分', 'fundamental_score'])
  if (fundVal !== null) {
    const v = Math.round(Number(fundVal) <= 1 ? Number(fundVal) * 100 : Number(fundVal))
    const meta = scoreMeta(v)
    items.push({
      key: 'fundamental', name: '基本面', icon: '💰',
      subtitle: '营收 / 利润 / 估值 / 行业',
      type: 'progress', value: v, color: meta.color, label: meta.label,
      tooltip: '公司营收、利润增长、ROE、毛利率、资产质量、PE/PB 估值水平、行业地位与竞争格局的综合评分，体现企业内在价值的健康度。',
    })
  }

  const sentVal = pickField(report.value, ['情绪面评分', 'sentiment_score'])
  if (sentVal !== null) {
    const v = Math.round(Number(sentVal) <= 1 ? Number(sentVal) * 100 : Number(sentVal))
    const meta = scoreMeta(v)
    items.push({
      key: 'sentiment', name: '情绪面', icon: '🔥',
      subtitle: '新闻 / 舆论 / 资金情绪',
      type: 'progress', value: v, color: meta.color, label: meta.label,
      tooltip: '基于新闻正面度、社交媒体讨论、资金流向（北向资金、主力净流入）、板块热度等信息得出的市场情绪评分。高分代表情绪整体积极。',
    })
  }

  const policyVal = pickField(report.value, ['政策面评分', 'policy_score'])
  if (policyVal !== null) {
    const v = Math.round(Number(policyVal) <= 1 ? Number(policyVal) * 100 : Number(policyVal))
    const meta = scoreMeta(v)
    items.push({
      key: 'policy', name: '政策面', icon: '🏛️',
      subtitle: '监管 / 行业 / 宏观政策',
      type: 'progress', value: v, color: meta.color, label: meta.label,
      tooltip: '监管政策、行业扶持或限制、利率与汇率政策、财政政策等对该标的所在行业的直接与间接影响评估。',
    })
  }

  const riskVal = pickField(report.value, ['风险等级', 'risk_level'])
  if (riskVal !== null) {
    const starMap: Record<string, number> = { '低': 1, '中低': 2, '中等': 3, '中高': 4, '高': 5 }
    const stars = starMap[String(riskVal)] ?? 3
    const colorMap: Record<number, string> = {
      1: '#22c55e', 2: '#84cc16', 3: '#f59e0b', 4: '#f97316', 5: '#ef4444'
    }
    const labelMap: Record<number, string> = {
      1: '可控风险', 2: '风险偏低', 3: '风险一般', 4: '风险偏高', 5: '风险较高'
    }
    items.push({
      key: 'risk', name: '风险等级', icon: '🛡️',
      subtitle: '波动性 / 流动性 / 不确定性',
      type: 'stars', stars, text: String(riskVal),
      starColor: colorMap[stars] ?? '#f59e0b', label: labelMap[stars] ?? '风险一般',
      tooltip: '综合标的历史波动、个股流动性、行业政策不确定性、财报披露风险与宏观敏感度得出的风险评级。仅供参考，不构成风险控制建议。',
    })
  }

  return items
})

// 根据评级/操作建议决定标签颜色
const getDecisionActionTagType = (action: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  if (!action) return 'info'
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    '强烈买入': 'success',
    '买入': 'success',
    '持有': 'warning',
    '观望': 'info',
    '减仓': 'danger',
    '卖出': 'danger',
  }
  for (const k of Object.keys(map)) {
    if (action.includes(k)) return map[k]
  }
  return 'info'
}

watch(
  () => route.params.id,
  async () => {
    report.value = null
    activeModule.value = ''
    await fetchLLMConfigs()
    await fetchReportDetail()
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.report-detail {
  .loading-container {
    padding: 24px;
  }

  .report-content {
    .report-header {
      margin-bottom: 24px;

      .header-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;

        .title-section {
          .report-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 12px 0;
          }

          .report-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;

            .meta-item {
              display: flex;
              align-items: center;
              gap: 4px;
              color: var(--el-text-color-regular);
              font-size: 14px;
            }
          }
        }

        .action-section {
          display: flex;
          gap: 8px;
        }
      }
    }

    /* 风险提示样式 */
    .risk-disclaimer {
      margin-bottom: 24px;
      animation: fadeInDown 0.5s ease-out;
    }

    .risk-disclaimer :deep(.el-alert) {
      background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
      border: 2px solid #ffc107;
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
    }

    .risk-disclaimer :deep(.el-alert__icon) {
      font-size: 24px;
      color: #ff6b00;
    }

    .disclaimer-content {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 15px;
      line-height: 1.6;
    }

    .disclaimer-icon {
      font-size: 24px;
      color: #ff6b00;
      flex-shrink: 0;
      animation: pulse 2s ease-in-out infinite;
    }

    .disclaimer-text {
      color: #856404;
      flex: 1;
    }

    .disclaimer-text strong {
      color: #d63031;
      font-size: 16px;
      font-weight: 700;
    }

    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
        opacity: 1;
      }
      50% {
        transform: scale(1.1);
        opacity: 0.8;
      }
    }

    @keyframes fadeInDown {
      from {
        opacity: 0;
        transform: translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .summary-card,
    .strategy-card,
    .metrics-card,
    .modules-card {
      margin-bottom: 24px;

      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;

        .header-tip {
          font-size: 12.5px;
          font-weight: 400;
          color: #9ca3af;
          margin-left: 8px;
        }
      }
    }

    /* daily_stock_analysis 风格的策略点位卡片 */
    .strategy-card {
      .strategy-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 20px;

        @media (max-width: 768px) {
          grid-template-columns: repeat(2, 1fr);
        }
      }

      .price-block {
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid var(--el-border-color-lighter);
        background: var(--el-fill-color-light);

        &.buy-block { background: linear-gradient(135deg, rgba(232, 245, 233, 0.6) 0%, rgba(187, 247, 208, 0.3) 100%); border-color: #a5d6a7; }
        &.add-block { background: linear-gradient(135deg, rgba(225, 245, 254, 0.6) 0%, rgba(186, 230, 253, 0.3) 100%); border-color: #81d4fa; }
        &.stop-block { background: linear-gradient(135deg, rgba(254, 226, 226, 0.6) 0%, rgba(252, 165, 165, 0.3) 100%); border-color: #ef9a9a; }
        &.target-block { background: linear-gradient(135deg, rgba(255, 243, 224, 0.6) 0%, rgba(255, 213, 128, 0.3) 100%); border-color: #ffb74d; }
        &.support-block { background: linear-gradient(135deg, rgba(237, 231, 246, 0.6) 0%, rgba(206, 188, 228, 0.3) 100%); border-color: #b39ddb; }
        &.resistance-block { background: linear-gradient(135deg, rgba(255, 235, 238, 0.6) 0%, rgba(244, 194, 194, 0.3) 100%); border-color: #e57373; }
      }

      .price-label {
        font-size: 13px;
        color: var(--el-text-color-regular);
        font-weight: 500;
        margin-bottom: 8px;
      }

      .price-value {
        font-size: 22px;
        font-weight: 700;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
        letter-spacing: 0.5px;
      }

      .price-sub {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }

      /* ========== 核心洞察 & 多维度评分 公共区块标题 */
      .block-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        .block-title-text {
          font-size: 17px;
          font-weight: 700;
          color: #111827;
          letter-spacing: 0.3px;
        }

        .help-icon {
          color: #9ca3af;
          cursor: help;
          margin-left: 4px;
        }
      }

      /* ========== 核心洞察卡片容器 */
      .insights-block {
        margin: 24px 0;
        padding: 22px 22px 8px;
        background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
        border-radius: 14px;
        border: 1px solid var(--el-border-color-lighter);

        .insight-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
          padding-bottom: 16px;

          @media (max-width: 1024px) {
            grid-template-columns: repeat(2, 1fr);
          }
          @media (max-width: 640px) {
            grid-template-columns: 1fr;
          }
        }
      }

      .insight-card {
        position: relative;
        padding: 22px 22px 20px;
        border-radius: 16px;
        overflow: hidden;
        cursor: default;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.35s ease;
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.03);
        background: #fff;

        /* 顶部装饰圆 */
        &::before {
          content: '';
          position: absolute;
          top: -60px;
          right: -60px;
          width: 180px;
          height: 180px;
          border-radius: 50%;
          opacity: 0.08;
          pointer-events: none;
        }

        /* 左侧装饰条 */
        &::after {
          content: '';
          position: absolute;
          top: 22px;
          left: 0;
          width: 4px;
          height: 40px;
          border-radius: 0 4px 4px 0;
        }

        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.10), 0 2px 6px rgba(15, 23, 42, 0.04);
          border-color: rgba(99, 102, 241, 0.18);
        }

        .insight-card-header {
          display: flex;
          align-items: center;
          gap: 14px;
          margin-bottom: 16px;
          padding: 0 0 14px;
          border-bottom: 1px solid rgba(15, 23, 42, 0.05);
          position: relative;

          .insight-card-icon {
            width: 52px;
            height: 52px;
            flex: 0 0 52px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 14px;
            font-size: 28px;
            box-shadow: inset 0 -2px 4px rgba(0, 0, 0, 0.04);
          }

          .insight-card-text-wrap {
            flex: 1;
            min-width: 0;
          }

          .insight-card-title {
            font-size: 17px;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: 0.2px;
            line-height: 1.2;
          }

          .insight-card-subtitle {
            font-size: 13px;
            color: #64748b;
            margin-top: 5px;
            font-weight: 400;
          }
        }

        .insight-card-body {
          flex: 1;
          font-size: 14.5px;
          line-height: 1.85;
          color: #334155;
          word-break: break-word;
          position: relative;

          .insight-empty {
            color: #94a3b8;
            font-style: italic;
            font-size: 13.5px;
          }

          .insight-heading {
            font-size: 15px;
            font-weight: 700;
            color: #1e293b;
            margin: 14px 0 10px;
            padding-bottom: 6px;
            border-bottom: 2px solid rgba(100, 116, 139, 0.12);

            strong {
              background: none;
              padding: 0;
              color: inherit;
              font-weight: inherit;
            }
          }

          .insight-paragraph {
            margin: 0 0 12px;

            &:last-child {
              margin-bottom: 0;
            }
          }

          .insight-list {
            margin: 6px 0 12px;
            padding-left: 20px;

            li {
              margin-bottom: 6px;
              line-height: 1.8;
              font-size: 14px;
            }
          }

          // 悬停查看完整内容提示
          .insight-expand-hint {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-top: 14px;
            padding: 10px 14px;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(96, 165, 250, 0.12) 100%);
            border-radius: 8px;
            font-size: 13px;
            color: #3b82f6;
            font-weight: 500;
            border: 1px solid rgba(59, 130, 246, 0.15);
          }

          strong {
            color: #0f172a;
            font-weight: 600;
            background: linear-gradient(transparent 70%, rgba(250, 204, 21, 0.35) 70%);
            padding: 0 2px;
          }

          code {
            background: rgba(15, 23, 42, 0.04);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            color: #1e293b;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", monospace;
          }
        }

        /* 每张卡片的专属配色 */
        &.insight-core {
          background: linear-gradient(155deg, #fffbeb 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #fef3c7, #fde68a);
          }
          .insight-card-title { color: #92400e; }

          &::before { background: #f59e0b; }
          &::after  { background: linear-gradient(180deg, #f59e0b, #fbbf24); }
        }

        &.insight-logic {
          background: linear-gradient(155deg, #eff6ff 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #dbeafe, #bfdbfe);
          }
          .insight-card-title { color: #1e3a8a; }

          &::before { background: #3b82f6; }
          &::after  { background: linear-gradient(180deg, #3b82f6, #60a5fa); }
        }

        &.insight-sentiment {
          background: linear-gradient(155deg, #fdf2f8 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #fce7f3, #fbcfe8);
          }
          .insight-card-title { color: #9d174d; }

          &::before { background: #ec4899; }
          &::after  { background: linear-gradient(180deg, #ec4899, #f472b6); }
        }

        &.insight-trend {
          background: linear-gradient(155deg, #ecfdf5 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #d1fae5, #a7f3d0);
          }
          .insight-card-title { color: #065f46; }

          &::before { background: #10b981; }
          &::after  { background: linear-gradient(180deg, #10b981, #34d399); }
        }

        &.insight-strategy {
          background: linear-gradient(155deg, #f5f3ff 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #e9d5ff, #d8b4fe);
          }
          .insight-card-title { color: #5b21b6; }

          &::before { background: #8b5cf6; }
          &::after  { background: linear-gradient(180deg, #8b5cf6, #a78bfa); }
        }

        &.insight-risk {
          background: linear-gradient(155deg, #fef2f2 0%, #ffffff 55%);

          .insight-card-icon {
            background: linear-gradient(145deg, #fee2e2, #fecaca);
          }
          .insight-card-title { color: #991b1b; }

          &::before { background: #ef4444; }
          &::after  { background: linear-gradient(180deg, #ef4444, #f87171); }
        }
      }

      /* ========== 多维度评分卡片 */
      .dimension-block {
        margin: 24px 0;
        padding: 22px 22px 8px;
        background: linear-gradient(135deg, #f8fafc 0%, #fef3c7 100%);
        border-radius: 14px;
        border: 1px solid var(--el-border-color-lighter);

        .dimension-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          padding-bottom: 14px;

          @media (max-width: 768px) {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .dimension-card {
          background: #fff;
          border-radius: 12px;
          padding: 18px 18px 14px;
          border: 1px solid var(--el-border-color-lighter);
          box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
          transition: box-shadow 0.3s ease, transform 0.3s ease, border-color 0.3s ease;
          cursor: default;
          position: relative;
          overflow: hidden;

          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: currentColor;
            opacity: 0.9;
          }

          &:hover {
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.10);
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.25);
          }

          .dimension-card-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;

            .dimension-icon {
              font-size: 22px;
              width: 38px;
              height: 38px;
              flex: 0 0 38px;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 10px;
              background: #f8fafc;
            }

            .dimension-text-wrap {
              flex: 1;
              min-width: 0;
            }

            .dimension-name {
              font-size: 15px;
              font-weight: 700;
              color: #111827;
              letter-spacing: 0.3px;
            }

            .dimension-subtitle {
              font-size: 12px;
              color: #6b7280;
              margin-top: 3px;
            }
          }

          .dimension-progress {
            margin: 10px 0 6px;
          }

          .dimension-risk {
            display: flex;
            gap: 5px;
            margin: 10px 0 6px;

            .risk-star {
              font-size: 20px;
              transition: transform 0.2s ease, color 0.2s ease;

              &.active {
                animation: dimStarPulse 0.6s ease-in-out;
              }
            }
          }

          .dimension-value {
            margin-top: 6px;

            .score-number {
              font-size: 28px;
              font-weight: 700;
              color: #111827;
              letter-spacing: 0.3px;
            }

            .score-unit {
              font-size: 13px;
              color: #6b7280;
              margin-left: 4px;
            }
          }

          .dimension-label {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: 6px;
            font-size: 13px;
            font-weight: 600;
          }

          &.dim-confidence { color: #f59e0b; .dimension-icon { background: #fff7ed; } }
          &.dim-technical  { color: #3b82f6; .dimension-icon { background: #eff6ff; } }
          &.dim-fundamental{ color: #10b981; .dimension-icon { background: #ecfdf5; } }
          &.dim-sentiment  { color: #ec4899; .dimension-icon { background: #fdf2f8; } }
          &.dim-policy     { color: #8b5cf6; .dimension-icon { background: #f5f3ff; } }
          &.dim-risk       { color: #ef4444; .dimension-icon { background: #fef2f2; } }
        }
      }

      @keyframes dimStarPulse {
        0%, 100% { transform: scale(1); }
        50%      { transform: scale(1.15); }
      }

      /* ========== 区块内卡片图标与颜色统一 */
      .insight-card .insight-card-icon,
      .dimension-card .dimension-icon {
        text-align: center;
      }
    }

    .summary-content {
      line-height: 1.6;
      color: var(--el-text-color-primary);
    }

    .metrics-content {
      .metric-item {
        text-align: center;
        padding: 24px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 12px;
        background: var(--el-fill-color-blank);
        transition: all 0.3s ease;

        &:hover {
          box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .metric-label {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          font-size: 15px;
          font-weight: 500;
          color: var(--el-text-color-regular);
          margin-bottom: 16px;

          .el-icon {
            font-size: 18px;
          }
        }

        .metric-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-color-primary);
        }

        .recommendation-value {
          font-size: 16px;
          line-height: 1.6;
          color: var(--el-text-color-primary);
        }
      }

      // 置信度评分样式
      .confidence-item {
        .confidence-display {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;

          .el-progress {
            margin-bottom: 8px;
          }

          .confidence-text {
            display: flex;
            flex-direction: column;
            align-items: center;
            line-height: 1;

            .confidence-number {
              font-size: 32px;
              font-weight: 700;
            }

            .confidence-unit {
              font-size: 14px;
              margin-top: 4px;
              opacity: 0.8;
            }
          }

          .confidence-label {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }
        }
      }

      // 风险等级样式
      .risk-item {
        .risk-display {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;

          .risk-stars {
            display: flex;
            gap: 8px;
            font-size: 28px;

            .star-icon {
              color: #DCDFE6;
              transition: all 0.3s ease;

              &.active {
                color: #F7BA2A;
                animation: starPulse 0.6s ease-in-out;
              }
            }
          }

          .risk-label {
            font-size: 18px;
            font-weight: 700;
            margin-top: 4px;
          }

          .risk-description {
            font-size: 13px;
            color: var(--el-text-color-secondary);
            text-align: center;
            line-height: 1.4;
            max-width: 200px;
          }
        }
      }

      .key-points {
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid var(--el-border-color-lighter);

        h4 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);

          .el-icon {
            font-size: 18px;
            color: var(--el-color-primary);
          }
        }

        ul {
          margin: 0;
          padding: 0;
          list-style: none;

          li {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-bottom: 12px;
            padding: 12px;
            background: var(--el-fill-color-light);
            border-radius: 8px;
            line-height: 1.6;
            transition: all 0.2s ease;

            &:hover {
              background: var(--el-fill-color);
            }

            .point-icon {
              flex-shrink: 0;
              margin-top: 2px;
              font-size: 16px;
              color: var(--el-color-success);
            }
          }
        }
      }
    }

    // 星星脉冲动画
    @keyframes starPulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.2);
      }
    }

    .module-content {
      /* 报告模块内容的统一 markdown-body 样式 */
      .markdown-body {
        font-size: 15px;
        line-height: 1.9;
        color: #1f2937;

        /* 标题 */
        :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
          margin: 22px 0 10px;
          color: #111827;
          font-weight: 700;
          line-height: 1.4;
        }

        :deep(h1) { font-size: 22px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }
        :deep(h2) { font-size: 19px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
        :deep(h3) { font-size: 17px; }
        :deep(h4) { font-size: 15px; color: #374151; }

        /* 段落 */
        :deep(p) {
          margin: 10px 0;
          word-break: break-word;
        }

        /* 列表 */
        :deep(ul), :deep(ol) {
          margin: 10px 0;
          padding-left: 28px;
        }

        :deep(li) {
          margin-bottom: 6px;
          line-height: 1.9;
        }

        /* 加粗与强调 */
        :deep(strong), :deep(b) {
          color: #111827;
          font-weight: 700;
        }

        :deep(em) {
          color: #374151;
          font-style: italic;
        }

        /* 引用块 */
        :deep(blockquote) {
          margin: 14px 0;
          padding: 10px 16px;
          border-left: 4px solid #6366f1;
          background: #f5f3ff;
          color: #4338ca;
          border-radius: 0 8px 8px 0;
        }

        /* 行内代码 */
        :deep(code) {
          background: #f3f4f6;
          color: #111827;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 13.5px;
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
        }

        /* 代码块 */
        :deep(pre) {
          background: #0f172a;
          color: #e2e8f0;
          padding: 16px 18px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 14px 0;

          code {
            background: transparent;
            color: inherit;
            padding: 0;
            font-size: 13px;
          }
        }

        /* 表格 */
        :deep(table) {
          width: 100%;
          border-collapse: collapse;
          margin: 14px 0;
          font-size: 14px;

          th, td {
            padding: 10px 12px;
            border: 1px solid #e5e7eb;
            text-align: left;
          }

          th {
            background: #f8fafc;
            color: #111827;
            font-weight: 700;
          }

          tr:nth-child(even) td {
            background: #fafafa;
          }
        }

        /* 水平分割线 */
        :deep(hr) {
          border: none;
          border-top: 1px dashed #d1d5db;
          margin: 18px 0;
        }

        /* 链接 */
        :deep(a) {
          color: #2563eb;
          text-decoration: none;
          border-bottom: 1px dotted #bfdbfe;

          &:hover {
            color: #1d4ed8;
            border-bottom-color: #93c5fd;
          }
        }
      }

      .json-content {
        pre {
          background: var(--el-fill-color-light);
          padding: 16px;
          border-radius: 8px;
          overflow-x: auto;
          font-size: 13px;
          line-height: 1.6;
          color: #1f2937;
        }
      }
    }
  }

  /* 报告模块 tabs 风格微调 */
  .report-tabs {
    :deep(.el-tabs__item) {
      font-size: 14px;
    }
  }

  .error-container {
    padding: 48px 24px;
  }
}
</style>
