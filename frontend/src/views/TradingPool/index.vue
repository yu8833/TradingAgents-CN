<template>
  <div class="trading-pool-container">
    <div class="page-header">
      <h1 class="page-title">
        <TrendCharts class="icon" />
        三买三卖
      </h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="scanAllStocks" :disabled="scanning">
          <Refresh :class="['icon', { spinning: scanning }]" />
          {{ scanning ? '扫描中...' : '扫描全市场' }}
        </button>
        <button class="btn btn-secondary" @click="toggleMonitoring">
          <component :is="monitoringEnabled ? 'Close' : 'Bell'" class="icon" />
          {{ monitoringEnabled ? '停止监控' : '启动监控' }}
        </button>
      </div>
    </div>

    <div class="scan-info" v-if="lastScanTime">
      <span>上次扫描: {{ formatTime(lastScanTime) }}</span>
      <span class="scan-stats">共扫描 {{ scanResult?.total_scanned || 0 }} 只，发现信号 {{ scanResult?.total_with_signals || 0 }} 只</span>
    </div>

    <div class="main-content">
      <!-- 左侧：分类扫描结果 -->
      <div class="left-panel">
        <div class="panel-header">
          <h2>信号扫描结果</h2>
        </div>

        <!-- 买入信号 -->
        <div class="signal-section">
          <h3 class="section-title buy">
            <span class="section-icon">📈</span>
            买入信号 (B1/B2/B3)
          </h3>

          <div v-for="category in scanResult?.buy_signals || []" :key="category.category" class="category-section">
            <div class="category-header" @click="toggleCategory(category.category)">
              <span class="category-name" :class="'category-' + category.category.toLowerCase()">
                {{ category.category }} - {{ category.category_name }}
              </span>
              <span class="category-count">{{ category.count }} 只</span>
              <component :is="expandedCategories[category.category] ? 'ArrowUp' : 'ArrowDown'" class="expand-icon" />
            </div>
            <div v-show="expandedCategories[category.category]" class="category-stocks">
              <div v-if="category.stocks.length === 0" class="empty-hint">暂无股票</div>
              <div
                v-for="stock in category.stocks"
                :key="stock.stock_code"
                class="stock-item"
                :class="{ selected: selectedStocks.has(stock.stock_code) }"
              >
                <div class="stock-info" @click="selectStock(stock)">
                  <span class="stock-code">{{ stock.stock_code }}</span>
                  <span class="stock-name">{{ stock.stock_name }}</span>
                  <span class="stock-price">¥{{ formatPrice(stock.current_price) }}</span>
                </div>
                <div class="stock-actions">
                  <button
                    v-if="!isInWatching(stock.stock_code)"
                    class="btn btn-xs btn-success"
                    @click.stop="addToWatching(stock)"
                  >
                    <Plus class="icon-xs" />
                    自选
                  </button>
                  <span v-else class="in-watching-tag">已关注</span>
                  <button class="btn btn-xs btn-info" @click.stop="analyzeStock(stock)">
                    分析
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 卖出信号 -->
        <div class="signal-section">
          <h3 class="section-title sell">
            <span class="section-icon">📉</span>
            卖出信号 (S1/S2/S3)
          </h3>

          <div v-for="category in scanResult?.sell_signals || []" :key="category.category" class="category-section">
            <div class="category-header" @click="toggleCategory(category.category)">
              <span class="category-name" :class="'category-' + category.category.toLowerCase()">
                {{ category.category }} - {{ category.category_name }}
              </span>
              <span class="category-count">{{ category.count }} 只</span>
              <component :is="expandedCategories[category.category] ? 'ArrowUp' : 'ArrowDown'" class="expand-icon" />
            </div>
            <div v-show="expandedCategories[category.category]" class="category-stocks">
              <div v-if="category.stocks.length === 0" class="empty-hint">暂无股票</div>
              <div
                v-for="stock in category.stocks"
                :key="stock.stock_code"
                class="stock-item sell-signal"
              >
                <div class="stock-info" @click="selectStock(stock)">
                  <span class="stock-code">{{ stock.stock_code }}</span>
                  <span class="stock-name">{{ stock.stock_name }}</span>
                  <span class="stock-price">¥{{ formatPrice(stock.current_price) }}</span>
                </div>
                <div class="stock-actions">
                  <button
                    v-if="!isInWatching(stock.stock_code)"
                    class="btn btn-xs btn-success"
                    @click.stop="addToWatching(stock)"
                  >
                    <Plus class="icon-xs" />
                    自选
                  </button>
                  <span v-else class="in-watching-tag">已关注</span>
                  <button class="btn btn-xs btn-info" @click.stop="analyzeStock(stock)">
                    分析
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：自选股 -->
      <div class="right-panel">
        <div class="panel-header">
          <h2>我的自选股</h2>
          <span class="watching-count">{{ watchingStocks.length }} 只</span>
        </div>

        <div class="watching-list">
          <div v-if="watchingStocks.length === 0" class="empty-state">
            <Star class="empty-icon" />
            <p>暂无自选股</p>
            <p class="hint">从左侧扫描结果中添加股票到自选股</p>
          </div>

          <div
            v-for="stock in watchingStocks"
            :key="stock.stock_code"
            class="watching-item"
            :class="{ alerting: alertingStocks.has(stock.stock_code) }"
          >
            <div class="watching-info">
              <div class="stock-main">
                <span class="stock-code">{{ stock.stock_code }}</span>
                <span class="stock-name">{{ stock.stock_name }}</span>
              </div>
              <div class="stock-meta">
                <span class="added-signal" :class="'signal-' + stock.added_signal.toLowerCase()">
                  {{ getSignalName(stock.added_signal) }}
                </span>
                <span class="added-date">添加于 {{ formatDate(stock.added_at) }}</span>
              </div>
            </div>
            <div class="watching-actions">
              <button class="btn btn-xs btn-danger" @click="removeFromWatching(stock.stock_code)">
                <Delete class="icon-xs" />
              </button>
            </div>
          </div>
        </div>

        <!-- 通知面板 -->
        <div class="notifications-panel" v-if="notifications.length > 0">
          <div class="panel-header">
            <h3>最新通知</h3>
          </div>
          <div class="notifications-list">
            <div
              v-for="notif in notifications"
              :key="notif.stock_code + notif.timestamp"
              class="notification-item"
              :class="'severity-' + notif.signal_strength"
            >
              <div class="notif-header">
                <span class="notif-stock">{{ notif.stock_name }}</span>
                <span class="notif-strength">{{ getStrengthText(notif.signal_strength) }}</span>
              </div>
              <div class="notif-message">{{ notif.message }}</div>
              <div class="notif-action">{{ notif.action }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分析弹窗 -->
    <el-dialog title="个股分析" v-model="showAnalysisDialog" width="800px">
      <div v-if="analysisResult" class="analysis-content">
        <div class="analysis-header">
          <h3>{{ analysisResult.stock_code }} {{ analysisResult.stock_name }}</h3>
          <div class="current-price">当前价: ¥{{ formatPrice(analysisResult.current_price) }}</div>
        </div>

        <div class="indicators-grid">
          <div class="indicator-card">
            <div class="indicator-label">MA5</div>
            <div class="indicator-value">{{ formatPrice(analysisResult.indicators?.ma_5) }}</div>
          </div>
          <div class="indicator-card">
            <div class="indicator-label">MA13</div>
            <div class="indicator-value">{{ formatPrice(analysisResult.indicators?.ma_13) }}</div>
          </div>
          <div class="indicator-card">
            <div class="indicator-label">MA60</div>
            <div class="indicator-value">{{ formatPrice(analysisResult.indicators?.ma_60) }}</div>
          </div>
          <div class="indicator-card">
            <div class="indicator-label">BIAS60</div>
            <div class="indicator-value" :class="analysisResult.indicators?.bias_60 > 0 ? 'positive' : 'negative'">
              {{ analysisResult.indicators?.bias_60?.toFixed(2) }}%
            </div>
          </div>
          <div class="indicator-card">
            <div class="indicator-label">DIF</div>
            <div class="indicator-value">{{ analysisResult.indicators?.dif?.toFixed(4) }}</div>
          </div>
          <div class="indicator-card">
            <div class="indicator-label">DEA</div>
            <div class="indicator-value">{{ analysisResult.indicators?.dea?.toFixed(4) }}</div>
          </div>
        </div>

        <div class="signals-section">
          <h4>三买信号状态</h4>
          <div class="signals-grid">
            <div v-for="signal in buySignals" :key="signal.type" class="signal-item">
              <div :class="['signal-icon', { active: analysisResult.signals?.includes(signal.type) }]">
                {{ signal.type }}
              </div>
              <div class="signal-name">{{ signal.name }}</div>
              <div class="signal-desc">{{ signal.desc }}</div>
            </div>
          </div>
        </div>

        <div class="signals-section">
          <h4>三卖信号状态</h4>
          <div class="signals-grid">
            <div v-for="signal in sellSignals" :key="signal.type" class="signal-item">
              <div :class="['signal-icon sell', { active: analysisResult.signals?.includes(signal.type) }]">
                {{ signal.type }}
              </div>
              <div class="signal-name">{{ signal.name }}</div>
              <div class="signal-desc">{{ signal.desc }}</div>
            </div>
          </div>
        </div>

        <div v-if="analysisResult.recommendations?.length > 0" class="recommendations">
          <h4>操作建议</h4>
          <div v-for="(rec, index) in analysisResult.recommendations" :key="index" class="recommendation-item">
            <Warning class="rec-icon" />
            {{ rec }}
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 策略介绍 -->
    <div class="strategy-intro">
      <div class="intro-section">
        <h2 class="intro-title">📊 策略概述</h2>
        <p class="intro-desc">
          三买三卖交易策略是一种基于技术分析的量化交易方法，结合了均线系统（MA5/MA8/MA13/MA55/MA60）、乖离率（BIAS60）和MACD指标，
          帮助投资者识别股票的买入和卖出时机。
        </p>
      </div>

      <div class="signals-overview">
        <div class="signals-grid">
          <div class="signal-card buy">
            <div class="signal-header">
              <span class="signal-icon">📈</span>
              <span class="signal-category">买入信号</span>
            </div>
            <div class="signal-items">
              <div class="signal-item">
                <span class="signal-type">B1</span>
                <span class="signal-name">左侧买点</span>
                <span class="signal-desc">BIAS60进入超卖区间[-30%, -20%]</span>
              </div>
              <div class="signal-item">
                <span class="signal-type">B2</span>
                <span class="signal-name">突破买点</span>
                <span class="signal-desc">放量突破MA55/MA60均线</span>
              </div>
              <div class="signal-item">
                <span class="signal-type">B3</span>
                <span class="signal-name">回踩买点</span>
                <span class="signal-desc">回踩确认支撑后放量上涨</span>
              </div>
            </div>
          </div>

          <div class="signal-card sell">
            <div class="signal-header">
              <span class="signal-icon">📉</span>
              <span class="signal-category">卖出信号</span>
            </div>
            <div class="signal-items">
              <div class="signal-item">
                <span class="signal-type">S1</span>
                <span class="signal-name">加速卖点</span>
                <span class="signal-desc">BIAS60超过超买阈值，警惕回调</span>
              </div>
              <div class="signal-item">
                <span class="signal-type">S2</span>
                <span class="signal-name">跌破卖点</span>
                <span class="signal-desc">连续跌破MA5/MA8/MA13短期均线</span>
              </div>
              <div class="signal-item">
                <span class="signal-type">S3</span>
                <span class="signal-name">清仓卖点</span>
                <span class="signal-desc">跌破MA55/MA60且MACD死叉确认</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="indicators-section">
        <h3 class="section-title">📋 核心指标说明</h3>
        <div class="indicators-grid">
          <div class="indicator-item">
            <span class="indicator-name">MA5/MA8/MA13</span>
            <span class="indicator-desc">短期均线，判断短期趋势</span>
          </div>
          <div class="indicator-item">
            <span class="indicator-name">MA55/MA60</span>
            <span class="indicator-desc">中长期均线，判断趋势方向</span>
          </div>
          <div class="indicator-item">
            <span class="indicator-name">BIAS60</span>
            <span class="indicator-desc">60日乖离率，衡量价格偏离程度</span>
          </div>
          <div class="indicator-item">
            <span class="indicator-name">MACD</span>
            <span class="indicator-desc">指数平滑异同移动平均线，判断趋势强度</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  TrendCharts, Refresh, Bell, Close, Plus, Delete, Star, ArrowUp, ArrowDown,
  Warning, DataAnalysis
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ApiClient } from '@/api/request'
import { favoritesApi } from '@/api/favorites'

