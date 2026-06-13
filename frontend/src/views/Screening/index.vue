<template>
  <div class="stock-screening">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Search /></el-icon>
        股票筛选
      </h1>
      <p class="page-description">
        通过多维度筛选条件，快速找到符合投资策略的优质股票
      </p>
    </div>

    <!-- 智能策略模板 -->
    <el-card class="templates-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-icon><MagicStick /></el-icon>
            <span>智能策略模板</span>
            <el-tag type="info" size="small" effect="plain">一键应用预设筛选条件</el-tag>
          </div>
        </div>
      </template>

      <el-row :gutter="16">
        <!-- 第1行：突破型 / 价值型 / 成长型 -->
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'breakout' }" @click="applyTemplate('breakout')">
            <div class="strategy-icon breakout"><el-icon><TrendCharts /></el-icon></div>
            <div class="strategy-info">
              <h3>突破型</h3>
              <p>放量上涨 + 高换手</p>
              <div class="strategy-tags">
                <el-tag size="small" type="warning">放量</el-tag>
                <el-tag size="small" type="danger">涨3%+</el-tag>
                <el-tag size="small" type="primary">换手5%+</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'value' }" @click="applyTemplate('value')">
            <div class="strategy-icon value"><el-icon><Wallet /></el-icon></div>
            <div class="strategy-info">
              <h3>价值型</h3>
              <p>低PE + 低PB + 大市值</p>
              <div class="strategy-tags">
                <el-tag size="small" type="warning">PE<15</el-tag>
                <el-tag size="small" type="success">PB<2</el-tag>
                <el-tag size="small" type="info">大盘股</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'growth' }" @click="applyTemplate('growth')">
            <div class="strategy-icon growth"><el-icon><Histogram /></el-icon></div>
            <div class="strategy-info">
              <h3>成长型</h3>
              <p>中小盘 + 高换手 + 合理估值</p>
              <div class="strategy-tags">
                <el-tag size="small" type="warning">中盘</el-tag>
                <el-tag size="small" type="danger">换手3%+</el-tag>
                <el-tag size="small" type="success">PE<50</el-tag>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px;">
        <!-- 第2行：动量型 / 低波动型 / 小盘成长 -->
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'momentum' }" @click="applyTemplate('momentum')">
            <div class="strategy-icon momentum"><el-icon><Lightning /></el-icon></div>
            <div class="strategy-info">
              <h3>动量型</h3>
              <p>涨幅领先 + 量能放大</p>
              <div class="strategy-tags">
                <el-tag size="small" type="danger">涨5%+</el-tag>
                <el-tag size="small" type="warning">高成交</el-tag>
                <el-tag size="small" type="primary">换手3%+</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'lowVolatility' }" @click="applyTemplate('lowVolatility')">
            <div class="strategy-icon lowvolatility"><el-icon><TrendCharts /></el-icon></div>
            <div class="strategy-info">
              <h3>低波动型</h3>
              <p>低估值 + 大盘股 + 波动小</p>
              <div class="strategy-tags">
                <el-tag size="small" type="info">大盘</el-tag>
                <el-tag size="small" type="success">低PE</el-tag>
                <el-tag size="small" type="warning">低换手</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'smallCapGrowth' }" @click="applyTemplate('smallCapGrowth')">
            <div class="strategy-icon smallcap"><el-icon><DataAnalysis /></el-icon></div>
            <div class="strategy-info">
              <h3>小盘成长</h3>
              <p>小市值 + 高换手</p>
              <div class="strategy-tags">
                <el-tag size="small" type="warning">小盘</el-tag>
                <el-tag size="small" type="danger">换手5%+</el-tag>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-top: 16px;">
        <!-- 第3行：蓝筹稳健 / 超低PB / 低价股 -->
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'blueChip' }" @click="applyTemplate('blueChip')">
            <div class="strategy-icon bluechip"><el-icon><Crop /></el-icon></div>
            <div class="strategy-info">
              <h3>蓝筹稳健</h3>
              <p>大市值 + 低估值 + 稳健换手</p>
              <div class="strategy-tags">
                <el-tag size="small" type="info">大盘</el-tag>
                <el-tag size="small" type="success">低PE</el-tag>
                <el-tag size="small" type="warning">稳健</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'superLowPB' }" @click="applyTemplate('superLowPB')">
            <div class="strategy-icon superlowpb"><el-icon><Money /></el-icon></div>
            <div class="strategy-info">
              <h3>超低PB</h3>
              <p>PB<1 破净股</p>
              <div class="strategy-tags">
                <el-tag size="small" type="success">PB<1</el-tag>
                <el-tag size="small" type="warning">破净</el-tag>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card" :class="{ active: activeTemplate === 'lowPrice' }" @click="applyTemplate('lowPrice')">
            <div class="strategy-icon lowprice"><el-icon><ShoppingCart /></el-icon></div>
            <div class="strategy-info">
              <h3>低价股</h3>
              <p>低价 + 正常PE</p>
              <div class="strategy-tags">
                <el-tag size="small" type="warning">股价<10</el-tag>
                <el-tag size="small" type="success">PE正常</el-tag>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 筛选条件面板 -->
    <el-card class="filter-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>筛选条件</span>
            <el-tag v-if="currentDataSource" type="info" size="small" effect="plain">
              <el-icon style="vertical-align: middle; margin-right: 4px;"><Connection /></el-icon>
              当前数据源: {{ currentDataSource.name }}
              <span v-if="currentDataSource.token_source_display" style="margin-left: 4px; opacity: 0.8;">
                ({{ currentDataSource.token_source_display }})
              </span>
            </el-tag>
            <el-tag v-else type="warning" size="small">
              <el-icon style="vertical-align: middle; margin-right: 4px;"><Warning /></el-icon>
              无可用数据源
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="text" @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="filters" label-width="120px" class="filter-form">
        <!-- 基础信息 -->
        <div class="filter-section">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            <span>基础信息</span>
          </div>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="市场类型">
                <el-select v-model="filters.market" placeholder="选择市场" disabled>
                  <el-option label="A股" value="A股" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="板块">
                <el-select v-model="filters.board" placeholder="选择板块">
                  <el-option label="全部" value="" />
                  <el-option label="主板" value="主板" />
                  <el-option label="创业板" value="创业板" />
                  <el-option label="科创板" value="科创板" />
                  <el-option label="北交所" value="北交所" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="市值范围">
                <el-select v-model="filters.marketCapRange" placeholder="选择市值范围">
                  <el-option label="小盘股 (< 100亿)" value="small" />
                  <el-option label="中盘股 (100-500亿)" value="medium" />
                  <el-option label="大盘股 (> 500亿)" value="large" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 交易指标 -->
        <div class="filter-section">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            <span>交易指标</span>
          </div>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="涨跌幅 (%)">
                <el-input-number
                  v-model="filters.changePercent.min"
                  placeholder="最小值"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.changePercent.max"
                  placeholder="最大值"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="换手率 (%)">
                <el-input-number
                  v-model="filters.turnoverRate.min"
                  placeholder="最小值"
                  :min="0"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.turnoverRate.max"
                  placeholder="最大值"
                  :min="0"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="量比">
                <el-input-number
                  v-model="filters.volumeRatio.min"
                  placeholder="最小值"
                  :min="0"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.volumeRatio.max"
                  placeholder="最大值"
                  :min="0"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="成交量">
                <el-select v-model="filters.volumeLevel" placeholder="选择成交量水平">
                  <el-option label="活跃 (高成交量)" value="high" />
                  <el-option label="正常 (中等成交量)" value="medium" />
                  <el-option label="清淡 (低成交量)" value="low" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 技术信号 -->
        <div class="filter-section">
          <div class="section-title">
            <el-icon><Search /></el-icon>
            <span>技术信号</span>
          </div>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="MACD金叉">
                <el-select v-model="filters.macdGoldenFork" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="KDJ金叉">
                <el-select v-model="filters.kdjGoldenFork" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item label="站上20日均线">
                <el-select v-model="filters.ma20Cross" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="站上5日均线">
                <el-select v-model="filters.ma5Cross" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 财务指标 -->
        <div class="filter-section">
          <div class="section-title">
            <el-icon><Money /></el-icon>
            <span>财务指标</span>
          </div>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="市盈率 PE">
                <el-input-number
                  v-model="filters.peRange.min"
                  placeholder="最小值"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.peRange.max"
                  placeholder="最大值"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="市净率 PB">
                <el-input-number
                  v-model="filters.pbRange.min"
                  placeholder="最小值"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.pbRange.max"
                  placeholder="最大值"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="收盘价 (元)">
                <el-input-number
                  v-model="filters.priceRange.min"
                  placeholder="最小值"
                  :precision="2"
                  style="width: 45%"
                />
                <span style="margin: 0 8px">-</span>
                <el-input-number
                  v-model="filters.priceRange.max"
                  placeholder="最大值"
                  :precision="2"
                  style="width: 45%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 筛选按钮 -->
        <el-row>
          <el-col :span="24">
            <div class="filter-actions">
              <el-button
                type="primary"
                @click="performScreening"
                :loading="screeningLoading"
                size="large"
              >
                <el-icon><Search /></el-icon>
                开始筛选
              </el-button>
              <el-button @click="resetFilters" size="large">
                重置条件
              </el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 筛选结果 -->
    <el-card v-if="screeningResults.length > 0" class="results-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <span>筛选结果 ({{ screeningResults.length }}只股票)</span>
          <div class="header-actions">
            <el-button
              type="primary"
              @click="batchAnalyze"
              :disabled="selectedStocks.length === 0"
            >
              <el-icon><TrendCharts /></el-icon>
              批量分析 ({{ selectedStocks.length }})
            </el-button>
            <el-button type="text" @click="exportResults">
              <el-icon><Download /></el-icon>
              导出结果
            </el-button>
          </div>
        </div>
      </template>

      <!-- 结果表格 -->
      <el-table
        :data="paginatedResults"
        row-key="code"
        @selection-change="handleSelectionChange"
        stripe
        border
        style="width: 100%"
        :default-sort="{ prop: sortField, order: sortOrder }"
        @sort-change="handleSortChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="code" label="股票代码" width="110">
          <template #default="{ row }">
            <el-link type="primary" @click="viewStockDetail(row)">
              {{ row.code }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="股票名称" width="120">
          <template #default="{ row }">
            <span>{{ row.name || row.code }}</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="close" 
          label="当前价格" 
          width="100" 
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.close" class="price-text">¥{{ row.close?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="pct_chg" 
          label="涨跌幅" 
          width="100" 
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.pct_chg !== null && row.pct_chg !== undefined" :class="getChangeClass(row.pct_chg)">
              {{ row.pct_chg > 0 ? '+' : '' }}{{ row.pct_chg?.toFixed(2) }}%
            </span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="total_mv" 
          label="总市值" 
          width="120" 
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.total_mv">{{ formatMarketCap(row.total_mv) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="circ_mv" 
          label="流通市值" 
          width="120" 
          align="right"
        >
          <template #default="{ row }">
            <span v-if="row.circ_mv">{{ formatMarketCap(row.circ_mv) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="turnover_rate" 
          label="换手率" 
          width="90" 
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.turnover_rate !== null && row.turnover_rate !== undefined">{{ row.turnover_rate?.toFixed(2) }}%</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          prop="volume_ratio" 
          label="量比" 
          width="80" 
          align="right"
          sortable="custom"
        >
          <template #default="{ row }">
            <span v-if="row.volume_ratio !== null && row.volume_ratio !== undefined">{{ row.volume_ratio?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="board" label="板块" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.board" size="small" type="info">{{ row.board }}</el-tag>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="analyzeSingle(row)">
              分析
            </el-button>
            <el-button type="success" link size="small" @click="addToTradingPool(row)">
              <el-icon><Plus /></el-icon>
              加入交易池
            </el-button>
            <el-button type="text" size="small" @click="toggleFavorite(row)">
              <el-icon><Star /></el-icon>
              {{ isFavorited(row.code) ? '取消自选' : '加入自选' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="screeningResults.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty
      v-else-if="!screeningLoading && hasSearched"
      description="未找到符合条件的股票"
      :image-size="200"
    >
      <el-button type="primary" @click="resetFilters">
        重新筛选
      </el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, TrendCharts, Download, Star, Connection, Warning, MagicStick, Wallet, Histogram, Lightning, DataAnalysis, Crop, Money, ShoppingCart, Plus } from '@element-plus/icons-vue'
import type { StockInfo } from '@/types/analysis'
import { screeningApi, type FieldConfigResponse } from '@/api/screening'
import { favoritesApi } from '@/api/favorites'
import { getCurrentDataSource } from '@/api/sync'
import { normalizeMarketForAnalysis, exchangeCodeToMarket, getMarketByStockCode } from '@/utils/market'

// 响应式数据
const screeningLoading = ref(false)
const hasSearched = ref(false)
const screeningResults = ref<StockInfo[]>([])
const selectedStocks = ref<StockInfo[]>([])
const currentPage = ref(1)
const pageSize = ref(20)

// 策略模板
const activeTemplate = ref<string>('')
const STRATEGY_TEMPLATES = {
  // 1. 突破型
  breakout: {
    name: '突破型',
    description: '放量上涨 + 高换手',
    conditions: {
      marketCapRange: '',
      changePercent: { min: 3, max: null },
      volumeLevel: 'high',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: 5, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: null, max: null },
      pbRange: { min: null, max: null },
      priceRange: { min: null, max: null },
    }
  },
  // 2. 价值型 - PE<15 + PB<2 + 大盘股
  value: {
    name: '价值型',
    description: '低PE + 低PB + 大市值',
    conditions: {
      marketCapRange: 'large',
      changePercent: { min: null, max: null },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: null, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 15 },
      pbRange: { min: 0.5, max: 2 },
      priceRange: { min: null, max: null },
    }
  },
  // 3. 成长型 - 中小盘 + 高换手 + 合理PB
  growth: {
    name: '成长型',
    description: '中小盘 + 高换手 + 合理估值',
    conditions: {
      marketCapRange: 'medium',
      changePercent: { min: 0, max: null },
      volumeLevel: 'medium',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: 3, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 50 },
      pbRange: { min: 1, max: 8 },
      priceRange: { min: null, max: null },
    }
  },
  // 4. 动量型 - 强势上涨 + 大成交量
  momentum: {
    name: '动量型',
    description: '涨幅领先 + 量能放大',
    conditions: {
      marketCapRange: '',
      changePercent: { min: 5, max: null },
      volumeLevel: 'high',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: 3, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: null, max: null },
      pbRange: { min: null, max: null },
      priceRange: { min: null, max: null },
    }
  },
  // 5. 低波动型 - 低PE + 低PB + 大盘股 + 跌幅可控
  lowVolatility: {
    name: '低波动型',
    description: '低估值 + 大盘股 + 波动小',
    conditions: {
      marketCapRange: 'large',
      changePercent: { min: -5, max: 5 },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: null, max: 2 },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 20 },
      pbRange: { min: 0.5, max: 3 },
      priceRange: { min: null, max: null },
    }
  },
  // 6. 小盘成长型 - 小市值 + 高换手
  smallCapGrowth: {
    name: '小盘成长',
    description: '小市值 + 高换手',
    conditions: {
      marketCapRange: 'small',
      changePercent: { min: 0, max: null },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: 5, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 80 },
      pbRange: { min: null, max: null },
      priceRange: { min: null, max: null },
    }
  },
  // 7. 蓝筹稳健型 - 大盘 + 低PE + 低PB + 低换手
  blueChip: {
    name: '蓝筹稳健',
    description: '大市值 + 低估值 + 稳健换手',
    conditions: {
      marketCapRange: 'large',
      changePercent: { min: -3, max: null },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: null, max: 3 },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 25 },
      pbRange: { min: 0.5, max: 4 },
      priceRange: { min: null, max: null },
    }
  },
  // 8. 超低PB型 - PB<1 (破净股)
  superLowPB: {
    name: '超低PB',
    description: 'PB<1 破净股',
    conditions: {
      marketCapRange: '',
      changePercent: { min: null, max: null },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: null, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 100 },
      pbRange: { min: 0, max: 1 },
      priceRange: { min: null, max: null },
    }
  },
  // 9. 低价股型 - 低股价 + 合理PE
  lowPrice: {
    name: '低价股',
    description: '低价 + 正常PE',
    conditions: {
      marketCapRange: '',
      changePercent: { min: null, max: null },
      volumeLevel: '',
      macdGoldenFork: '',
      kdjGoldenFork: '',
      ma20Cross: '',
      ma5Cross: '',
      turnoverRate: { min: null, max: null },
      volumeRatio: { min: null, max: null },
      board: '',
      peRange: { min: 0, max: 60 },
      pbRange: { min: null, max: null },
      priceRange: { min: 0, max: 10 },
    }
  },
} as const

