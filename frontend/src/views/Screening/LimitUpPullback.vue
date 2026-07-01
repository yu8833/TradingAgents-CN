<template>
  <div class="limit-up-pullback">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><TrendCharts /></el-icon>
        涨停回调（龙回头）
      </h1>
      <p class="page-description">
        涨停板回调战法，筛选主力建仓后缩量洗盘、即将启动主升浪的强势股
      </p>
    </div>

    <!-- 策略说明卡片 -->
    <el-card class="strategy-intro" shadow="never">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-icon><InfoFilled /></el-icon>
            <span>策略原理</span>
            <el-tag type="warning" size="small" effect="plain">N字反包战法</el-tag>
          </div>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :span="6">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>涨停建仓</h4>
              <p>主力用涨停快速建仓或拉升，筛选有市场地位的涨停股</p>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>缩量洗盘</h4>
              <p>涨停后3-5天缩量回调，主力锁仓，成交量萎缩至1/3以下</p>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>地量止跌</h4>
              <p>回调出现地量+长下影线，抛压衰竭，左侧潜伏买点</p>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>放量突破</h4>
              <p>放量站上5日线，洗盘结束，右侧确认买点，博弈主升浪</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 参数调整面板 -->
    <el-card class="params-panel" shadow="never" style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-icon><Setting /></el-icon>
            <span>策略参数</span>
          </div>
          <div class="header-actions">
            <el-button type="text" @click="resetParams">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="params" label-width="140px" class="params-form">
        <el-row :gutter="24">
          <el-col :span="6">
            <el-form-item label="涨停回溯天数">
              <el-input-number
                v-model="params.max_lookback_days"
                :min="5"
                :max="30"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最少回调天数">
              <el-input-number
                v-model="params.min_pullback_days"
                :min="1"
                :max="10"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最多回调天数">
              <el-input-number
                v-model="params.max_pullback_days"
                :min="3"
                :max="20"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最低评分阈值">
              <el-input-number
                v-model="params.min_score"
                :min="0"
                :max="100"
                :step="5"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="6">
            <el-form-item label="缩量比例阈值">
              <el-input-number
                v-model="params.shrink_volume_ratio"
                :min="0.1"
                :max="1"
                :step="0.05"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="最少缩量天数">
              <el-input-number
                v-model="params.min_shrink_days"
                :min="1"
                :max="10"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="地量比例阈值">
              <el-input-number
                v-model="params.ground_volume_ratio"
                :min="0.1"
                :max="1"
                :step="0.05"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="下影线比例阈值">
              <el-input-number
                v-model="params.lower_shadow_ratio"
                :min="0.001"
                :max="0.1"
                :step="0.005"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="6">
            <el-form-item label="站上10日线">
              <el-switch v-model="params.above_ma10" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="突破5日线(右侧)">
              <el-switch v-model="params.breakout_ma5" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item v-if="params.breakout_ma5" label="突破放量倍数">
              <el-input-number
                v-model="params.breakout_volume_ratio"
                :min="1"
                :max="5"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="返回数量">
              <el-input-number
                v-model="params.limit"
                :min="10"
                :max="200"
                :step="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div style="text-align: center; margin-top: 8px;">
          <el-button type="primary" :loading="loading" @click="doScan" size="large">
            <el-icon><Search /></el-icon>
            开始扫描
          </el-button>
          <el-button :loading="loading" @click="resetParams" size="large" style="margin-left: 12px;">
            <el-icon><Refresh /></el-icon>
            重置参数
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 扫描结果 -->
    <el-card class="result-panel" shadow="never" style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-icon><List /></el-icon>
            <span>扫描结果</span>
            <el-tag v-if="results.length > 0" type="success" size="small" effect="plain">
              找到 {{ results.length }} 只符合条件的股票
            </el-tag>
            <el-tag v-if="tookMs" type="info" size="small" effect="plain">
              耗时 {{ (tookMs / 1000).toFixed(1) }}s
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <div v-if="!loading && results.length === 0 && !hasSearched" class="empty-state">
        <el-empty description="调整参数后点击开始扫描">
          <el-button type="primary" @click="doScan">立即扫描</el-button>
        </el-empty>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-state">
        <el-loading fullscreen-text="正在扫描全市场股票，请稍候..." />
      </div>

      <!-- 结果表格 -->
      <el-table
        v-if="results.length > 0"
        :data="results"
        v-loading="loading"
        element-loading-text="扫描中..."
        stripe
        style="width: 100%"
      >
        <el-table-column prop="code" label="代码" width="80" fixed="left">
          <template #default="{ row }">
            <span class="stock-code" @click="goToStock(row.code)">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="100" fixed="left">
          <template #default="{ row }">
            <span class="stock-name" @click="goToStock(row.code)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" width="100" />
        <el-table-column prop="close" label="现价" width="90" sortable>
          <template #default="{ row }">
            <span class="price">{{ row.close.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pct_chg" label="涨跌幅" width="100" sortable>
          <template #default="{ row }">
            <span :class="['pct', row.pct_chg >= 0 ? 'up' : 'down']">
              {{ row.pct_chg >= 0 ? '+' : '' }}{{ row.pct_chg.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="limit_up_date" label="涨停日期" width="110" />
        <el-table-column prop="days_since_limit_up" label="回调天数" width="100" sortable>
          <template #default="{ row }">{{ row.days_since_limit_up }}天</template>
        </el-table-column>
        <el-table-column prop="pullback_depth" label="回调幅度" width="100" sortable>
          <template #default="{ row }">-{{ row.pullback_depth.toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="volume_shrink_ratio" label="缩量比例" width="100" sortable>
          <template #default="{ row }">{{ (row.volume_shrink_ratio * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="ground_volume_ratio" label="地量比例" width="100" sortable>
          <template #default="{ row }">{{ (row.ground_volume_ratio * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="signal_type" label="信号类型" width="110">
          <template #default="{ row }">
            <el-tag :type="getSignalTypeTag(row.signal_type)" size="small">
              {{ row.signal_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="综合评分" width="100" sortable fixed="right">
          <template #default="{ row }">
            <el-progress
              :percentage="row.score"
              :color="getScoreColor(row.score)"
              :show-text="true"
              :stroke-width="12"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="goToStock(row.code)">分析</el-button>
            <el-button type="success" link @click="addToFavorites(row.code)">自选</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  InfoFilled,
  Setting,
  Refresh,
  Search,
  List
} from '@element-plus/icons-vue'
import { screeningApi, type LimitUpPullbackItem, type LimitUpPullbackScanReq } from '@/api/screening'

const router = useRouter()

const loading = ref(false)
const results = ref<LimitUpPullbackItem[]>([])
const tookMs = ref(0)
const hasSearched = ref(false)

const defaultParams = {
  max_lookback_days: 15,
  min_pullback_days: 2,
  max_pullback_days: 8,
  shrink_volume_ratio: 0.5,
  min_shrink_days: 2,
  above_ma10: true,
  ground_volume_ratio: 0.35,
  lower_shadow_ratio: 0.015,
  breakout_ma5: false,
  breakout_volume_ratio: 1.5,
  min_score: 40,
  limit: 50
}

const params = reactive<LimitUpPullbackScanReq>({ ...defaultParams })

const resetParams = () => {
  Object.assign(params, defaultParams)
}

const doScan = async () => {
  loading.value = true
  hasSearched.value = true
  results.value = []
  tookMs.value = 0

  try {
    const resp = await screeningApi.scanLimitUpPullback(params)
    results.value = resp.items
    tookMs.value = resp.took_ms || 0

    if (resp.items.length > 0) {
      ElMessage.success(`找到 ${resp.items.length} 只符合条件的股票`)
    } else {
      ElMessage.warning('未找到符合条件的股票，请调整参数后重试')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '扫描失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const goToStock = (code: string) => {
  router.push(`/stocks/${code}`)
}

const addToFavorites = (code: string) => {
  ElMessage.info('添加自选功能待实现')
}

const getSignalTypeTag = (type: string) => {
  const map: Record<string, string> = {
    '右侧确认': 'success',
    '左侧潜伏': 'warning',
    '缩量回调中': 'info',
    '观察': ''
  }
  return map[type] || ''
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  if (score >= 40) return '#F56C6C'
  return '#909399'
}

onMounted(() => {
  // 页面加载时自动扫描一次
  doScan()
})
</script>

<style lang="scss" scoped>
.limit-up-pullback {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  .page-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #303133;
  }

  .page-description {
    margin: 0;
    color: #909399;
    font-size: 14px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

.strategy-intro {
  .step-item {
    display: flex;
    gap: 12px;
    padding: 8px;
    border-radius: 8px;
    transition: all 0.2s;

    &:hover {
      background-color: #f5f7fa;
    }

    .step-number {
      flex-shrink: 0;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 16px;
    }

    .step-content {
      h4 {
        margin: 0 0 4px 0;
        font-size: 14px;
        color: #303133;
      }

      p {
        margin: 0;
        font-size: 12px;
        color: #909399;
        line-height: 1.5;
      }
    }
  }
}

.params-form {
  :deep(.el-form-item) {
    margin-bottom: 16px;
  }
}

.result-panel {
  .empty-state {
    padding: 40px 0;
  }

  .stock-code, .stock-name {
    cursor: pointer;
    color: #409eff;

    &:hover {
      text-decoration: underline;
    }
  }

  .price {
    font-weight: 500;
  }

  .pct {
    font-weight: 500;

    &.up {
      color: #f56c6c;
    }

    &.down {
      color: #67c23a;
    }
  }
}
</style>
