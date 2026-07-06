<template>
  <div class="filings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon class="title-icon"><Document /></el-icon>
        个股公告
        <span class="page-subtitle">汇总自选股的近期公告</span>
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
        共 <span class="status-num">{{ announcements.length }}</span> 条公告
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

    <!-- 公告列表 -->
    <div v-else class="filing-list" v-loading="loading">
      <div v-if="announcements.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无公告数据" />
      </div>
      <a
        v-for="(item, idx) in announcements"
        :key="idx"
        :href="item.url"
        target="_blank"
        rel="noopener noreferrer"
        class="filing-item"
      >
        <span class="filing-date">{{ item.date }}</span>
        <span class="filing-stock">{{ item.stockName }}</span>
        <span class="filing-type">{{ item.type || '-' }}</span>
        <span class="filing-title">{{ item.title }}</span>
        <el-icon class="link-icon"><Link /></el-icon>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Search, Refresh, Loading, Link } from '@element-plus/icons-vue'
import { vibeApi } from '@/api/vibe'
import { ApiClient } from '@/api/request'
import type { Announcement } from '@/api/vibe'

interface TrackedStock {
  code: string
  name: string
}

interface MergedAnnouncement extends Announcement {
  stockName: string
  stockCode: string
}

const loading = ref(false)
const manualCode = ref('')
const trackedStocks = ref<TrackedStock[]>([])
const announcements = ref<MergedAnnouncement[]>([])

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
  loadAnnouncements()
}

const removeStock = (code: string) => {
  trackedStocks.value = trackedStocks.value.filter(s => s.code !== code)
  loadAnnouncements()
}

const loadAnnouncements = async () => {
  if (trackedStocks.value.length === 0) {
    announcements.value = []
    return
  }
  loading.value = true
  const all: MergedAnnouncement[] = []
  try {
    await Promise.all(
      trackedStocks.value.map(async (s) => {
        try {
          const res = await vibeApi.getAnnouncements(s.code)
          const items = res.data || []
          for (const it of items) {
            all.push({ ...it, stockName: s.name || s.code, stockCode: s.code })
          }
        } catch (e) {
          // 单个股票失败不影响整体
        }
      })
    )
    // 按日期倒序
    all.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
    announcements.value = all.slice(0, 60)
  } finally {
    loading.value = false
  }
}

const loadAll = async () => {
  await loadFavorites()
  await loadAnnouncements()
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.filings-page {
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

/* 公告列表 */
.filing-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.filing-item {
  display: grid;
  grid-template-columns: 100px 110px 90px 1fr 24px;
  gap: 14px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  text-decoration: none;
  color: var(--el-text-color-primary);
  transition: background 0.15s ease;
  align-items: baseline;
}

.filing-item:hover {
  background: var(--el-fill-color-light);
}

.filing-item:last-child {
  border-bottom: none;
}

.filing-date {
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.filing-stock {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filing-type {
  font-size: 11px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  justify-self: start;
}

.filing-title {
  font-size: 14px;
  line-height: 1.5;
  transition: color 0.15s ease;
}

.filing-item:hover .filing-title {
  color: var(--el-color-primary);
}

.link-icon {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  transition: color 0.15s ease;
}

.filing-item:hover .link-icon {
  color: var(--el-color-primary);
}

@media (max-width: 720px) {
  .filing-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .link-icon {
    display: none;
  }
}
</style>