// 排序状态
const sortField = ref('total_mv')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 路由 & 自选集
const router = useRouter()
const favoriteSet = ref<Set<string>>(new Set())

// 当前数据源
const currentDataSource = ref<{
  name: string
  priority: number
  description: string
  token_source?: 'database' | 'env'
  token_source_display?: string
} | null>(null)

// 字段配置
const fieldConfig = ref<FieldConfigResponse | null>(null)
const fieldsLoading = ref(false)

// 筛选条件
const filters = reactive({
  market: 'A股',
  marketCapRange: '',
  changePercent: { min: null, max: null },
  volumeLevel: '',
  // 标志筛选条件
  macdGoldenFork: '',  // MACD金叉：是/否/空(全部)
  kdjGoldenFork: '',   // KDJ金叉
  ma20Cross: '',       // 站上20日均线
  ma5Cross: '',        // 站上5日均线
  // 扩展筛选条件
  turnoverRate: { min: null, max: null },  // 换手率区间(%)
  volumeRatio: { min: null, max: null },   // 量比区间
  board: '',                                // 板块（主板/创业板/科创板/北交所）
  // 财务指标区间
  peRange: { min: null, max: null },        // PE 区间
  pbRange: { min: null, max: null },        // PB 区间
  priceRange: { min: null, max: null },     // 收盘价区间
})

