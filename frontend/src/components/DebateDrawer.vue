<template>
  <el-drawer
    v-model="visible"
    direction="rtl"
    size="100%"
    :before-close="handleClose"
    class="debate-drawer"
  >
    <!-- 自定义头部 -->
    <template #header>
      <div class="drawer-header">
        <div class="header-left">
          <el-icon class="header-icon"><ChatLineSquare /></el-icon>
          <span class="header-title">多智能体辩论对战</span>
        </div>
        <div class="header-right">
          <el-tag type="info" effect="plain" size="default">
            <el-icon style="margin-right: 4px;"><Timer /></el-icon>
            {{ totalRounds }} 轮辩论
          </el-tag>
          <el-tag v-if="hasDecision" type="success" effect="plain" size="default">
            <el-icon style="margin-right: 4px;"><CircleCheckFilled /></el-icon>
            已裁决
          </el-tag>
        </div>
      </div>
    </template>

    <div class="debate-container">
      <!-- 三列主区域 -->
      <div class="debate-columns">

        <!-- ===== 第一列：多空辩论 ===== -->
        <div class="debate-column bull-bear-column">
          <div class="column-header">
            <div class="column-title">
              <el-icon><DataLine /></el-icon>
              <span>多空辩论</span>
            </div>
            <div class="agent-badges">
              <span class="badge bull-badge">🐂 多头</span>
              <span class="vs-text">VS</span>
              <span class="badge bear-badge">🐻 空头</span>
            </div>
          </div>

          <div class="column-content">
            <div v-if="mergedBullBearRounds.length > 0" class="round-list">
              <div
                v-for="(round, idx) in mergedBullBearRounds"
                :key="'bb-' + idx"
                class="round-card"
              >
                <div class="round-card-header">
                  <el-tag :type="getBullBearTagType(idx)" effect="dark" size="small" round>
                    第 {{ round.round }} 轮
                  </el-tag>
                </div>

                <div class="round-messages">
                  <!-- 多头 -->
                  <div v-if="round.bull" class="message-block bull-block">
                    <div class="message-block-header">
                      <span class="speaker-avatar">🐂</span>
                      <span class="speaker-name bull-text">多头研究员</span>
                    </div>
                    <div class="message-block-content">
                      {{ formatContent(round.bull.content || round.bull) }}
                    </div>
                  </div>

                  <!-- 中间箭头 -->
                  <div v-if="round.bull || round.bear" class="vs-arrow">
                    <el-icon><DArrowRight /></el-icon>
                  </div>

                  <!-- 空头 -->
                  <div v-if="round.bear" class="message-block bear-block">
                    <div class="message-block-header">
                      <span class="speaker-avatar">🐻</span>
                      <span class="speaker-name bear-text">空头研究员</span>
                    </div>
                    <div class="message-block-content">
                      {{ formatContent(round.bear.content || round.bear) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-icon class="empty-icon"><ChatDotSquare /></el-icon>
              <span>暂无多空辩论</span>
            </div>
          </div>
        </div>

        <!-- ===== 第二列：风控辩论 ===== -->
        <div class="debate-column risk-column">
          <div class="column-header">
            <div class="column-title">
              <el-icon><WarningFilled /></el-icon>
              <span>风控辩论</span>
            </div>
            <div class="agent-badges">
              <span class="badge risky-badge">⚡ 激进</span>
              <span class="badge neutral-badge">⚖️ 中性</span>
              <span class="badge safe-badge">🛡️ 保守</span>
            </div>
          </div>

          <div class="column-content">
            <div v-if="mergedRiskRounds.length > 0" class="round-list">
              <div
                v-for="(round, idx) in mergedRiskRounds"
                :key="'risk-' + idx"
                class="round-card"
              >
                <div class="round-card-header">
                  <el-tag :type="getRiskTagType(idx)" effect="dark" size="small" round>
                    第 {{ round.round }} 轮
                  </el-tag>
                </div>

                <div class="risk-messages">
                  <div v-if="round.risky" class="message-block risky-block">
                    <div class="message-block-header">
                      <span class="speaker-avatar">⚡</span>
                      <span class="speaker-name risky-text">激进分析师</span>
                    </div>
                    <div class="message-block-content">
                      {{ formatContent(round.risky.content || round.risky) }}
                    </div>
                  </div>

                  <div v-if="round.neutral" class="message-block neutral-block">
                    <div class="message-block-header">
                      <span class="speaker-avatar">⚖️</span>
                      <span class="speaker-name neutral-text">中性分析师</span>
                    </div>
                    <div class="message-block-content">
                      {{ formatContent(round.neutral.content || round.neutral) }}
                    </div>
                  </div>

                  <div v-if="round.safe" class="message-block safe-block">
                    <div class="message-block-header">
                      <span class="speaker-avatar">🛡️</span>
                      <span class="speaker-name safe-text">保守分析师</span>
                    </div>
                    <div class="message-block-content">
                      {{ formatContent(round.safe.content || round.safe) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-icon class="empty-icon"><Warning /></el-icon>
              <span>暂无风控辩论</span>
            </div>
          </div>
        </div>

        <!-- ===== 第三列：裁决区 ===== -->
        <div class="debate-column judge-column">
          <div class="column-header">
            <div class="column-title">
              <el-icon><Medal /></el-icon>
              <span>最终裁决</span>
            </div>
          </div>

          <div class="column-content">
            <!-- 研究经理裁决 -->
            <div v-if="debateData?.judge_decision" class="judge-card research-card">
              <div class="judge-card-header">
                <div class="judge-icon-bg">
                  <el-icon><User /></el-icon>
                </div>
                <div class="judge-info">
                  <div class="judge-name">研究经理裁决</div>
                  <div class="judge-desc">Research Manager</div>
                </div>
              </div>
              <div class="judge-card-body">
                {{ formatContent(debateData.judge_decision) }}
              </div>
            </div>

            <!-- 组合经理最终决策 -->
            <div v-if="debateData?.final_decision" class="judge-card final-card">
              <div class="judge-card-header">
                <div class="judge-icon-bg final">
                  <el-icon><Briefcase /></el-icon>
                </div>
                <div class="judge-info">
                  <div class="judge-name">投资组合经理决策</div>
                  <div class="judge-desc">Portfolio Manager</div>
                </div>
              </div>
              <div class="judge-card-body">
                {{ formatContent(debateData.final_decision) }}
              </div>
            </div>

            <div v-if="!debateData?.judge_decision && !debateData?.final_decision" class="empty-state">
              <el-icon class="empty-icon"><Trophy /></el-icon>
              <span>等待裁决...</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  ChatLineSquare, DataLine, WarningFilled, Warning, Medal, User, Briefcase,
  Timer, CircleCheckFilled, ChatDotSquare, DArrowRight, Trophy
} from '@element-plus/icons-vue'

export interface DebateRoundItem {
  round: number
  content: string
  timestamp?: string
}

export interface DebateData {
  bull_history?: DebateRoundItem[]
  bear_history?: DebateRoundItem[]
  risky_history?: DebateRoundItem[]
  safe_history?: DebateRoundItem[]
  neutral_history?: DebateRoundItem[]
  judge_decision?: string
  final_decision?: string
}

interface Props {
  visible: boolean
  debateData: DebateData | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'agent-click': [agent: string]
}>()

// 总轮数
const totalRounds = computed(() => {
  if (!props.debateData) return 0
  const bullRounds = props.debateData.bull_history?.length || 0
  const bearRounds = props.debateData.bear_history?.length || 0
  const riskRounds = Math.max(
    props.debateData.risky_history?.length || 0,
    props.debateData.safe_history?.length || 0,
    props.debateData.neutral_history?.length || 0
  )
  return Math.max(bullRounds, bearRounds, riskRounds)
})

const hasDecision = computed(() =>
  !!props.debateData?.judge_decision || !!props.debateData?.final_decision
)

// 合并多空辩论轮次
const mergedBullBearRounds = computed(() => {
  const rounds: Array<{
    round: number
    bull?: DebateRoundItem
    bear?: DebateRoundItem
  }> = []

  const bullRounds = props.debateData?.bull_history || []
  const bearRounds = props.debateData?.bear_history || []

  const allRounds = new Set([
    ...bullRounds.map(r => r.round),
    ...bearRounds.map(r => r.round)
  ])

  Array.from(allRounds).sort((a, b) => a - b).forEach(round => {
    rounds.push({
      round,
      bull: bullRounds.find(r => r.round === round),
      bear: bearRounds.find(r => r.round === round)
    })
  })

  return rounds
})

// 合并风控辩论轮次
const mergedRiskRounds = computed(() => {
  const rounds: Array<{
    round: number
    risky?: DebateRoundItem
    safe?: DebateRoundItem
    neutral?: DebateRoundItem
  }> = []

  const riskyRounds = props.debateData?.risky_history || []
  const safeRounds = props.debateData?.safe_history || []
  const neutralRounds = props.debateData?.neutral_history || []

  const allRounds = new Set([
    ...riskyRounds.map(r => r.round),
    ...safeRounds.map(r => r.round),
    ...neutralRounds.map(r => r.round)
  ])

  Array.from(allRounds).sort((a, b) => a - b).forEach(round => {
    rounds.push({
      round,
      risky: riskyRounds.find(r => r.round === round),
      safe: safeRounds.find(r => r.round === round),
      neutral: neutralRounds.find(r => r.round === round)
    })
  })

  return rounds
})

const getBullBearTagType = (idx: number): string => {
  const types = ['danger', 'warning', 'success', 'primary', 'info']
  return types[idx % types.length]
}

const getRiskTagType = (idx: number): string => {
  const types = ['warning', 'primary', 'info', 'success', 'danger']
  return types[idx % types.length]
}

const formatContent = (data: unknown): string => {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if ('content' in obj) return formatContent(obj.content)
    return JSON.stringify(data, null, 2)
  }
  return String(data)
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleAgentClick = (agent: string) => {
  emit('agent-click', agent)
}
</script>

<style scoped lang="scss">
// ===== 抽屉容器 =====
.debate-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 0;
  }
}

// ===== 头部 =====
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: linear-gradient(135deg, var(--el-fill-color-dark) 0%, var(--el-bg-color) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-icon {
    font-size: 26px;
    color: var(--el-color-primary);
  }

  .header-title {
    font-size: 19px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

// ===== 主容器 =====
.debate-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  background: var(--el-bg-color-page);
}

// ===== 三列布局 =====
.debate-columns {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0;
  overflow: hidden;
  min-height: 0;
}

// ===== 通用列样式 =====
.debate-column {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  border-right: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-right: none;
  }

  &.bull-bear-column {
    background: linear-gradient(180deg, rgba(245, 108, 108, 0.03) 0%, var(--el-bg-color-page) 100%);
  }

  &.risk-column {
    background: linear-gradient(180deg, rgba(230, 162, 60, 0.03) 0%, var(--el-bg-color-page) 100%);
  }

  &.judge-column {
    background: linear-gradient(180deg, rgba(64, 158, 255, 0.03) 0%, var(--el-bg-color-page) 100%);
  }
}

// ===== 列头部 =====
.column-header {
  padding: 16px 20px;
  background: var(--el-bg-color);
  border-bottom: 2px solid var(--el-border-color-lighter);
  flex-shrink: 0;

  .column-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin-bottom: 10px;

    .el-icon {
      font-size: 20px;
    }
  }

  .bull-bear-column & .column-title .el-icon { color: var(--el-color-danger); }
  .risk-column & .column-title .el-icon { color: var(--el-color-warning); }
  .judge-column & .column-title .el-icon { color: var(--el-color-primary); }
}