// 类型定义
interface SignalDetectionResult {
  stock_code: string
  stock_name: string
  current_price: number
  indicators: Record<string, any>
  signals: string[]
  recommendations: string[]
  position_advice: string
}

interface ScanResultCategory {
  category: string
  category_name: string
  category_description: string
  stocks: SignalDetectionResult[]
  count: number
}

interface ScanResult {
  total_scanned: number
  total_with_signals: number
  scan_time: string
  buy_signals: ScanResultCategory[]
  sell_signals: ScanResultCategory[]
}

interface WatchingStock {
  stock_code: string
  stock_name: string
  added_date?: string
  added_at?: string
  added_signal?: string
  entry_price?: number
  current_price?: number
  change_percent?: number
  status?: string
  market?: string
  notes?: string
}

interface SignalAlert {
  stock_code: string
  stock_name: string
  new_signals: string[]
  signal_strength: string
  message: string
  action: string
  timestamp: string
}

// 状态
const scanning = ref(false)
const monitoringEnabled = ref(false)
const lastScanTime = ref<Date | null>(null)
const scanResult = ref<ScanResult | null>(null)
const watchingStocks = ref<WatchingStock[]>([])
const notifications = ref<SignalAlert[]>([])
const selectedStocks = ref<Set<string>>(new Set())
const alertingStocks = ref<Set<string>>(new Set())
const expandedCategories = ref<Record<string, boolean>>({
  'B1': true, 'B2': true, 'B3': true,
  'S1': true, 'S2': true, 'S3': true
})
const showAnalysisDialog = ref(false)
const analysisResult = ref<SignalDetectionResult | null>(null)
let monitoringTimer: number | null = null

