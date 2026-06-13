<template>
  <el-drawer
    :model-value="visible"
    direction="rtl"
    size="95%"
    :before-close="handleClose"
    class="debate-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <el-icon class="header-icon"><ChatDotRound /></el-icon>
        <span class="header-title">辩论对战</span>
        <el-tag type="info" size="small" effect="plain" style="margin-left: 12px;">
          {{ debateData ? totalRounds : 0 }} 轮辩论
        </el-tag>
      </div>
    </template>

    <div class="debate-container">
      <!-- 调试信息：显示数据状态 -->
      <div v-if="debugMode" class="debug-info">
        <pre>{{ JSON.stringify(debugInfo, null, 2) }}</pre>
      </div>

      <!-- 主要辩论区域 -->
      <div class="debate-main">
        <!-- 左侧：多头 VS 空头 -->
        <div class="debate-side bull-bear">
          <div class="side-header">
            <div class="agent-card bull">
              <el-icon class="agent-icon"><CaretTop /></el-icon>
              <span class="agent-name">多头</span>
              <el-tag type="danger" size="small" effect="dark">看涨派</el-tag>
            </div>
            <div class="vs-divider">VS</div>
            <div class="agent-card bear">
              <el-icon class="agent-icon"><CaretBottom /></el-icon>
              <span class="agent-name">空头</span>
              <el-tag type="success" size="small" effect="dark">看跌派</el-tag>
            </div>
          </div>

          <div class="timeline-scroll">
            <div v-if="mergedBullBearRounds.length > 0" class="timeline">
              <div
                v-for="(round, index) in mergedBullBearRounds"
                :key="`bull-bear-${index}`"
                class="round-block"
              >
                <div class="round-label">
                  <el-tag :type="getRoundType(round.round)" size="small">
                    第 {{ round.round }} 轮
                  </el-tag>
                </div>
                <div class="messages-row">
                  <div v-if="round.bull" class="message-card bull">
                    <div class="message-header">
                      <span class="speaker bull">🐂 多头</span>
                    </div>
                    <div class="message-content">{{ round.bull.content }}</div>
                  </div>
                  <div v-else class="message-card empty">
                    <div class="message-placeholder">多头未发言</div>
                  </div>
                  <div v-if="round.bear" class="message-card bear">
                    <div class="message-header">
                      <span class="speaker bear">🐻 空头</span>
                    </div>
                    <div class="message-content">{{ round.bear.content }}</div>
                  </div>
                  <div v-else class="message-card empty">
                    <div class="message-placeholder">空头未发言</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">
              <el-empty description="暂无多空辩论记录" :image-size="60" />
            </div>
          </div>
        </div>

        <!-- 右侧：风控辩论 -->
        <div class="debate-side risk-control">
          <div class="side-header">
            <div class="section-title">
              <el-icon><Warning /></el-icon>
              <span>风控辩论</span>
            </div>
          </div>

          <div class="risk-agents">
            <div class="agent-card risky">
              <el-icon class="agent-icon"><Lightning /></el-icon>
              <span class="agent-name">激进</span>
              <el-tag type="warning" size="small" effect="dark">高风险</el-tag>
            </div>
            <div class="agent-card safe">
              <el-icon class="agent-icon"><Lock /></el-icon>
              <span class="agent-name">保守</span>
              <el-tag type="primary" size="small" effect="dark">低风险</el-tag>
            </div>
            <div class="agent-card neutral">
              <el-icon class="agent-icon"><Aim /></el-icon>
              <span class="agent-name">中性</span>
              <el-tag type="info" size="small" effect="dark">均衡</el-tag>
            </div>
          </div>

          <div class="timeline-scroll">
            <div v-if="mergedRiskRounds.length > 0" class="timeline">
              <div
                v-for="(round, index) in mergedRiskRounds"
                :key="`risk-${index}`"
                class="round-block"
              >
                <div class="round-label">
                  <el-tag :type="getRiskRoundType(round.round)" size="small">
                    第 {{ round.round }} 轮
                  </el-tag>
                </div>
                <div class="messages-stack">
                  <div v-if="round.risky" class="message-card risky">
                    <div class="message-header">
                      <span class="speaker risky">⚡ 激进分析师</span>
                    </div>
                    <div class="message-content">{{ round.risky.content }}</div>
                  </div>
                  <div v-if="round.safe" class="message-card safe">
                    <div class="message-header">
                      <span class="speaker safe">🔒 保守分析师</span>
                    </div>
                    <div class="message-content">{{ round.safe.content }}</div>
                  </div>
                  <div v-if="round.neutral" class="message-card neutral">
                    <div class="message-header">
                      <span class="speaker neutral">🎯 中性分析师</span>
                    </div>
                    <div class="message-content">{{ round.neutral.content }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">
              <el-empty description="暂无风控辩论记录" :image-size="60" />
            </div>
          </div>
        </div>
      </div>

      <!-- 裁决区域 -->
      <div class="judge-section">
        <div class="judge-header">
          <el-icon><Medal /></el-icon>
          <span>最终裁决</span>
        </div>
        <div class="judge-cards">
          <div v-if="debateData?.judge_decision" class="judge-card">
            <div class="judge-card-header">
              <el-icon><User /></el-icon>
              <span>研究总监裁决</span>
            </div>
            <div class="judge-content">{{ debateData.judge_decision }}</div>
          </div>
          <div v-if="debateData?.final_decision" class="judge-card final">
            <div class="judge-card-header">
              <el-icon><Briefcase /></el-icon>
              <span>组合经理决策</span>
            </div>
            <div class="judge-content">{{ debateData.final_decision }}</div>
          </div>
          <div v-if="!debateData?.judge_decision && !debateData?.final_decision" class="no-data-inline">
            <el-empty description="暂无裁决信息" :image-size="40" />
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChatDotRound, CaretTop, CaretBottom, Warning, Lightning, Lock, Aim, Medal, User, Briefcase } from '@element-plus/icons-vue'

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

