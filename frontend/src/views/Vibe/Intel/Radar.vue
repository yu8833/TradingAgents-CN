<template>
  <div class="radar-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon class="title-icon"><DataLine /></el-icon>
        赛道资讯
        <span class="page-subtitle">12赛道全球公开RSS资讯</span>
      </h1>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-info">
        <span class="status-num">{{ stats.total_sources }}</span> 个公开源
        <span class="status-sep">·</span>
        近 <span class="status-num">{{ radarData?.recent_days ?? '-' }}</span> 天
        <span class="status-sep">·</span>
        更新于 <span class="status-time">{{ radarData?.generated_at || '-' }}</span>
      </div>
      <div class="status-actions">
        <el-button
          type="warning"
          plain
          :loading="distillAllLoading"
          :disabled="distillAllLoading || loading"
          @click="distillAll"
        >
          <el-icon><MagicStick /></el-icon>
          <span v-if="distillAllLoading">提炼中 {{ distillAllDone }}/{{ distillAllTotal }}</span>
          <span v-else>一键提炼全部要点</span>
        </el-button>
        <el-button :loading="refreshing" :disabled="refreshing" @click="refresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 赛道筛选 -->
    <div class="industry-pills" v-loading="loading">
      <button
        v-for="ind in industries"
        :key="ind.key"
        class="pill"
        :class="{ active: ind.key === currentKey }"
        @click="switchIndustry(ind.key)"
      >
        <span class="dot" :style="{ background: ind.accent }"></span>
        <span class="pill-name">{{ ind.name }}</span>
        <span class="pill-count">{{ ind.total }}</span>
      </button>
    </div>

    <!-- 今日要点总结框 -->
    <div class="summary-box">
      <div class="summary-head">
        <div class="summary-title">
          <el-icon><MagicStick /></el-icon>
          今日要点<span v-if="currentIndustry"> · {{ currentIndustry.name }}</span>
        </div>
        <div class="summary-actions" v-if="summaryState === 'done'">
          <el-button size="small" type="primary" plain @click="saveSummary">
            <el-icon><EditPen /></el-icon>
            存入沉淀
          </el-button>
          <el-button size="small" link @click="resetSummary">重新提炼</el-button>
        </div>
      </div>
      <div class="summary-body">
        <div v-if="summaryState === 'idle'" class="summary-idle">
          <el-button type="warning" @click="distillCurrent">
            <el-icon><MagicStick /></el-icon>
            让 AI 提炼今日要点
          </el-button>
        </div>
        <div
          v-else-if="summaryState === 'loading' || summaryState === 'done'"
          class="summary-text"
          :class="{ streaming: summaryState === 'loading' }"
        >
          {{ currentSummary || '...' }}
          <span v-if="summaryState === 'loading'" class="cursor">▌</span>
        </div>
        <div v-if="summaryError" class="summary-error">
          <el-icon><Warning /></el-icon>
          {{ summaryError }}
        </div>
      </div>
    </div>

    <!-- 资讯列表 -->
    <div class="news-list" v-loading="loading">
      <div class="list-head">
        <el-icon><Reading /></el-icon>
        <span>资讯列表</span>
        <span class="list-count">共 {{ currentItems.length }} 条</span>
      </div>
      <div v-if="currentItems.length === 0 && !loading" class="empty">
        <el-empty description="该赛道暂无资讯" />
      </div>
      <a
        v-for="(item, idx) in currentItems"
        :key="idx"
        :href="item.url"
        target="_blank"
        rel="noopener noreferrer"
        class="news-item"
      >
        <span class="news-time">{{ item.time }}</span>
        <span class="news-source">{{ item.source }}</span>
        <span class="news-title">{{ item.title }}</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataLine,
  Refresh,
  MagicStick,
  Reading,
  EditPen,
  Warning
} from '@element-plus/icons-vue'
import { vibeApi } from '@/api/vibe'
import type { RadarData, Industry, RadarItem } from '@/api/vibe'

const loading = ref(false)
const refreshing = ref(false)
const radarData = ref<RadarData | null>(null)

const currentKey = ref('')
const industries = computed<Industry[]>(() => radarData.value?.industries ?? [])
const stats = computed(() => radarData.value?.stats ?? { industries: 0, total_sources: 0 })

const currentIndustry = computed<Industry | undefined>(() =>
  industries.value.find(i => i.key === currentKey.value)
)

const currentItems = computed<RadarItem[]>(() => {
  if (!currentIndustry.value) return []
  return [...currentIndustry.value.items].sort((a, b) => {
    const ta = a.ts ?? new Date(a.time).getTime()
    const tb = b.ts ?? new Date(b.time).getTime()
    return (tb || 0) - (ta || 0)
  })
})

// 今日要点总结
type SummaryState = 'idle' | 'loading' | 'done'
const summaryState = ref<SummaryState>('idle')
const currentSummary = ref('')
const summaryError = ref('')
const summaryCache = ref<Record<string, string>>({})

// 一键提炼全部
const distillAllLoading = ref(false)
const distillAllDone = ref(0)
const distillAllTotal = ref(0)

const sortByTime = (items: RadarItem[]): RadarItem[] =>
  [...items].sort((a, b) => {
    const ta = a.ts ?? new Date(a.time).getTime()
    const tb = b.ts ?? new Date(b.time).getTime()
    return (tb || 0) - (ta || 0)
  })