// 信号定义
const buySignals = [
  { type: 'B1', name: '左侧买点', desc: 'BIAS60在[-30%,-20%]区间' },
  { type: 'B2', name: '突破买点', desc: '放量突破MA55/MA60' },
  { type: 'B3', name: '回踩买点', desc: '回踩确认后放量上涨' }
]

const sellSignals = [
  { type: 'S1', name: '加速卖点', desc: 'BIAS60超过阈值' },
  { type: 'S2', name: '跌破卖点', desc: '连续跌破MA5/MA8/MA13' },
  { type: 'S3', name: '清仓卖点', desc: '跌破MA55/MA60且趋势向下' }
]

// 工具函数
function formatPrice(price: number | undefined) {
  if (!price) return '--'
  return price.toFixed(2)
}

function formatTime(time: Date | null) {
  if (!time) return '--'
  return time.toLocaleTimeString('zh-CN')
}

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function getSignalName(signal: string) {
  const names: Record<string, string> = {
    B1: '左侧买点', B2: '突破买点', B3: '回踩买点',
    S1: '加速卖点', S2: '跌破卖点', S3: '清仓卖点',
    manual: '手动添加'
  }
  return names[signal] || signal
}

function getStrengthText(strength: string) {
  const texts: Record<string, string> = {
    mild: '轻微',
    strong: '强烈',
    critical: '紧急'
  }
  return texts[strength] || strength
}

