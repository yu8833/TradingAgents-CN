<template>
  <div class="news-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon class="title-icon"><Reading /></el-icon>
        个股新闻
        <span class="page-subtitle">汇总自选股的近期新闻</span>
      </h1>
    </div>

    <!-- 输入栏 -->
    <div class="input-bar">
      <el-input
        v-model="manualCode"
        placeholder="输入6位股票代码，回车添加"
        maxlength="6"
        style="width: 260px;"
        @keyup.enter="addManualCode"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="addManualCode">添加</el-button>
      <el-button :loading="loading" :disabled="loading" @click="loadAll">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <div class="stock-tags" v-if="trackedStocks.length > 0">
        <el-tag
          v-for="s in trackedStocks"
          :key="s.code"
          size="small"
          closable
          @close="removeStock(s.code)"
          class="stock-tag"
        >
          {{ s.name || s.code }}
        </el-tag>
      </div>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-info">
        关注 <span class="status-num">{{ trackedStocks.length }}</span> 只
        <span class="status-sep">·</span>
        共 <span class="status-num">{{ newsList.length }}</span> 条新闻
      </div>
      <div v-if="loading" class="loading-hint">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && trackedStocks.length === 0" class="empty-state">
      <el-empty description="请先添加股票代码">
        <p class="empty-hint">在上方输入6位代码回车添加，或前往自选股页面添加</p>
      </el-empty>
    </div>

    <!-- 新闻列表 -->
    <div v-else class="news-list" v-loading="loading">
      <div v-if="newsList.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无新闻数据" />
      </div>
      <a
        v-for="(item, idx) in newsList"
        :key="idx"
        :href="item.新闻链接"
        target="_blank"
        rel="noopener noreferrer"
        class="news-item"
      >
        <span class="news-time">{{ item.发布时间 }}</span>
        <span class="news-stock">{{ item.stockName }}</span>
        <span class="news-title">{{ item.新闻标题 }}</span>
        <span class="news-source">{{ item.新闻来源 }}</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Reading, Search, Refresh, Loading } from '@element-plus/icons-vue'
import { vibeApi } from '@/api/vibe'
import { ApiClient } from '@/api/request'
import type { NewsItem } from '@/api/vibe'

interface TrackedStock {
  code: string
  name: string
}

interface MergedNews extends NewsItem {
  stockName: string
  stockCode: string
}

const loading = ref(false)
const manualCode = ref('')
const trackedStocks = ref<TrackedStock[]>([])
const newsList = ref<MergedNews[]>([])

const loadFavorites = async () => {
  try {
    const res = await ApiClient.get<any>('/api/favorites/')
    const list = res.data || []
    const mapped: TrackedStock[] = list
      .map((f: any) => ({
        code: String(f.stock_code || f.symbol || ''),
        name: f.stock_name || ''
      }))
      .filter((s: TrackedStock) => s.code)
    // 去重，保留已有的手动添加项
    const existCodes = new Set(trackedStocks.value.map(s => s.code))
    for (const s of mapped) {
      if (!existCodes.has(s.code)) {
        trackedStocks.value.push(s)
      }
    }
  } catch (e: any) {
    // 静默失败，用户可手动添加
    console.error('加载自选股失败', e)
  }
}

const addManualCode = () => {
  const code = manualCode.value.trim()
  if (!/^\d{6}$/.test(code)) {
    ElMessage.warning('请输入6位数字代码')
    return
  }
  if (trackedStocks.value.some(s => s.code === code)) {
    ElMessage.warning('该股票已在列表中')
    return
  }
  trackedStocks.value.push({ code, name: code })
  manualCode.value = ''
  loadNews()
}

const removeStock = (code: string) => {
  trackedStocks.value = trackedStocks.value.filter(s => s.code !== code)
  loadNews()
}

const loadNews = async () => {
  if (trackedStocks.value.length === 0) {
    newsList.value = []
    return
  }
  loading.value = true
  const all: MergedNews[] = []
  try {
    await Promise.all(
      trackedStocks.value.map(async (s) => {
        try {
          const res = await vibeApi.getNews(s.code)
          const items = res.data || []
          for (const it of items) {
            all.push({ ...it, stockName: s.name || s.code, stockCode: s.code })
          }
        } catch (e) {
          // 单个股票失败不影响整体
        }
      })
    )
    // 按发布时间倒序
    all.sort((a, b) => {
      const ta = new Date(a.发布时间).getTime()
      const tb = new Date(b.发布时间).getTime()
      return (tb || 0) - (ta || 0)
    })
    newsList.value = all
  } finally {
    loading.value = false
  }
}

const loadAll = async () => {
  await loadFavorites()
  await loadNews()
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.news-page {
  padding: 4px 8px;
  max-width: 1120px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.title-icon {
  color: var(--el-color-primary);
}

.page-subtitle {
  font-size: 13px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
  margin-left: 2px;
}

/* 输入栏 */
.input-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 14px 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  margin-bottom: 14px;
}

.stock-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  width: 100%;
  margin-top: 4px;
}

.stock-tag {
  border-radius: 4px;
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.status-num {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.status-sep {
  margin: 0 8px;
  color: var(--el-text-color-placeholder);
}

.loading-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--el-color-primary);
  font-size: 12px;
}

.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  padding: 60px 0;
}

.empty-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* 新闻列表 */
.news-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.news-item {
  display: grid;
  grid-template-columns: 150px 100px 1fr 110px;
  gap: 14px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  text-decoration: none;
  color: var(--el-text-color-primary);
  transition: background 0.15s ease;
  align-items: baseline;
}

.news-item:hover {
  background: var(--el-fill-color-light);
}

.news-item:last-child {
  border-bottom: none;
}

.news-time {
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.news-stock {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.news-title {
  font-size: 14px;
  line-height: 1.5;
  transition: color 0.15s ease;
}

.news-item:hover .news-title {
  color: var(--el-color-primary);
}

.news-source {
  font-size: 12px;
  color: var(--el-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

@media (max-width: 720px) {
  .news-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .news-source {
    text-align: left;
  }
}
</style>