// 调试模式
const debugMode = ref(false)

const debugInfo = computed(() => {
  if (!props.debateData) return null
  return {
    bull_count: props.debateData.bull_history?.length || 0,
    bear_count: props.debateData.bear_history?.length || 0,
    risky_count: props.debateData.risky_history?.length || 0,
    safe_count: props.debateData.safe_history?.length || 0,
    neutral_count: props.debateData.neutral_history?.length || 0,
    has_judge: !!props.debateData.judge_decision,
    has_final: !!props.debateData.final_decision
  }
})

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

// 合并多头/空头的辩论轮次
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

// 合并风控辩论的轮次
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

const getRoundType = (round: number): string => {
  const types = ['primary', 'success', 'warning', 'danger', 'info']
  return types[round % types.length]
}

const getRiskRoundType = (round: number): string => {
  const types = ['warning', 'primary', 'info', 'success']
  return types[round % types.length]
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleAgentClick = (agent: string) => {
  emit('agent-click', agent)
}
</script>

<style scoped lang="scss">
// 抽屉样式
.debate-drawer {
  :deep(.el-drawer__body) {
    padding: 0;
    overflow: hidden;
  }

  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}

.drawer-header {
  display: flex;
  align-items: center;

  .header-icon {
    font-size: 24px;
    color: var(--el-color-primary);
    margin-right: 8px;
  }

  .header-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

// 容器布局
.debate-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.debug-info {
  background: var(--el-fill-color-dark);
  color: var(--el-text-color-regular);
  padding: 12px;
  font-size: 12px;
  overflow: auto;
  max-height: 200px;
}

// 主要辩论区域
.debate-main {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
  min-height: 0;
}

// 辩论侧边栏
.debate-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  min-height: 0;

  &.bull-bear {
    border: 2px solid var(--el-border-color-lighter);
  }

  &.risk-control {
    border: 2px solid var(--el-color-warning-light-8);
  }
}

// 侧边头部
.side-header {
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.debate-side.bull-bear .side-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-color-warning);
}