function isInWatching(stockCode: string) {
  return watchingStocks.value.some(s => s.stock_code === stockCode)
}

function toggleCategory(category: string) {
  expandedCategories.value[category] = !expandedCategories.value[category]
}

function selectStock(stock: SignalDetectionResult) {
  if (selectedStocks.value.has(stock.stock_code)) {
    selectedStocks.value.delete(stock.stock_code)
  } else {
    selectedStocks.value.add(stock.stock_code)
  }
}

// API调用
async function scanAllStocks() {
  scanning.value = true
  try {
    console.log('🔍 [scan] 开始调用扫描API...')

    const response = await ApiClient.get(
      '/api/three-buy-three-sell/scan/all?limit_per_category=50',
      {},
      { timeout: 300000 }
    )

    console.log('🔍 [scan] API返回的完整response:', JSON.stringify(response, null, 2))
    console.log('🔍 [scan] response类型:', typeof response)
    console.log('🔍 [scan] response.keys:', response ? Object.keys(response) : 'null/undefined')

    // 从响应中提取实际的扫描结果数据
    // 支持两种格式：
    //   新格式: { success: true, data: { total_scanned, buy_signals, ... }, message: "..." }
    //   旧格式: { total_scanned, buy_signals, sell_signals, ... }
    let scanData: any = null
    let apiMessage = ''

    if (response && typeof response === 'object') {
      if ('success' in response && response.success && response.data) {
        // 新格式 - 从 response.data 中提取
        scanData = response.data
        apiMessage = response.message || ''
        console.log('🔍 [scan] ✅ 识别为新格式（success/data/message）')
        console.log('🔍 [scan] scanData.keys:', Object.keys(scanData))
        console.log('🔍 [scan] scanData.total_with_signals:', scanData.total_with_signals)
      } else if ('total_with_signals' in response || 'buy_signals' in response) {
        // 旧格式 - response 本身就是数据
        scanData = response
        console.log('🔍 [scan] ✅ 识别为旧格式（直接是ScanResult）')
      } else {
        // 尝试其他可能的嵌套方式
        console.log('🔍 [scan] ⚠️ 无法识别响应格式，尝试回退方式')
        scanData = response?.data ?? response
      }
    }

    if (!scanData) {
      console.error('❌ [scan] 无法获取扫描数据')
      ElMessage.error('扫描结果为空，请检查后端服务')
      return
    }

    console.log('🔍 [scan] 最终赋值给 scanResult.value:', {
      total_scanned: scanData.total_scanned,
      total_with_signals: scanData.total_with_signals,
      buy_count: scanData.buy_signals?.length,
      sell_count: scanData.sell_signals?.length
    })

    scanResult.value = scanData
    lastScanTime.value = new Date()

    const signalCount = scanData.total_with_signals ?? 0
    ElMessage.success(apiMessage || `扫描完成，发现 ${signalCount} 只股票有信号`)
  } catch (error: any) {
    console.error('❌ [scan] 扫描失败:', error)
    ElMessage.error('扫描失败: ' + (error.message || '未知错误'))
  } finally {
    scanning.value = false
  }
}

