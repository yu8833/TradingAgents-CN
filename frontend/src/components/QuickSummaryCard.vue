<template>
  <div class="quick-summary-card">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <span class="icon">🚀</span>
        <span class="title">快速结论</span>
      </div>
      <div class="header-right" v-if="showDeepButton">
        <el-button type="primary" size="small" @click="handleDeepAnalysis">
          深度分析
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 主要数据行 -->
    <div class="main-data">
      <!-- 操作建议 -->
      <div class="data-item action-item">
        <div class="item-label">操作建议</div>
        <div class="item-value" :class="'action-' + actionClass">
          {{ result?.buy_signal || '暂无' }}
        </div>
      </div>

      <!-- 置信度 -->
      <div class="data-item">
        <div class="item-label">置信度</div>
        <div class="item-value">
          <span class="confidence-value">{{ formatConfidence(result?.confidence) }}</span>
        </div>
      </div>

      <!-- 综合评分 -->
      <div class="data-item">
        <div class="item-label">综合评分</div>
        <div class="item-value">
          <span class="score-value">{{ result?.signal_score || 0 }}</span>
          <span class="score-max">/100</span>
        </div>
      </div>

      <!-- 趋势状态 -->
      <div class="data-item">
        <div class="item-label">趋势状态</div>
        <div class="item-value trend-value">
          {{ result?.trend_status || '暂无' }}
        </div>
      </div>
    </div>

    <!-- 一句话总结 -->
    <div class="summary-bar" v-if="result?.summary">
      <span class="summary-label">一句话：</span>
      <span class="summary-text">{{ result.summary }}</span>
    </div>

    <!-- 关键价位 -->
    <div class="key-prices" v-if="hasKeyPrices">
      <div class="price-item support">
        <span class="price-label">支撑</span>
        <span class="price-value">{{ formatPrice(result?.support_levels?.[0]) }}</span>
      </div>
      <div class="price-item resistance">
        <span class="price-label">阻力</span>
        <span class="price-value">{{ formatPrice(result?.resistance_levels?.[0]) }}</span>
      </div>
      <div class="price-item stop-loss">
        <span class="price-label">止损</span>
        <span class="price-value">{{ formatPrice(result?.stop_loss) }}</span>
      </div>
      <div class="price-item target">
        <span class="price-label">目标</span>
        <span class="price-value">{{ formatPrice(result?.target) }}</span>
      </div>
    </div>

    <!-- 技术面指标概览 -->
    <div class="tech-indicators" v-if="showTechIndicators">
      <div class="indicator-item" :class="trendStatusClass">
        <span class="indicator-icon">{{ trendIcon }}</span>
        <span class="indicator-text">{{ result?.ma_alignment || result?.trend_status || '暂无' }}</span>
      </div>
      <div class="indicator-item" :class="macdStatusClass">
        <span class="indicator-icon">📊</span>
        <span class="indicator-text">{{ result?.macd_status || '暂无' }}</span>
      </div>
      <div class="indicator-item" :class="rsiStatusClass">
        <span class="indicator-icon">📈</span>
        <span class="indicator-text">{{ result?.rsi_status || '暂无' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  result: {
    type: Object,
    default: null
  },
  showDeepButton: {
    type: Boolean,
    default: true
  },
  showTechIndicators: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['deep-analysis'])

const actionClass = computed(() => {
  // 优先使用标准化字段 signal_type，其次回退到字符串匹配
  const signalType = props.result?.signal_type || ''
  const signal = props.result?.buy_signal || ''
  
  // 标准化信号类型判断
  if (signalType === 'buy' || signalType === 'strong_buy' || 
      signal.includes('买入') || signal.includes('强烈买入')) {
    return 'buy'
  }
  if (signalType === 'sell' || signalType === 'strong_sell' || 
      signal.includes('卖出') || signal.includes('强烈卖出')) {
    return 'sell'
  }
  if (signalType === 'wait' || signal.includes('观望')) {
    return 'wait'
  }
  return 'hold'
})

const signalType = computed(() => {
  const type = props.result?.signal_type || ''
  const signal = props.result?.buy_signal || ''
  if (type) return type
  if (signal.includes('买入') || signal.includes('强烈买入')) return 'buy'
  if (signal.includes('卖出') || signal.includes('强烈卖出')) return 'sell'
  if (signal.includes('观望')) return 'wait'
  return 'hold'
})

const trendStatusClass = computed(() => {
  const status = props.result?.trend_status || ''
  if (status.includes('多头')) return 'bull'
  if (status.includes('空头')) return 'bear'
  return 'neutral'
})

const macdStatusClass = computed(() => {
  const status = props.result?.macd_status || ''
  if (status.includes('金叉') || status.includes('多头')) return 'bull'
  if (status.includes('死叉') || status.includes('空头')) return 'bear'
  return 'neutral'
})

const rsiStatusClass = computed(() => {
  const status = props.result?.rsi_status || ''
  if (status.includes('超买')) return 'overbought'
  if (status.includes('超卖')) return 'oversold'
  return 'neutral'
})

const trendIcon = computed(() => {
  const status = props.result?.trend_status || ''
  if (status.includes('强势多头')) return '🌟'
  if (status.includes('多头')) return '📈'
  if (status.includes('强势空头')) return '💥'
  if (status.includes('空头')) return '📉'
  return '➡️'
})

const hasKeyPrices = computed(() => {
  return props.result?.support_levels?.length > 0 ||
         props.result?.resistance_levels?.length > 0 ||
         props.result?.stop_loss > 0 ||
         props.result?.target > 0
})

const formatConfidence = (val) => {
  if (val === null || val === undefined) return '--'
  return `${Math.round(val)}%`
}

const formatPrice = (val) => {
  if (val === null || val === undefined || val <= 0) return '--'
  return val.toFixed(2)
}

const handleDeepAnalysis = () => {
  emit('deep-analysis', props.result)
}
</script>

<style scoped>
.quick-summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left .icon {
  font-size: 20px;
}

.header-left .title {
  font-size: 16px;
  font-weight: 600;
}

.header-right .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
}