// 行业选项（动态加载）
const industryOptions = ref<Array<{label: string, value: string, count?: number}>>([])

// 计算属性
const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return screeningResults.value.slice(start, end)
})

// 方法
const performScreening = async () => {
  screeningLoading.value = true
  hasSearched.value = true

  try {
    // 基于用户真实选择构建 conditions（只拼选中的项，不注入默认技术条件）
    const children: any[] = []

    // 市值范围映射为区间（单位：亿元，与数据库一致）
    const capRangeMap: Record<string, [number, number] | null> = {
      small: [0, 100],
      medium: [100, 500],
      large: [500, Number.MAX_SAFE_INTEGER],
    }
    const cap = filters.marketCapRange ? capRangeMap[filters.marketCapRange] : null
    if (cap) {
      children.push({ field: 'total_mv', op: 'between', value: cap })
    }

    // 涨跌幅条件
    if (filters.changePercent.min != null || filters.changePercent.max != null) {
      const lo = filters.changePercent.min ?? -100
      const hi = filters.changePercent.max ?? 100
      children.push({ field: 'pct_chg', op: 'between', value: [lo, hi] })
    }

    // 成交量条件（映射为成交额范围，单位：元）
    if (filters.volumeLevel) {
      const volumeRangeMap: Record<string, [number, number]> = {
        high: [1000000000, Number.MAX_SAFE_INTEGER],    // 高成交量：>10亿元
        medium: [300000000, 1000000000],                 // 中等成交量：3亿-10亿元
        low: [0, 300000000]                              // 低成交量：<3亿元
      }
      const volumeRange = volumeRangeMap[filters.volumeLevel]
      if (volumeRange) {
        children.push({ field: 'amount', op: 'between', value: volumeRange })
      }
    }

    // 标志筛选条件（MACD金叉、KDJ金叉等）
    const flagConditions: Record<string, string> = {
      macdGoldenFork: 'macd_golden_fork',
      kdjGoldenFork: 'kdj_golden_fork',
      ma20Cross: 'ma20_cross',
      ma5Cross: 'ma5_cross',
    }
    
    for (const [filterKey, fieldName] of Object.entries(flagConditions)) {
      const value = filters[filterKey as keyof typeof filters]
      if (value === 'Y') {
        children.push({ field: fieldName, op: 'eq', value: true })
      } else if (value === 'N') {
        children.push({ field: fieldName, op: 'eq', value: false })
      }
    }

    // 扩展筛选条件
    // 换手率区间
    if (filters.turnoverRate.min != null || filters.turnoverRate.max != null) {
      const lo = filters.turnoverRate.min ?? 0
      const hi = filters.turnoverRate.max ?? 100
      children.push({ field: 'turnover_rate', op: 'between', value: [lo, hi] })
    }

    // 量比区间
    if (filters.volumeRatio.min != null || filters.volumeRatio.max != null) {
      const lo = filters.volumeRatio.min ?? 0
      const hi = filters.volumeRatio.max ?? 100
      children.push({ field: 'volume_ratio', op: 'between', value: [lo, hi] })
    }

    // 板块筛选（数据库字段为 market，值为 "主板"/"创业板" 等）
    if (filters.board) {
      children.push({ field: 'market', op: 'eq', value: filters.board })
    }

    // PE 区间
    if (filters.peRange.min != null || filters.peRange.max != null) {
      const lo = filters.peRange.min ?? -100000
      const hi = filters.peRange.max ?? 100000
      children.push({ field: 'pe', op: 'between', value: [lo, hi] })
    }

    // PB 区间
    if (filters.pbRange.min != null || filters.pbRange.max != null) {
      const lo = filters.pbRange.min ?? -10000
      const hi = filters.pbRange.max ?? 10000
      children.push({ field: 'pb', op: 'between', value: [lo, hi] })
    }

    // 收盘价区间
    if (filters.priceRange.min != null || filters.priceRange.max != null) {
      const lo = filters.priceRange.min ?? 0
      const hi = filters.priceRange.max ?? 10000
      children.push({ field: 'close', op: 'between', value: [lo, hi] })
    }

    const payload = {
      market: 'CN' as const,
      date: undefined,
      adj: 'qfq' as const,
      conditions: { logic: 'AND', children },
      order_by: [{ field: sortField.value, direction: sortOrder.value as const }],
      limit: 500,
      offset: 0,
    }

    // 调试日志：打印请求payload
    console.log('🔍 筛选请求 payload:', JSON.stringify(payload, null, 2))
    console.log('🔍 筛选条件 children:', children)

    const res = await screeningApi.run(payload, { timeout: 120000 })
    const data = (res as any)?.data || res // ApiClient封装会返回 {success,data} 格式
    const items = data?.items || []

    // 调试日志：打印返回数据示例
    if (items.length > 0) {
      console.log('🔍 后端返回数据示例:', JSON.stringify(items[0], null, 2))
    }

    // 直接使用后端返回的数据，字段名已统一
    screeningResults.value = items.map((it: any) => ({
      symbol: it.code || it.symbol || '',  // 股票代码
      code: it.code || it.symbol || '',    // 兼容字段
      name: it.name || it.stock_name || it.code || '',  // 使用股票名称
      market: it.market || 'A股',
      industry: it.industry || '',
      area: it.area || '',
      board: it.board || '',  // 板块（主板、创业板、科创板等）

      // 市值信息
      total_mv: it.total_mv,
      circ_mv: it.circ_mv,

      // 财务指标
      pe: it.pe,
      pb: it.pb,
      pe_ttm: it.pe_ttm,
      pb_mrq: it.pb_mrq,
      roe: it.roe,

      // 交易数据
      close: it.close,
      pct_chg: it.pct_chg,
      amount: it.amount,
      turnover_rate: it.turnover_rate,
      volume_ratio: it.volume_ratio,

      // 技术指标
      ma20: it.ma20,
      rsi14: it.rsi14,
      kdj_k: it.kdj_k,
      kdj_d: it.kdj_d,
      kdj_j: it.kdj_j,
      dif: it.dif,
      dea: it.dea,
      macd_hist: it.macd_hist,
    }))

    ElMessage.success(`筛选完成，找到 ${screeningResults.value.length} 只股票`)
  } catch (error) {
    ElMessage.error('筛选失败，请重试')
  } finally {
    screeningLoading.value = false
  }
}