const buildPrompt = (ind: Industry): string => {
  const list = sortByTime(ind.items)
    .slice(0, 20)
    .map(it => `- [${it.time}] ${it.title} (${it.source})`)
    .join('\n')
  return `以下是「${ind.name}」赛道近期资讯。请提炼「今日要点」3-5 条：每条一句话（≤40 字），只客观陈述重要事件/趋势，不推荐标的、不预测涨跌、不构成建议。直接用「- 」列点。\n\n资讯列表：\n${list}`
}

const distillCurrent = async () => {
  const ind = currentIndustry.value
  if (!ind || ind.items.length === 0) {
    ElMessage.warning('当前赛道暂无资讯')
    return
  }
  summaryState.value = 'loading'
  currentSummary.value = ''
  summaryError.value = ''
  try {
    await vibeApi.chatStream(
      [{ role: 'user', content: buildPrompt(ind) }],
      'radar',
      (delta) => { currentSummary.value += delta },
      (msg) => { summaryError.value = msg }
    )
    summaryCache.value[ind.key] = currentSummary.value
    summaryState.value = 'done'
  } catch (e: any) {
    summaryError.value = e?.message || '提炼失败'
    summaryState.value = 'idle'
  }
}

const resetSummary = () => {
  summaryState.value = 'idle'
  currentSummary.value = ''
  summaryError.value = ''
}

const saveSummary = () => {
  const ind = currentIndustry.value
  if (!ind || !currentSummary.value) return
  vibeApi.saveNote('今日要点', `赛道资讯·${ind.name}·今日要点`, currentSummary.value)
  ElMessage.success('已存入研究记录')
}

const distillAll = async () => {
  const targets = industries.value.filter(i => i.items.length > 0)
  if (targets.length === 0) {
    ElMessage.warning('暂无可提炼的赛道')
    return
  }
  distillAllLoading.value = true
  distillAllDone.value = 0
  distillAllTotal.value = targets.length
  try {
    for (const ind of targets) {
      let text = ''
      try {
        await vibeApi.chatStream(
          [{ role: 'user', content: buildPrompt(ind) }],
          'radar',
          (delta) => { text += delta }
        )
        if (text) {
          vibeApi.saveNote('今日要点', `赛道资讯·${ind.name}·今日要点`, text)
          summaryCache.value[ind.key] = text
          if (ind.key === currentKey.value) {
            currentSummary.value = text
            summaryState.value = 'done'
          }
        }
      } catch (e) {
        // 单个赛道失败继续下一个
      }
      distillAllDone.value++
    }
    ElMessage.success(`已提炼 ${distillAllDone.value} 个赛道并存入研究记录`)
  } finally {
    distillAllLoading.value = false
  }
}

const switchIndustry = (key: string) => {
  currentKey.value = key
}

// 切换赛道时恢复该赛道的缓存总结
watch(currentKey, (key) => {
  if (summaryCache.value[key]) {
    currentSummary.value = summaryCache.value[key]
    summaryState.value = 'done'
  } else {
    currentSummary.value = ''
    summaryState.value = 'idle'
  }
  summaryError.value = ''
})

const loadRadar = async () => {
  loading.value = true
  try {
    const res = await vibeApi.getRadar()
    radarData.value = res.data
    if (!currentKey.value && industries.value.length > 0) {
      currentKey.value = industries.value[0].key
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载资讯失败')
  } finally {
    loading.value = false
  }
}

const refresh = async () => {
  refreshing.value = true
  try {
    const res = await vibeApi.refreshRadar()
    radarData.value = res.data
    ElMessage.success('已刷新')
  } catch (e: any) {
    ElMessage.error(e?.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadRadar()
})
</script>

<style scoped>
.radar-page {
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

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  margin-bottom: 18px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.status-num {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.status-sep {
  margin: 0 8px;
  color: var(--el-text-color-placeholder);
}

.status-time {
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
}

.status-actions {
  display: flex;
  gap: 8px;
}

/* 赛道 pill 筛选 */
.industry-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  min-height: 36px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 999px;
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.pill:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.pill.active {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}

.pill.active .dot {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.55);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pill-count {
  font-size: 11px;
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 7px;
  border-radius: 10px;
  line-height: 1.6;
}

.pill.active .pill-count {
  background: rgba(255, 255, 255, 0.28);
}

/* 今日要点总结框（暖橙边框） */
.summary-box {
  border: 1.5px solid #e8722c;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(232, 114, 44, 0.05), rgba(232, 114, 44, 0.01));
}

.summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #c75c1c;
  font-size: 15px;
}

.summary-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-body {
  min-height: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-idle {
  display: flex;
  align-items: center;
}

.summary-text {
  white-space: pre-wrap;
  line-height: 1.85;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.summary-text.streaming {
  color: var(--el-text-color-regular);
}

.cursor {
  animation: blink 1s steps(2) infinite;
  color: #e8722c;
  font-weight: 600;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.summary-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--el-color-danger);
  font-size: 13px;
  margin-top: 8px;
}

/* 资讯列表 */
.news-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.list-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.list-count {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: var(--el-text-color-secondary);
}

.empty {
  padding: 40px 0;
}

.news-item {
  display: grid;
  grid-template-columns: 150px 110px 1fr;
  gap: 16px;
  padding: 11px 16px;
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

.news-source {
  font-size: 12px;
  color: var(--el-color-primary);
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

@media (max-width: 720px) {
  .news-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