.header-right .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.main-data {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.data-item {
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 8px;
}

.data-item.action-item {
  background: rgba(255, 255, 255, 0.2);
}

.item-label {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.item-value {
  font-size: 14px;
  font-weight: 600;
}

.item-value.action-buy {
  color: #52c41a;
  font-size: 16px;
}

.item-value.action-sell {
  color: #ff4d4f;
  font-size: 16px;
}

.item-value.action-wait {
  color: #faad14;
  font-size: 16px;
}

.item-value.action-hold {
  color: #1890ff;
  font-size: 16px;
}

.confidence-value {
  color: #52c41a;
}

.score-value {
  font-size: 18px;
  font-weight: bold;
}

.score-max {
  font-size: 12px;
  opacity: 0.7;
}

.trend-value {
  font-size: 12px;
}

.summary-bar {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  font-size: 13px;
}

.summary-label {
  font-weight: 600;
  color: #ffd700;
}

.summary-text {
  color: white;
}

.key-prices {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.price-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 8px;
  text-align: center;
}

.price-label {
  display: block;
  font-size: 11px;
  opacity: 0.8;
  margin-bottom: 2px;
}

.price-value {
  font-size: 14px;
  font-weight: 600;
}

.price-item.support .price-value {
  color: #52c41a;
}

.price-item.resistance .price-value {
  color: #ff4d4f;
}

.price-item.stop-loss .price-value {
  color: #faad14;
}

.price-item.target .price-value {
  color: #1890ff;
}

.tech-indicators {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.indicator-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.indicator-item.bull {
  background: rgba(82, 196, 26, 0.3);
}

.indicator-item.bear {
  background: rgba(255, 77, 79, 0.3);
}

.indicator-item.overbought {
  background: rgba(255, 77, 79, 0.3);
}

.indicator-item.oversold {
  background: rgba(82, 196, 26, 0.3);
}

.indicator-icon {
  font-size: 12px;
}

.indicator-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}
</style>