const applyTemplate = (templateKey: string) => {
  const template = (STRATEGY_TEMPLATES as any)[templateKey]
  if (!template) return

  activeTemplate.value = templateKey
  Object.assign(filters, {
    market: 'A股',
    ...template.conditions
  })

  ElMessage.info(`已应用【${template.name}】策略模板，请点击"开始筛选"查看结果`)
}

const resetFilters = () => {
  activeTemplate.value = ''
  Object.assign(filters, {
    market: 'A股',
    marketCapRange: '',
    changePercent: { min: null, max: null },
    volumeLevel: '',
    // 标志筛选条件重置
    macdGoldenFork: '',
    kdjGoldenFork: '',
    ma20Cross: '',
    ma5Cross: '',
    // 扩展筛选条件重置
    turnoverRate: { min: null, max: null },
    volumeRatio: { min: null, max: null },
    board: '',
    // 财务指标区间重置
    peRange: { min: null, max: null },
    pbRange: { min: null, max: null },
    priceRange: { min: null, max: null },
  })

  screeningResults.value = []
  selectedStocks.value = []
  hasSearched.value = false
  currentPage.value = 1
}

const handleSelectionChange = (selection: StockInfo[]) => {
  selectedStocks.value = selection
}

const batchAnalyze = async () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请先选择要分析的股票')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要对选中的 ${selectedStocks.value.length} 只股票进行批量分析吗？`,
      '确认批量分析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    // 跳转到批量分析页面（携带统一市场参数）
    router.push({
      name: 'BatchAnalysis',
      query: {
        stocks: selectedStocks.value.map(s => s.code || s.symbol || '').filter(Boolean).join(','),
        market: normalizeMarketForAnalysis(filters.market)
      }
    })
  } catch {
    // 用户取消
  }
}