async function loadWatchingStocks() {
  try {
    const response: any = await favoritesApi.list()
    // favoritesApi返回的数据结构可能是 { data: [...] } 或直接是 [...]
    const list = response?.data || response || []
    // 转换数据结构以适配界面
    watchingStocks.value = list.map((item: any) => ({
      stock_code: item.stock_code,
      stock_name: item.stock_name,
      added_at: item.added_at,
      added_signal: item.added_signal || item.tags?.[0] || 'manual',
      current_price: item.current_price,
      change_percent: item.change_percent,
      market: item.market,
      notes: item.notes
    }))
  } catch (error) {
    console.error('加载自选股失败:', error)
  }
}

async function addToWatching(stock: SignalDetectionResult) {
  try {
    // 确定主要信号作为标签
    const signal = stock.signals && stock.signals.length > 0 ? stock.signals[0] : 'B'

    await favoritesApi.add({
      stock_code: stock.stock_code,
      stock_name: stock.stock_name,
      market: 'A股',
      tags: [signal],
      notes: `三买三卖信号: ${stock.signals?.join(', ') || '无'}`
    })
    ElMessage.success(`${stock.stock_name} 已添加到自选股`)
    await loadWatchingStocks()
  } catch (error: any) {
    console.error('添加失败:', error)
    // 如果是已存在的错误，给出友好提示
    if (error?.message?.includes('已存在') || error?.message?.includes('already')) {
      ElMessage.info(`${stock.stock_name} 已在自选股中`)
    } else {
      ElMessage.error('添加失败: ' + (error.message || '未知错误'))
    }
  }
}

async function removeFromWatching(stockCode: string) {
  try {
    await favoritesApi.remove(stockCode)
    ElMessage.success('已从自选股移除')
    await loadWatchingStocks()
  } catch (error: any) {
    console.error('移除失败:', error)
    ElMessage.error('移除失败: ' + (error.message || '未知错误'))
  }
}

async function analyzeStock(stock: SignalDetectionResult) {
  try {
    const response = await ApiClient.get(`/api/three-buy-three-sell/stocks/${stock.stock_code}/analysis`)
    analysisResult.value = response
    showAnalysisDialog.value = true
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败')
  }
}