.agent-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.bull-badge {
  background: rgba(245, 108, 108, 0.12);
  color: var(--el-color-danger);
  border: 1px solid rgba(245, 108, 108, 0.3);
}

.bear-badge {
  background: rgba(103, 194, 58, 0.12);
  color: var(--el-color-success);
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.risky-badge {
  background: rgba(230, 162, 60, 0.12);
  color: var(--el-color-warning);
  border: 1px solid rgba(230, 162, 60, 0.3);
}

.neutral-badge {
  background: rgba(144, 147, 153, 0.12);
  color: var(--el-color-info);
  border: 1px solid rgba(144, 147, 153, 0.3);
}

.safe-badge {
  background: rgba(64, 158, 255, 0.12);
  color: var(--el-color-primary);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.vs-text {
  font-size: 11px;
  font-weight: 700;
  color: var(--el-text-color-placeholder);
  padding: 0 2px;
}

// ===== 列内容（可滚动）=====
.column-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--el-border-color);
    border-radius: 3px;

    &:hover {
      background: var(--el-color-primary-light-6);
    }
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

// ===== 轮次卡片列表 =====
.round-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.round-card {
  background: var(--el-bg-color);
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  }
}

.round-card-header {
  padding: 10px 16px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

// ===== 多空辩论消息 =====
.round-messages {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-block {
  border-radius: 8px;
  padding: 14px;
  border-left: 4px solid;

  &.bull-block {
    border-left-color: var(--el-color-danger);
    background: linear-gradient(90deg, rgba(245, 108, 108, 0.06) 0%, var(--el-bg-color) 40%);
  }

  &.bear-block {
    border-left-color: var(--el-color-success);
    background: linear-gradient(90deg, rgba(103, 194, 58, 0.06) 0%, var(--el-bg-color) 40%);
  }

  &.risky-block {
    border-left-color: var(--el-color-warning);
    background: linear-gradient(90deg, rgba(230, 162, 60, 0.06) 0%, var(--el-bg-color) 40%);
  }

  &.neutral-block {
    border-left-color: var(--el-color-info);
    background: linear-gradient(90deg, rgba(144, 147, 153, 0.06) 0%, var(--el-bg-color) 40%);
  }

  &.safe-block {
    border-left-color: var(--el-color-primary);
    background: linear-gradient(90deg, rgba(64, 158, 255, 0.06) 0%, var(--el-bg-color) 40%);
  }
}

.message-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.speaker-avatar {
  font-size: 18px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--el-fill-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.speaker-name {
  font-weight: 700;
  font-size: 13px;

  &.bull-text { color: var(--el-color-danger); }
  &.bear-text { color: var(--el-color-success); }
  &.risky-text { color: var(--el-color-warning); }
  &.neutral-text { color: var(--el-color-info); }
  &.safe-text { color: var(--el-color-primary); }
}

.message-block-content {
  font-size: 13.5px;
  line-height: 1.85;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-word;
}

// ===== VS 箭头 =====
.vs-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  font-size: 18px;
  opacity: 0.5;
  padding: 2px 0;
}

// ===== 风控辩论 =====
.risk-messages {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

// ===== 裁决卡片 =====
.judge-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
  margin-bottom: 16px;

  &.final-card {
    border-color: var(--el-color-primary-light-5);
    box-shadow: 0 4px 16px rgba(64, 158, 255, 0.1);
  }
}

.judge-card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);

  .judge-icon-bg {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: var(--el-color-primary-light-8);
    color: var(--el-color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;

    &.final {
      background: var(--el-color-primary);
      color: white;
    }
  }

  .judge-name {
    font-size: 15px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin-bottom: 3px;
  }

  .judge-desc {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

.judge-card-body {
  padding: 18px 20px;
  font-size: 14px;
  line-height: 1.9;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-word;
}

// ===== 空状态 =====
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--el-text-color-secondary);

  .empty-icon {
    font-size: 48px;
    opacity: 0.3;
  }

  span {
    font-size: 14px;
  }
}

// ===== 响应式 =====
@media (max-width: 1200px) {
  .debate-columns {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .debate-column {
    min-height: 400px;
    border-right: none;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }
  }
}
</style>