// Agent 卡片
.agent-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--el-bg-color);
  border: 2px solid transparent;
  transition: all 0.3s;

  &.bull {
    border-color: var(--el-color-danger-light-7);
    .agent-icon { color: var(--el-color-danger); }
  }

  &.bear {
    border-color: var(--el-color-success-light-7);
    .agent-icon { color: var(--el-color-success); }
  }

  &.risky {
    border-color: var(--el-color-warning-light-7);
    .agent-icon { color: var(--el-color-warning); }
  }

  &.safe {
    border-color: var(--el-color-primary-light-7);
    .agent-icon { color: var(--el-color-primary); }
  }

  &.neutral {
    border-color: var(--el-color-info-light-7);
    .agent-icon { color: var(--el-color-info); }
  }

  .agent-icon {
    font-size: 28px;
  }

  .agent-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
}

.vs-divider {
  font-size: 18px;
  font-weight: 700;
  color: var(--el-text-color-secondary);
}

// 风控 Agent 行
.risk-agents {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;

  .agent-card {
    flex: 1;
    flex-direction: row;
    justify-content: center;
    padding: 10px 8px;

    .agent-name {
      font-size: 13px;
    }

    .el-tag {
      font-size: 11px;
    }
  }
}

// 时间线滚动区域
.timeline-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--el-color-primary-light-6);
    border-radius: 4px;

    &:hover {
      background: var(--el-color-primary-light-5);
    }
  }

  &::-webkit-scrollbar-track {
    background: var(--el-fill-color-light);
    border-radius: 4px;
  }
}

// 时间线
.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// 轮次块
.round-block {
  .round-label {
    margin-bottom: 8px;
  }
}

// 消息行（多空辩论用）
.messages-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

// 消息堆叠（风控辩论用）
.messages-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

// 消息卡片
.message-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 12px;
  border-left: 4px solid;

  &.bull {
    border-left-color: var(--el-color-danger);
  }

  &.bear {
    border-left-color: var(--el-color-success);
  }

  &.risky {
    border-left-color: var(--el-color-warning);
  }

  &.safe {
    border-left-color: var(--el-color-primary);
  }

  &.neutral {
    border-left-color: var(--el-color-info);
  }

  &.empty {
    border-left-color: var(--el-border-color);
    background: var(--el-fill-color-lighter);
  }

  .message-header {
    margin-bottom: 8px;
  }

  .speaker {
    font-weight: 600;
    font-size: 13px;

    &.bull { color: var(--el-color-danger); }
    &.bear { color: var(--el-color-success); }
    &.risky { color: var(--el-color-warning); }
    &.safe { color: var(--el-color-primary); }
    &.neutral { color: var(--el-color-info); }
  }

  .message-content {
    font-size: 14px;
    line-height: 1.7;
    color: var(--el-text-color-regular);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 300px;
    overflow-y: auto;
  }

  .message-placeholder {
    color: var(--el-text-color-secondary);
    font-size: 13px;
    font-style: italic;
    text-align: center;
    padding: 20px;
  }
}

// 裁决区域
.judge-section {
  flex-shrink: 0;
  padding: 20px;
  background: var(--el-bg-color);
  border-top: 2px solid var(--el-border-color-lighter);

  .judge-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-color-primary);
    margin-bottom: 16px;

    .el-icon {
      font-size: 22px;
    }
  }

  .judge-cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .judge-card {
    background: var(--el-fill-color-lighter);
    border-radius: 12px;
    padding: 16px;
    border: 2px solid var(--el-border-color-lighter);

    &.final {
      border-color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }

    .judge-card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 15px;
      color: var(--el-text-color-primary);
      margin-bottom: 12px;
    }

    .judge-content {
      font-size: 14px;
      line-height: 1.8;
      color: var(--el-text-color-regular);
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 200px;
      overflow-y: auto;
    }
  }

  .no-data-inline {
    grid-column: span 2;
    padding: 20px;
  }
}

// 无数据
.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

// 响应式调整
@media (max-width: 1024px) {
  .debate-main {
    flex-direction: column;
    overflow-y: auto;
  }

  .debate-side {
    min-height: 400px;
  }

  .messages-row {
    grid-template-columns: 1fr;
  }

  .judge-cards {
    grid-template-columns: 1fr;
  }

  .judge-card {
    .no-data-inline {
      grid-column: span 1;
    }
  }
}
</style>