const analyzeSingle = (stock: StockInfo) => {
  const stockCode = stock.code || stock.symbol || ''
  if (!stockCode) return
  router.push({
    name: 'SingleAnalysis',
    query: {
      stock: stockCode,
      market: normalizeMarketForAnalysis((stock as any).market || filters.market)
    }
  })
}

const viewStockDetail = (stock: StockInfo) => {
  const stockCode = stock.code || stock.symbol || ''
  if (!stockCode) return
  // 跳转到股票详情页面
  router.push({
    name: 'StockDetail',
    params: { code: stockCode }
  })
}

const isFavorited = (code: string) => favoriteSet.value.has(code)

const toggleFavorite = async (stock: StockInfo) => {
  try {
    const code = stock.code || stock.symbol || ''
    if (!code) {
      ElMessage.error('股票代码缺失，无法加入自选')
      return
    }
    if (favoriteSet.value.has(code)) {
      // 取消自选
      const res = await favoritesApi.remove(code)
      if ((res as any)?.success === false) throw new Error((res as any)?.message || '取消失败')
      favoriteSet.value.delete(code)
      ElMessage.success(`已取消自选：${stock.name || code}`)
    } else {
      // 加入自选
      // 根据股票代码判断市场类型
      let marketType = 'A股'
      if ((stock as any).market) {
        // 如果有 market 字段，尝试转换（可能是交易所代码如 "sz", "sh"）
        marketType = exchangeCodeToMarket((stock as any).market)
      } else {
        // 否则根据股票代码判断
        marketType = getMarketByStockCode(code)
      }

      const payload = {
        symbol: code,
        stock_code: code,  // 兼容字段
        stock_name: stock.name || code,
        market: marketType
      }
      const res = await favoritesApi.add(payload)
      if ((res as any)?.success === false) throw new Error((res as any)?.message || '添加失败')
      favoriteSet.value.add(code)
      ElMessage.success(`已加入自选：${stock.name || code}`)
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '自选操作失败')
  }
}

