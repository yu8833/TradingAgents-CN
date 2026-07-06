<template>
  <div class="sector-detail-page">
    <div class="back-link" @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      <span>全部板块</span>
    </div>

    <div v-loading="loading" class="detail-body">
      <template v-if="sector">
        <div class="page-header">
          <h1 class="page-title">{{ sector.label }}</h1>
          <p class="page-tagline">{{ sector.tagline || '—' }}</p>
        </div>

        <div class="action-bar">
          <el-button
            type="primary"
            :loading="aiLoading"
            :disabled="aiLoading"
            @click="runAiAnalysis"
          >
            <el-icon v-if="!aiLoading"><MagicStick /></el-icon>
            让 AI 拆这个板块
          </el-button>
          <el-button
            v-if="aiResult && !aiLoading"
            type="success"
            plain
            @click="saveToNotes"
          >
            <el-icon><Plus /></el-icon>
            存入沉淀
          </el-button>
        </div>

        <el-card v-if="aiResult || aiLoading" class="ai-output-card" shadow="never">
          <div v-if="aiLoading && !aiResult" class="ai-streaming">
            <span class="stream-cursor">AI 正在拆解</span>
            <span class="dots">...</span>
          </div>
          <div
            v-else
            class="ai-output"
            v-html="renderedAi"
          ></div>
        </el-card>

        <div class="section-title">核心环节</div>
        <div v-if="sector.verified" class="nodes-cloud">
          <el-tag
            v-for="node in sector.nodes"
            :key="node"
            class="node-pill"
            effect="plain"
            round
          >
            {{ node }}
          </el-tag>
          <span v-if="!sector.nodes.length" class="nodes-empty">
            暂无环节
          </span>
        </div>
        <el-alert
          v-else
          class="pending-alert"
          type="info"
          :closable="false"
          show-icon
        >
          环节骨架尚在实时核实补全中
        </el-alert>
      </template>

      <el-empty
        v-else-if="!loading"
        description="未找到该板块"
      />
    </div>

    <p class="disclaimer">
      只有环节，不含标的。用户可在本地挂自己的标的。
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, MagicStick, Plus } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { vibeApi } from '@/api/vibe'
import type { SectorNode } from '@/api/vibe'

marked.setOptions({ breaks: true, gfm: true })

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const aiLoading = ref(false)
const sector = ref<SectorNode | null>(null)
const aiResult = ref('')

const renderedAi = computed(() => {
  if (!aiResult.value) return ''
  try {
    return String(marked.parse(aiResult.value))
  } catch {
    return aiResult.value.replace(/\n/g, '<br/>')
  }
})

const sectorKey = computed(() => String(route.params.key || ''))

const loadSector = async () => {
  loading.value = true
  try {
    const res = await vibeApi.getSectors()
    const list = res?.data?.sectors || []
    sector.value = list.find(s => s.key === sectorKey.value) || null
    if (!sector.value) {
      ElMessage.warning('未找到该板块')
    }
  } catch (e: any) {
    console.error('加载板块失败:', e)
    ElMessage.error(e?.message || '加载板块失败')
  } finally {
    loading.value = false
  }
}

const buildPrompt = (s: SectorNode) => {
  return [
    `板块：${s.label}`,
    `定位：${s.tagline || '—'}`,
    `产业链环节：${(s.nodes || []).join('、') || '（环节梳理中）'}`,
    '请用中文分析这个板块的产业链结构、关键环节、卡脖子点。不推荐标的、不预测涨跌。',
  ].join('\n')
}

const runAiAnalysis = async () => {
  if (!sector.value || aiLoading.value) return
  aiLoading.value = true
  aiResult.value = ''
  const prompt = buildPrompt(sector.value)
  try {
    await vibeApi.chatStream(
      [{ role: 'user', content: prompt }],
      'sector_analysis',
      (delta: string) => {
        aiResult.value += delta
      },
      (msg: string) => {
        ElMessage.error(msg || 'AI 分析出错')
      }
    )
  } catch (e: any) {
    console.error('AI 分析失败:', e)
    ElMessage.error(e?.message || 'AI 分析失败')
  } finally {
    aiLoading.value = false
  }
}

const saveToNotes = () => {
  if (!aiResult.value || !sector.value) return
  try {
    vibeApi.saveNote(
      '问AI',
      `${sector.value.label} · AI 拆板块`,
      aiResult.value
    )
    ElMessage.success('已存入研究记录')
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  }
}

const goBack = () => {
  router.push('/vibe/sectors')
}

onMounted(() => {
  loadSector()
})
</script>

<style lang="scss" scoped>
.sector-detail-page {
  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 14px;
    color: var(--el-text-color-secondary);
    cursor: pointer;
    margin-bottom: 16px;
    user-select: none;

    &:hover {
      color: var(--el-color-primary);
    }
  }

  .detail-body {
    min-height: 200px;
  }

  .page-header {
    margin-bottom: 20px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 6px 0;
    }

    .page-tagline {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin: 0;
    }
  }

  .action-bar {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
  }

  .ai-output-card {
    margin-bottom: 24px;
    border-radius: 8px;

    .ai-streaming {
      color: var(--el-text-color-secondary);
      font-size: 14px;

      .dots {
        margin-left: 2px;
      }
    }

    .ai-output {
      font-size: 14px;
      line-height: 1.7;
      color: var(--el-text-color-primary);
      word-break: break-word;

      :deep(h1),
      :deep(h2),
      :deep(h3),
      :deep(h4) {
        margin: 12px 0 8px;
        font-weight: 600;
      }

      :deep(p) {
        margin: 6px 0;
      }

      :deep(ul),
      :deep(ol) {
        padding-left: 20px;
        margin: 6px 0;
      }

      :deep(code) {
        background: var(--el-fill-color-light);
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 13px;
      }

      :deep(pre) {
        background: var(--el-fill-color-light);
        padding: 10px 12px;
        border-radius: 6px;
        overflow-x: auto;
      }
    }
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 12px;
  }

  .nodes-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 24px;

    .node-pill {
      border-color: #e6a23c;
      color: #b88200;
      background-color: #fdf6ec;
      font-size: 13px;
    }

    .nodes-empty {
      font-size: 13px;
      color: var(--el-text-color-placeholder);
    }
  }

  .pending-alert {
    margin-bottom: 24px;
    border-radius: 8px;
  }

  .disclaimer {
    margin-top: 24px;
    font-size: 12px;
    color: var(--el-text-color-placeholder);
    line-height: 1.6;
  }
}
</style>