async function toggleMonitoring() {
  if (monitoringEnabled.value) {
    // 停止监控
    try {
      await ApiClient.post('/api/three-buy-three-sell/monitoring/stop')
      monitoringEnabled.value = false
      if (monitoringTimer) {
        clearInterval(monitoringTimer)
        monitoringTimer = null
      }
      ElMessage.success('监控已停止')
    } catch (error) {
      console.error('停止监控失败:', error)
    }
  } else {
    // 启动监控
    if (watchingStocks.value.length === 0) {
      ElMessage.warning('请先添加自选股')
      return
    }
    try {
      await ApiClient.post('/api/three-buy-three-sell/monitoring/start?interval_minutes=1')
      monitoringEnabled.value = true
      // 每30秒检查一次通知
      monitoringTimer = window.setInterval(checkNotifications, 30000)
      ElMessage.success('监控已启动，每分钟扫描自选股信号')
    } catch (error) {
      console.error('启动监控失败:', error)
    }
  }
}

async function checkNotifications() {
  try {
    const response = await ApiClient.get('/api/three-buy-three-sell/monitoring/alerts')
    if (response && response.length > 0) {
      notifications.value = response
      // 标记有信号的股票
      response.forEach((alert: SignalAlert) => {
        alertingStocks.value.add(alert.stock_code)
        ElMessage.warning(`${alert.stock_name}: ${alert.message}`)
      })
    }
  } catch (error) {
    console.error('检查通知失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadWatchingStocks()
})

onUnmounted(() => {
  if (monitoringTimer) {
    clearInterval(monitoringTimer)
  }
})
</script>

<style scoped>
.trading-pool-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  font-weight: bold;
}

.icon {
  width: 24px;
  height: 24px;
}