const addToTradingPool = async (stock: StockInfo) => {
  try {
    const code = stock.code || stock.symbol || ''
    if (!code) {
      ElMessage.error('股票代码缺失，无法加入交易池')
      return
    }

    const response = await fetch('/api/three-buy-three-sell/trading-pool/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stock_code: code,
        pool_type: 'buy_candidate',
        stock_name: stock.name || code,
        entry_price: stock.close || null
      })
    })

    const data = await response.json()
    if (data.success) {
      ElMessage.success(`已将 ${stock.name || code} 加入买入候选池`)
    } else {
      ElMessage.error(data.message || '加入交易池失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '加入交易池失败')
  }
}

const exportResults = () => {
  // 导出筛选结果
  ElMessage.info('导出功能开发中...')
}

const getChangeClass = (changePercent: number) => {
  if (changePercent > 0) return 'text-red'
  if (changePercent < 0) return 'text-green'
  return ''
}

const formatMarketCap = (marketCap: number) => {
  if (marketCap >= 10000) {
    return `${(marketCap / 10000).toFixed(2)}万亿`
  } else {
    return `${marketCap.toFixed(2)}亿`
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

// 获取字段配置
const loadFieldConfig = async () => {
  fieldsLoading.value = true
  try {
    const response = await screeningApi.getFields()
    fieldConfig.value = response.data || response
    console.log('字段配置加载成功:', fieldConfig.value)
  } catch (error) {
    console.error('加载字段配置失败:', error)
    ElMessage.error('加载字段配置失败')
  } finally {
    fieldsLoading.value = false
  }
}

// 加载行业列表
const loadIndustries = async () => {
  try {
    const response = await screeningApi.getIndustries()
    const data = response.data || response
    industryOptions.value = data.industries || []
    console.log('行业列表加载成功:', industryOptions.value.length, '个行业')
  } catch (error) {
    console.error('加载行业列表失败:', error)
    ElMessage.error('加载行业列表失败')
    // 如果加载失败，使用默认的行业列表
    industryOptions.value = [
      { label: '银行', value: '银行' },
      { label: '证券', value: '证券' },
      { label: '保险', value: '保险' },
      { label: '房地产', value: '房地产' },
      { label: '医药生物', value: '医药生物' }
    ]
  }
}

// 加载自选列表，初始化 favoriteSet
const loadFavorites = async () => {
  try {
    const resp = await favoritesApi.list()
    const list = (resp as any)?.data || resp
    const set = new Set<string>()
    ;(list || []).forEach((item: any) => {
      // 兼容新旧字段
      const code = item.symbol || item.stock_code || item.code
      if (code) set.add(code)
    })
    favoriteSet.value = set
  } catch (e) {
    console.warn('加载自选列表失败，可能未登录或接口不可用。', e)
  }
}

// 获取当前数据源
const loadCurrentDataSource = async () => {
  try {
    const response = await getCurrentDataSource()
    if (response.success && response.data) {
      currentDataSource.value = response.data
    }
  } catch (e) {
    console.warn('获取当前数据源失败', e)
  }
}

// 表头排序处理
const handleSortChange = (column: any) => {
  const field = column.prop
  if (!field) return
  
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
  
  // 重新执行筛选
  performScreening()
}

// 获取排序图标
const getSortIcon = (field: string) => {
  if (sortField.value === field) {
    return sortOrder.value === 'asc' ? 'arrow-up' : 'arrow-down'
  }
  return ''
}

// 生命周期
onMounted(() => {
  // 加载字段配置和行业列表
  loadFieldConfig()
  loadIndustries()
  // 初始化自选状态
  loadFavorites()
  // 加载当前数据源
  loadCurrentDataSource()
})
</script>

<style lang="scss" scoped>
.stock-screening {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;

  .templates-panel {
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(135deg, #e6f4ff 0%, #f0e6ff 100%);
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-lighter);
    }

    .card-header {
      span {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }

    :deep(.el-card__body) {
      padding: 20px;
    }

    .strategy-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px;
      background: var(--el-fill-color-light);
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 2px solid transparent;

      &:hover {
        background: var(--el-fill-color-lighter);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }

      &.active {
        border-color: var(--el-color-primary);
        background: linear-gradient(135deg, #409eff1a 0%, #67c23a1a 100%);
      }

      .strategy-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        color: white;
        flex-shrink: 0;

        &.breakout {
          background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
        }
        &.value {
          background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
        }
        &.growth {
          background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
        }
        &.momentum {
          background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        }
        &.lowvolatility {
          background: linear-gradient(135deg, #0097a7 0%, #006064 100%);
        }
        &.smallcap {
          background: linear-gradient(135deg, #ff6f00 0%, #e65100 100%);
        }
        &.bluechip {
          background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
        }
        &.superlowpb {
          background: linear-gradient(135deg, #388e3c 0%, #1b5e20 100%);
        }
        &.lowprice {
          background: linear-gradient(135deg, #795548 0%, #5d4037 100%);
        }
      }

      .strategy-info {
        flex: 1;
        min-width: 0;

        h3 {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 700;
          color: var(--el-text-color-primary);
        }

        p {
          margin: 0 0 10px 0;
          font-size: 13px;
          color: var(--el-text-color-regular);
          line-height: 1.4;
        }

        .strategy-tags {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }
      }
    }
  }

  .page-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 2px solid var(--el-border-color-lighter);

    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;

      .el-icon {
        color: var(--el-color-primary);
        font-size: 28px;
      }
    }

    .page-description {
      color: var(--el-text-color-regular);
      margin: 0;
      font-size: 14px;
    }
  }

  .filter-panel {
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-lighter);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      span {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .filter-form {
      padding: 20px;

      .filter-section {
        margin-bottom: 24px;
        padding: 16px;
        background: var(--el-fill-color-light);
        border-radius: 8px;
        transition: all 0.3s ease;

        &:hover {
          background: var(--el-fill-color-lighter);
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        }

        &:last-of-type {
          margin-bottom: 0;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 15px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 16px;
          padding-bottom: 10px;
          border-bottom: 2px solid var(--el-color-primary-light-5);

          .el-icon {
            color: var(--el-color-primary);
            font-size: 18px;
          }
        }
      }

      .filter-actions {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px dashed var(--el-border-color);

        .el-button {
          min-width: 140px;
          height: 42px;
          font-size: 15px;
          border-radius: 8px;
        }
      }
    }
  }

  .results-panel {
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(135deg, #67c23a0d 0%, #85ce610d 100%);
      padding: 16px 20px;
      border-bottom: 1px solid var(--el-border-color-lighter);
    }

    :deep(.el-table) {
      font-size: 14px;

      th {
        background-color: var(--el-fill-color-light) !important;
        color: var(--el-text-color-primary);
        font-weight: 600;
      }

      td {
        padding: 12px 0;
      }

      .el-table__row:hover {
        background-color: var(--el-fill-color-light);
      }
    }

    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 24px;
      padding: 16px 0;
    }
  }

  .text-red {
    color: #f56c6c;
    font-weight: 600;
  }

  .text-green {
    color: #67c23a;
    font-weight: 600;
  }

  .price-text {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}
</style>