.icon-xs {
  width: 14px;
  height: 14px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-actions {
  display: flex;
  gap: 10px;
}

.scan-info {
  display: flex;
  gap: 20px;
  padding: 10px 15px;
  background: #e8f4ff;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #666;
}

.scan-stats {
  color: #409eff;
  font-weight: 500;
}

.main-content {
  display: flex;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  flex: 2;
  overflow-y: auto;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.panel-header h2 {
  font-size: 18px;
  font-weight: bold;
}

.watching-count {
  background: #409eff;
  color: #fff;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.signal-section {
  margin-bottom: 25px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid;
}

.section-title.buy {
  border-color: #67c23a;
  color: #67c23a;
}

.section-title.sell {
  border-color: #f56c6c;
  color: #f56c6c;
}

.section-icon {
  font-size: 20px;
}

.category-section {
  margin-bottom: 10px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f5f5;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.category-header:hover {
  background: #e8e8e8;
}

.category-name {
  font-weight: bold;
  flex: 1;
}

.category-B1 { color: #67c23a; }
.category-B2 { color: #85ce61; }
.category-B3 { color: #99d16a; }
.category-S1 { color: #f56c6c; }
.category-S2 { color: #e64242; }
.category-S3 { color: #c94040; }

.category-count {
  background: #ddd;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: #666;
}

.expand-icon {
  width: 16px;
  height: 16px;
  color: #999;
}

.category-stocks {
  padding: 10px 0;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 15px;
  font-size: 14px;
}

.stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  margin: 5px 0;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 3px solid #67c23a;
  transition: all 0.2s;
}

.stock-item:hover {
  background: #f0f9eb;
}

.stock-item.selected {
  background: #e8f4ff;
  border-left-color: #409eff;
}

.stock-item.sell-signal {
  border-left-color: #f56c6c;
}

.stock-item.sell-signal:hover {
  background: #fef0f0;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
}

.stock-code {
  font-weight: bold;
  color: #333;
}

.stock-name {
  color: #666;
}

.stock-price {
  color: #409eff;
  font-weight: 500;
}

.stock-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.in-watching-tag {
  color: #67c23a;
  font-size: 12px;
  padding: 2px 8px;
  background: #f0f9eb;
  border-radius: 4px;
}

.watch-list {
  flex: 1;
  overflow-y: auto;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-icon {
  width: 60px;
  height: 60px;
  color: #ddd;
  margin-bottom: 15px;
}

.hint {
  font-size: 12px;
  margin-top: 5px;
}

.watching-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 3px solid #409eff;
}

.watching-item.alerting {
  background: #fff3cd;
  border-left-color: #e6a23c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.watch-info {
  flex: 1;
}

.stock-main {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
}

.stock-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #999;
}

.added-signal {
  padding: 1px 6px;
  border-radius: 4px;
  background: #e8f4ff;
  color: #409eff;
}

.added-signal.signal-b1,
.added-signal.signal-b2,
.added-signal.signal-b3 {
  background: #f0f9eb;
  color: #67c23a;
}

.added-signal.signal-s1,
.added-signal.signal-s2,
.added-signal.signal-s3 {
  background: #fef0f0;
  color: #f56c6c;
}

.notifications-panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  max-height: 250px;
  overflow-y: auto;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-item {
  padding: 10px 12px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.notification-item.severity-strong {
  background: #fff3cd;
  border-left-color: #e6a23c;
}

.notification-item.severity-critical {
  background: #fef0f0;
  border-left-color: #f56c6c;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.notif-stock {
  font-weight: bold;
}

.notif-strength {
  font-size: 12px;
  padding: 1px 6px;
  background: #ddd;
  border-radius: 4px;
}

.notif-message {
  font-size: 13px;
  color: #666;
  margin-bottom: 3px;
}

.notif-action {
  font-size: 12px;
  color: #409eff;
}

/* 策略介绍样式 */
.strategy-intro {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.intro-section {
  margin-bottom: 20px;
}

.intro-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #333;
}

.intro-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.signals-overview {
  margin-bottom: 20px;
}

.signals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.signal-card {
  border-radius: 12px;
  padding: 15px;
  background: #f9f9f9;
}

.signal-card.buy {
  border-left: 4px solid #67c23a;
}

.signal-card.sell {
  border-left: 4px solid #f56c6c;
}

.signal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.signal-icon {
  font-size: 20px;
}

.signal-category {
  font-size: 16px;
  font-weight: bold;
}

.signal-card.buy .signal-category {
  color: #67c23a;
}

.signal-card.sell .signal-category {
  color: #f56c6c;
}

.signal-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.signal-card .signal-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #fff;
  border-radius: 8px;
}

.signal-card .signal-type {
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
}

.signal-card.buy .signal-type {
  background: #f0f9eb;
  color: #67c23a;
}

.signal-card.sell .signal-type {
  background: #fef0f0;
  color: #f56c6c;
}

.signal-card .signal-name {
  font-weight: 500;
  font-size: 14px;
}

.signal-card .signal-desc {
  font-size: 12px;
  color: #999;
  margin-left: auto;
}

.indicators-section {
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.indicators-section .section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #333;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.indicator-name {
  font-weight: 500;
  color: #333;
}

.indicator-desc {
  font-size: 13px;
  color: #999;
}

/* 按钮样式 */
.btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-xs {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-primary {
  background: #409eff;
  color: #fff;
}

.btn-primary:hover {
  background: #66b1ff;
}

.btn-primary:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: #fff;
}

.btn-success {
  background: #67c23a;
  color: #fff;
}

.btn-success:hover {
  background: #85ce61;
}

.btn-info {
  background: #909399;
  color: #fff;
}

.btn-danger {
  background: #f56c6c;
  color: #fff;
}

.btn-danger:hover {
  background: #f78989;
}

/* 分析弹窗样式 */
.analysis-content {
  padding: 10px;
}

.analysis-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.analysis-header h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.current-price {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.indicator-card {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.indicator-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.indicator-value {
  font-size: 16px;
  font-weight: bold;
}

.indicator-value.positive { color: #f56c6c; }
.indicator-value.negative { color: #67c23a; }

.signals-section {
  margin-bottom: 20px;
}

.signals-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
}

.signals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.signal-item {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.signal-icon {
  width: 36px;
  height: 36px;
  line-height: 36px;
  border-radius: 50%;
  background: #eee;
  color: #999;
  font-weight: bold;
  margin: 0 auto 8px;
}

.signal-icon.active {
  background: #67c23a;
  color: #fff;
}

.signal-icon.sell.active {
  background: #f56c6c;
}

.signal-name {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 4px;
}

.signal-desc {
  font-size: 11px;
  color: #999;
}

.recommendations {
  background: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  padding: 12px;
}

.recommendations h4 {
  margin-bottom: 10px;
  font-size: 14px;
}

.recommendation-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
}

.rec-icon {
  width: 16px;
  height: 16px;
  color: #e6a23c;
  flex-shrink: 0;
  margin-top: 2px;
}
</style>
