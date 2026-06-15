<template>
  <div class="single-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon class="title-icon"><Document /></el-icon>
            单股分析
          </h1>
          <p class="page-description">
            AI驱动的智能股票分析，多维度评估投资价值与风险
          </p>
        </div>
      </div>
    </div>

    <!-- 主要分析表单 -->
    <div class="analysis-container">
      <el-row :gutter="24">
        <!-- 左侧：基础配置 -->
        <el-col :span="18">
          <el-card class="main-form-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>分析配置</h3>
                <el-tag type="info" size="small">必填信息</el-tag>
              </div>
            </template>

            <el-form :model="analysisForm" label-width="100px" class="analysis-form">
              <!-- 股票信息 -->
              <div class="form-section">
                <h4 class="section-title">📊 股票信息</h4>
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="股票代码" required>
                      <el-input
                        v-model="analysisForm.stockCode"
                        placeholder="如：000001、AAPL、700、1810"
                        clearable
                        size="large"
                        class="stock-input"
                        :class="{ 'is-error': stockCodeError }"
                        @blur="validateStockCodeInput"
                        @input="onStockCodeInput"
                      >
                        <template #prefix>
                          <el-icon><TrendCharts /></el-icon>
                        </template>
                      </el-input>
                      <div v-if="stockCodeError" class="error-message">
                        <el-icon><WarningFilled /></el-icon>
                        {{ stockCodeError }}
                      </div>
                      <div v-else-if="stockCodeHelp" class="help-message">
                        <el-icon><InfoFilled /></el-icon>
                        {{ stockCodeHelp }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="市场类型">
                      <el-select
                        v-model="analysisForm.market"
                        placeholder="选择市场"
                        size="large"
                        style="width: 100%"
                        @change="onMarketChange"
                      >
                        <el-option label="🇨🇳 A股市场" value="A股">
                          <span>🇨🇳 A股市场</span>
                          <span style="color: #909399; font-size: 12px; margin-left: 8px;">（6位数字）</span>
                        </el-option>
                        <el-option label="🇺🇸 美股市场" value="美股">
                          <span>🇺🇸 美股市场</span>
                          <span style="color: #909399; font-size: 12px; margin-left: 8px;">（1-5个字母）</span>
                        </el-option>
                        <el-option label="🇭🇰 港股市场" value="港股">
                          <span>🇭🇰 港股市场</span>
                          <span style="color: #909399; font-size: 12px; margin-left: 8px;">（1-5位数字）</span>
                        </el-option>
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="分析日期">
                  <el-date-picker
                    v-model="analysisForm.analysisDate"
                    type="date"
                    placeholder="选择分析基准日期"
                    size="large"
                    style="width: 100%"
                    :disabled-date="disabledDate"
                  />
                </el-form-item>
              </div>

              <!-- 分析深度 -->
              <div class="form-section">
                <h4 class="section-title">🎯 分析深度</h4>
                <div class="depth-selector">
                  <div
                    v-for="(depth, index) in depthOptions"
                    :key="index"
                    class="depth-option"
                    :class="{ active: analysisForm.researchDepth === index + 1 }"
                    @click="analysisForm.researchDepth = index + 1"
                  >
                    <div class="depth-icon">{{ depth.icon }}</div>
                    <div class="depth-info">
                      <div class="depth-name">{{ depth.name }}</div>
                      <div class="depth-desc">{{ depth.description }}</div>
                      <div class="depth-time">{{ depth.time }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分析师团队 -->
              <div class="form-section">
                <h4 class="section-title">👥 分析师团队</h4>
                <div class="analysts-grid">
                  <div
                    v-for="analyst in ANALYSTS"
                    :key="analyst.id"
                    class="analyst-card"
                    :class="{ 
                      active: analysisForm.selectedAnalysts.includes(analyst.name)
                    }"
                    @click="toggleAnalyst(analyst.name)"
                  >
                    <div class="analyst-avatar">
                      <el-icon>
                        <component :is="analyst.icon" />
                      </el-icon>
                    </div>
                    <div class="analyst-content">
                      <div class="analyst-name">{{ analyst.name }}</div>
                      <div class="analyst-desc">{{ analyst.description }}</div>
                    </div>
                    <div class="analyst-check">
                      <el-icon v-if="analysisForm.selectedAnalysts.includes(analyst.name)" class="check-icon">
                        <Check />
                      </el-icon>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="form-section">
                <div class="action-buttons" style="display: flex; justify-content: center; align-items: center; width: 100%; text-align: center;">
                  <el-button
                    v-if="analysisStatus === 'idle'"
                    type="primary"
                    size="large"
                    @click="submitAnalysis"
                    :loading="submitting"
                    :disabled="!analysisForm.stockCode.trim()"
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><TrendCharts /></el-icon>
                    开始智能分析
                  </el-button>

                  <el-button
                    v-else-if="analysisStatus === 'running'"
                    type="warning"
                    size="large"
                    disabled
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><Loading /></el-icon>
                    分析进行中...
                  </el-button>

                  <div v-else-if="analysisStatus === 'completed'" style="display: flex; gap: 12px;">
                    <el-button
                      type="success"
                      size="large"
                      @click="showResults = !showResults"
                      class="submit-btn"
                      style="width: 180px; height: 56px; font-size: 16px; font-weight: 700; border-radius: 16px;"
                    >
                      <el-icon><Document /></el-icon>
                      {{ showResults ? '隐藏结果' : '查看结果' }}
                    </el-button>

                    <el-button
                      type="primary"
                      size="large"
                      @click="restartAnalysis"
                      class="submit-btn"
                      style="width: 180px; height: 56px; font-size: 16px; font-weight: 700; border-radius: 16px;"
                    >
                      <el-icon><Refresh /></el-icon>
                      重新分析
                    </el-button>
                  </div>

                  <el-button
                    v-else-if="analysisStatus === 'failed'"
                    type="danger"
                    size="large"
                    @click="restartAnalysis"
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><Refresh /></el-icon>
                    重新分析
                  </el-button>
                </div>
              </div>

              <!-- 分析进度显示 -->
              <div v-if="analysisStatus === 'running'" class="progress-section">
                <el-card class="progress-card" shadow="hover">
                  <template #header>
                    <div class="progress-header">
                      <h4>
                        <el-icon class="rotating-icon">
                          <Loading />
                        </el-icon>
                        分析进行中...
                      </h4>
                      <!-- 任务ID已隐藏 -->
                      <!-- <el-tag type="warning">{{ currentTaskId }}</el-tag> -->
                    </div>
                  </template>

                  <div class="progress-content">
                    <!-- 总体进度信息 -->
                    <div class="overall-progress-info">
                      <div class="progress-stats">
                        <!-- 当前步骤已隐藏 -->
                        <!--
                        <div class="stat-item">
                          <div class="stat-label">当前步骤</div>
                          <div class="stat-value">{{ progressInfo.currentStep || '初始化中...' }}</div>
                        </div>
                        -->
                        <!-- 整体进度已隐藏 -->
                        <!--
                        <div class="stat-item">
                          <div class="stat-label">整体进度</div>
                          <div class="stat-value">{{ progressInfo.progress.toFixed(1) }}%</div>
                        </div>
                        -->
                        <div class="stat-item">
                          <div class="stat-label">已用时间</div>
                          <div class="stat-value">{{ formatTime(progressInfo.elapsedTime) }}</div>
                        </div>
                        <div class="stat-item">
                          <div class="stat-label">预计剩余</div>
                          <div class="stat-value">{{ formatTime(progressInfo.remainingTime) }}</div>
                        </div>
                        <div class="stat-item">
                          <div class="stat-label">预计总时长</div>
                          <div class="stat-value">{{ formatTime(progressInfo.totalTime) }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- 进度条 -->
                    <div class="progress-bar-section">
                      <el-progress
                        :percentage="Math.round(progressInfo.progress)"
                        :stroke-width="12"
                        :show-text="true"
                        :status="getProgressStatus()"
                        class="main-progress-bar"
                      />
                    </div>

                    <!-- 当前任务详情 -->
                    <div class="current-task-info">
                      <div class="task-title">
                        <el-icon class="task-icon">
                          <Loading />
                        </el-icon>
                        {{ progressInfo.currentStep || '正在初始化分析引擎...' }}
                      </div>
                      <div
                        class="task-description"
                        style="white-space: pre-wrap; line-height: 1.6;"
                      >
                        {{ progressInfo.currentStepDescription || progressInfo.message || 'AI正在根据您的要求重点分析相关内容' }}
                      </div>
                    </div>

                    <!-- 分析步骤显示 - 已隐藏 -->
                    <!--
                    <div v-if="analysisSteps.length > 0" class="analysis-steps">
                      <h5 class="steps-title">📋 分析步骤</h5>
                      <div class="steps-container">
                        <div
                          v-for="(step, index) in analysisSteps"
                          :key="index"
                          class="step-item"
                          :class="{
                            'step-completed': step.status === 'completed',
                            'step-current': step.status === 'current',
                            'step-pending': step.status === 'pending'
                          }"
                        >
                          <div class="step-icon">
                            <el-icon v-if="step.status === 'completed'" class="completed-icon">
                              <Check />
                            </el-icon>
                            <el-icon v-else-if="step.status === 'current'" class="current-icon rotating-icon">
                              <Loading />
                            </el-icon>
                            <el-icon v-else class="pending-icon">
                              <Clock />
                            </el-icon>
                          </div>
                          <div class="step-content">
                            <div class="step-title">{{ step.title }}</div>
                            <div class="step-description">{{ step.description }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                    -->
                  </div>
                </el-card>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：高级配置 -->
        <el-col :span="6">
          <el-card class="config-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>高级配置</h3>
                <el-tag type="warning" size="small">可选设置</el-tag>
              </div>
            </template>

            <div class="config-content">
              <!-- AI模型配置 -->
              <div class="config-section">
                <h4 class="config-title">🤖 AI模型配置</h4>
                <div class="model-config">
                  <div class="model-item">
                    <div class="model-label">
                      <span>快速分析模型</span>
                      <el-tooltip content="用于市场分析、新闻分析、基本面分析等" placement="top">
                        <el-icon class="help-icon"><InfoFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-select v-model="modelSettings.quickAnalysisModel" size="small" style="width: 100%" filterable>
                      <el-option
                        v-for="model in availableModels"
                        :key="`quick-${model.provider}/${model.model_name}`"
                        :label="model.model_display_name || model.model_name"
                        :value="model.model_name"
                      >
                        <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                          <span style="flex: 1;">{{ model.model_display_name || model.model_name }}</span>
                          <div style="display: flex; align-items: center; gap: 4px;">
                            <!-- 能力等级徽章 -->
                            <el-tag
                              v-if="model.capability_level"
                              :type="getCapabilityTagType(model.capability_level)"
                              size="small"
                              effect="plain"
                            >
                              {{ getCapabilityText(model.capability_level) }}
                            </el-tag>
                            <!-- 角色标签 -->
                            <el-tag
                              v-if="isQuickAnalysisRole(model.suitable_roles)"
                              type="success"
                              size="small"
                              effect="plain"
                            >
                              ⚡快速
                            </el-tag>
                            <span style="font-size: 12px; color: #909399;">{{ model.provider }}</span>
                          </div>
                        </div>
                      </el-option>
                    </el-select>
                  </div>

                  <div class="model-item">
                    <div class="model-label">
                      <span>深度决策模型</span>
                      <el-tooltip content="用于研究管理者综合决策、风险管理者最终评估" placement="top">
                        <el-icon class="help-icon"><InfoFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    <DeepModelSelector v-model="modelSettings.deepAnalysisModel" :available-models="availableModels" type="deep" size="small" width="100%" />
                  </div>
                </div>

                <!-- 🆕 模型推荐提示 -->
                <el-alert
                  v-if="modelRecommendation"
                  :title="modelRecommendation.title"
                  :type="modelRecommendation.type"
                  :closable="false"
                  style="margin-top: 12px;"
                >
                  <template #default>
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
                      <div style="font-size: 13px; line-height: 1.8; flex: 1; white-space: pre-line;">
                        {{ modelRecommendation.message }}
                      </div>
                      <el-button
                        v-if="modelRecommendation.quickModel && modelRecommendation.deepModel"
                        type="primary"
                        size="small"
                        @click="applyRecommendedModels"
                        style="flex-shrink: 0;"
                      >
                        应用推荐
                      </el-button>
                    </div>
                  </template>
                </el-alert>
              </div>

              <!-- 分析选项 -->
              <div class="config-section">
                <h4 class="config-title">⚙️ 分析选项</h4>
                <div class="option-list">
                  <div class="option-item">
                    <div class="option-info">
                      <span class="option-name">情绪分析</span>
                      <span class="option-desc">分析市场情绪和投资者心理</span>
                    </div>
                    <el-switch v-model="analysisForm.includeSentiment" />
                  </div>

                  <div class="option-item">
                    <div class="option-info">
                      <span class="option-name">风险评估</span>
                      <span class="option-desc">包含详细的风险因素分析</span>
                    </div>
                    <el-switch v-model="analysisForm.includeRisk" />
                  </div>

                  <div class="option-item">
                    <div class="option-info">
                      <span class="option-name">语言偏好</span>
                    </div>
                    <el-select v-model="analysisForm.language" size="small" style="width: 100px">
                      <el-option label="中文" value="zh-CN" />
                      <el-option label="English" value="en-US" />
                    </el-select>
                  </div>
                </div>
              </div>

            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 分析结果显示 -->
      <div v-if="showResults && analysisResults" class="results-section">
        <el-row :gutter="24">
          <el-col :span="24">
            <el-card class="results-card" shadow="hover">
              <template #header>
                <div class="results-header">
                  <h3>📊 分析结果</h3>
                  <div class="result-meta">
                    <el-tag type="success">{{ analysisResults.symbol || analysisResults.stock_symbol || analysisForm.symbol || analysisForm.stockCode }}</el-tag>
                    <el-tag>{{ analysisResults.analysis_date }}</el-tag>
                    <el-tag v-if="analysisResults.model_info && analysisResults.model_info !== 'Unknown'" type="info">
                      <el-icon><Cpu /></el-icon>
                      {{ analysisResults.model_info }}
                    </el-tag>
                  </div>
                </div>
              </template>

              <div class="results-content">
                <!-- 最终决策：策略点位 + 核心洞察（8 字段中文格式） -->
                <div v-if="analysisResults.decision" class="decision-section">
                  <h4>🎯 决策摘要</h4>
                  <div class="decision-card">
                    <div class="decision-main">
                      <div class="decision-action">
                        <span class="label">操作建议:</span>
                        <el-tag
                          :type="getActionTagType(analysisResults.decision.评级 || analysisResults.decision.action || analysisResults.decision.操作建议)"
                          size="large"
                        >
                          {{ analysisResults.decision.评级 || analysisResults.decision.action || analysisResults.decision.操作建议 }}
                        </el-tag>
                        <el-tag type="info" size="small" style="margin-left: 8px;">仅供参考</el-tag>
                      </div>

                      <div class="decision-metrics">
                        <div class="metric-item">
                          <span class="label">理想买入</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['理想买入', 'ideal_buy', 'target_price']) }}</span>
                        </div>
                        <div class="metric-item">
                          <span class="label">二次买入</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['二次买入', 'second_buy']) }}</span>
                        </div>
                        <div class="metric-item">
                          <span class="label">止损价格</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['止损价格', 'stop_loss']) }}</span>
                        </div>
                        <div class="metric-item">
                          <span class="label">止盈目标</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['止盈目标', 'target_price', 'price_target']) }}</span>
                        </div>
                        <div class="metric-item">
                          <span class="label">支撑位</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['支撑位', 'support_level']) }}</span>
                        </div>
                        <div class="metric-item">
                          <span class="label">阻力位</span>
                          <span class="value">¥{{ formatFieldValue(analysisResults.decision, ['阻力位', 'resistance_level']) }}</span>
                        </div>
                      </div>

                      <div class="decision-insights">
                        <!-- 6 张卡片：核心洞察、投资逻辑、情绪分析、趋势预测、策略点位、风险提示 -->
                        <div v-if="getRefinedField(analysisResults, '核心洞察')" class="insight-card insight-core">
                          <div class="insight-card-header">
                            <span class="insight-icon">💡</span>
                            <span class="insight-title">核心洞察</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '核心洞察') }}</div>
                        </div>

                        <div v-if="getRefinedField(analysisResults, '投资逻辑')" class="insight-card insight-investment">
                          <div class="insight-card-header">
                            <span class="insight-icon">📊</span>
                            <span class="insight-title">投资逻辑</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '投资逻辑') }}</div>
                        </div>

                        <div v-if="getSentimentContent(analysisResults)" class="insight-card insight-sentiment">
                          <div class="insight-card-header">
                            <span class="insight-icon">🔥</span>
                            <span class="insight-title">情绪分析</span>
                          </div>
                          <div class="insight-card-body">{{ getSentimentContent(analysisResults) }}</div>
                        </div>

                        <div v-if="getRefinedField(analysisResults, '趋势预测')" class="insight-card insight-trend">
                          <div class="insight-card-header">
                            <span class="insight-icon">📈</span>
                            <span class="insight-title">趋势预测</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '趋势预测') }}</div>
                        </div>

                        <div v-if="getRefinedField(analysisResults, '策略点位')" class="insight-card insight-strategy">
                          <div class="insight-card-header">
                            <span class="insight-icon">🎯</span>
                            <span class="insight-title">策略点位</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '策略点位') }}</div>
                        </div>

                        <div v-if="getRefinedField(analysisResults, '风险提示')" class="insight-card insight-risk">
                          <div class="insight-card-header">
                            <span class="insight-icon">⚠️</span>
                            <span class="insight-title">风险提示</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '风险提示') }}</div>
                        </div>

                        <div v-if="getRefinedField(analysisResults, '持仓周期')" class="insight-card insight-holding">
                          <div class="insight-card-header">
                            <span class="insight-icon">📅</span>
                            <span class="insight-title">持仓周期</span>
                          </div>
                          <div class="insight-card-body">{{ getRefinedField(analysisResults, '持仓周期') }}</div>
                        </div>
                      </div>

                      <div class="decision-confidence">
                        <div class="confidence-item">
                          <span class="label">置信度</span>
                          <span class="value">{{ formatPctField(analysisResults.decision, ['置信度', 'confidence', 'confidence_score']) }}%</span>
                        </div>
                        <div v-if="formatFieldValue(analysisResults.decision, ['风险等级', 'risk_level']) !== '--'" class="confidence-item">
                          <span class="label">风险等级</span>
                          <span class="value">{{ formatFieldValue(analysisResults.decision, ['风险等级', 'risk_level']) }}</span>
                        </div>
                        <div v-if="formatFieldValue(analysisResults.decision, ['技术面评分']) !== '--'" class="confidence-item">
                          <span class="label">技术面</span>
                          <span class="value">{{ formatPctField(analysisResults.decision, ['技术面评分']) }}%</span>
                        </div>
                        <div v-if="formatFieldValue(analysisResults.decision, ['基本面评分']) !== '--'" class="confidence-item">
                          <span class="label">基本面</span>
                          <span class="value">{{ formatPctField(analysisResults.decision, ['基本面评分']) }}%</span>
                        </div>
                        <div v-if="formatFieldValue(analysisResults.decision, ['情绪面评分']) !== '--'" class="confidence-item">
                          <span class="label">情绪面</span>
                          <span class="value">{{ formatPctField(analysisResults.decision, ['情绪面评分']) }}%</span>
                        </div>
                        <div v-if="formatFieldValue(analysisResults.decision, ['政策面评分']) !== '--'" class="confidence-item">
                          <span class="label">政策面</span>
                          <span class="value">{{ formatPctField(analysisResults.decision, ['政策面评分']) }}%</span>
                        </div>
                      </div>
                    </div>

                    <div class="decision-reasoning">
                      <h5>分析依据:</h5>
                      <p>{{ analysisResults.decision.reasoning || '详见下方详细分析报告' }}</p>
                      <el-alert type="info" :closable="false" style="margin-top: 12px;">
                        <template #default>
                          <span style="font-size: 13px;">💡 以上分析基于AI模型对公开市场数据的解读，不构成投资建议，请结合自身风险承受能力独立决策。</span>
                        </template>
                      </el-alert>
                    </div>
                  </div>
                </div>

                <!-- 分析概览（从 analysisResults 顶层字段提取，若存在则展示） -->
                <div v-if="analysisResults && (analysisResults.summary || analysisResults.recommendation)" class="overview-section">
                  <h4>📊 分析要点</h4>
                  <div class="overview-card">
                    <div v-if="analysisResults.summary" class="overview-summary">
                      <h5>分析摘要:</h5>
                      <p>{{ analysisResults.summary }}</p>
                    </div>
                    <div v-if="analysisResults.recommendation" class="overview-recommendation">
                      <h5>投资建议:</h5>
                      <p>{{ analysisResults.recommendation }}</p>
                    </div>
                  </div>
                </div>

                <!-- 详细分析报告 -->
                <div v-if="analysisResults.state || analysisResults.reports" class="reports-section">
                  <h4>📋 详细分析报告</h4>

                  <!-- 美观的标签页展示 -->
                  <div class="analysis-tabs-container">
                    <el-tabs
                      v-model="activeReportTab"
                      type="card"
                      class="analysis-tabs"
                      tab-position="top"
                      :key="analysisResults?.id || 'default'"
                    >
                      <el-tab-pane
                        v-for="(report, key) in getAnalysisReports(analysisResults)"
                        :key="key"
                        :name="key.toString()"
                        :label="report.title"
                        class="report-tab-pane"
                      >
                        <!-- 标签页内容头部 -->
                        <div class="report-header">
                          <div class="report-title">
                            <span class="report-icon">{{ getReportIcon(report.title) }}</span>
                            <span class="report-name">{{ getReportName(report.title) }}</span>
                          </div>
                          <div class="report-description">{{ getReportDescription(report.title) }}</div>
                        </div>

                        <!-- 报告内容 -->
                        <div class="report-content-wrapper">
                          <div
                            class="report-content"
                            v-html="formatReportContent(report.content)"
                            v-if="report.content"
                          ></div>
                          <div v-else class="no-content">
                            <el-empty description="暂无内容" />
                          </div>
                        </div>
                      </el-tab-pane>
                    </el-tabs>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="result-actions">
                  <el-button type="success" @click="goSimOrder">
                    <el-icon><CreditCard /></el-icon>
                    一键模拟下单
                  </el-button>
                  <el-button type="warning" @click="openDebateDrawer">
                    <el-icon><ChatDotRound /></el-icon>
                    查看辩论详情
                  </el-button>
                  <el-dropdown trigger="click" @command="downloadReport">
                    <el-button type="primary">
                      <el-icon><Download /></el-icon>
                      下载报告
                      <el-icon class="el-icon--right"><arrow-down /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="markdown">
                          <el-icon><document /></el-icon> Markdown
                        </el-dropdown-item>
                        <el-dropdown-item command="docx">
                          <el-icon><document /></el-icon> Word 文档
                        </el-dropdown-item>
                        <el-dropdown-item command="pdf">
                          <el-icon><document /></el-icon> PDF
                        </el-dropdown-item>
                        <el-dropdown-item command="json" divided>
                          <el-icon><document /></el-icon> JSON (原始数据)
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>

                <!-- 风险提示 -->
                <el-alert
                  type="warning"
                  :closable="false"
                  show-icon
                  class="risk-disclaimer"
                >
                  <template #title>
                    <span style="font-weight: bold;">报告依据真实交易数据使用AI分析生成，仅供参考，不构成任何投资建议。市场有风险，投资需谨慎。</span>
                  </template>
                </el-alert>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
    <!-- 辩论抽屉组件 -->
    <DebateDrawer v-model:visible="debateDrawerVisible" :debate-data="debateData" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, onActivated, onDeactivated, computed, h } from 'vue'

// 组件名称：用于 keep-alive 的 include 匹配
defineOptions({ name: 'SingleAnalysis' })
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, ElInputNumber } from 'element-plus'
import {
  Document,
  TrendCharts,
  InfoFilled,
  Check,
  Loading,
  Refresh,
  Download,
  CreditCard,
  WarningFilled,
  Cpu,
  QuestionFilled,
  ArrowDown,
  ChatDotRound,
} from '@element-plus/icons-vue'
import { analysisApi, type SingleAnalysisRequest } from '@/api/analysis'
import { paperApi } from '@/api/paper'
import { stocksApi } from '@/api/stocks'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { configApi } from '@/api/config'
import DeepModelSelector from '@/components/DeepModelSelector.vue'
import DebateDrawer from '@/components/DebateDrawer.vue'
import { ANALYSTS, convertAnalystNamesToIds } from '@/constants/analysts'
import { marked } from 'marked'
import { recommendModels } from '@/api/modelCapabilities'
import { validateStockCode, getStockCodeFormatHelp } from '@/utils/stockValidator'
import { normalizeMarketForAnalysis, getMarketByStockCode } from '@/utils/market'

// 配置marked选项
marked.setOptions({
  breaks: true,        // 支持换行符转换为<br>
  gfm: true           // 启用GitHub风格的Markdown
})

// 市场类型定义
type MarketType = 'A股' | '美股' | '港股'

// 表单类型定义
interface AnalysisForm {
  stockCode: string
  symbol: string
  market: MarketType
  analysisDate: Date
  researchDepth: number
  selectedAnalysts: string[]
  includeSentiment: boolean
  includeRisk: boolean
  language: 'zh-CN' | 'en-US'
}

// 使用store
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const submitting = ref(false)

// 分析进度和结果相关状态
const currentTaskId = ref('')
const analysisStatus = ref('idle') // 'idle', 'running', 'completed', 'failed'
const showResults = ref(false)
const analysisResults = ref<any>(null)
const activeReportTab = ref('') // 当前激活的报告标签页
const debateDrawerVisible = ref(false)
const debateData = ref<any>(null)
const progressInfo = ref({
  progress: 0,
  currentStep: '',
  currentStepDescription: '',  // 当前步骤描述
  message: '',
  elapsedTime: 0,      // 已用时间（秒）
  remainingTime: 0,    // 预计剩余时间（秒）
  totalTime: 0         // 预计总时长（秒）
})
const pollingTimer = ref<any>(null)

// 分析步骤定义（动态生成）
const analysisSteps = ref<any[]>([])

// 从后端步骤数据生成前端步骤
const generateStepsFromBackend = (backendSteps: any[]) => {
  if (!backendSteps || !Array.isArray(backendSteps)) {
    return []
  }

  return backendSteps.map((step: any, index: number) => ({
    key: `step_${index}`,
    title: step.name || `步骤 ${index + 1}`,
    description: step.description || '处理中...',
    status: 'pending'
  }))
}

// 模型设置
const modelSettings = ref({
  quickAnalysisModel: 'qwen-turbo',
  deepAnalysisModel: 'qwen-max'
})

// 可用的模型列表（从配置中获取）
const availableModels = ref<any[]>([])

// 🆕 模型推荐提示
const modelRecommendation = ref<{
  title: string
  message: string
  type: 'success' | 'warning' | 'info' | 'error'
  quickModel?: string
  deepModel?: string
} | null>(null)

// 分析表单
const analysisForm = reactive<AnalysisForm>({
  stockCode: '',  // 保留用于表单绑定
  symbol: '',     // 标准化后的代码
  market: 'A股',
  analysisDate: new Date(),
  researchDepth: 3, // 默认选中3级标准分析（推荐），将在 onMounted 中从用户偏好加载
  selectedAnalysts: ['市场分析师', '基本面分析师'], // 将在 onMounted 中从用户偏好加载
  includeSentiment: true,
  includeRisk: true,
  language: 'zh-CN'
})

// 股票代码验证相关
const stockCodeError = ref<string>('')
const stockCodeHelp = ref<string>('')

// 深度选项（5个级别，基于实际测试数据更新）
const depthOptions = [
  { icon: '⚡', name: '1级 - 快速分析', description: '基础数据概览，快速决策', time: '2-5分钟' },
  { icon: '📈', name: '2级 - 基础分析', description: '常规投资决策', time: '3-6分钟' },
  { icon: '🎯', name: '3级 - 标准分析', description: '技术+基本面，推荐', time: '4-8分钟' },
  { icon: '🔍', name: '4级 - 深度分析', description: '多轮辩论，深度研究', time: '6-11分钟' },
  { icon: '🏆', name: '5级 - 全面分析', description: '最全面的分析报告', time: '8-16分钟' }
]

// 禁用日期
const disabledDate = (time: Date) => {
  return time.getTime() > Date.now()
}

// 股票代码输入时的处理
const onStockCodeInput = () => {
  // 清除错误信息
  stockCodeError.value = ''
  // 显示格式提示
  stockCodeHelp.value = getStockCodeFormatHelp(analysisForm.market)
}

// 市场类型变更时的处理
const onMarketChange = () => {
  // 重新验证股票代码
  if (analysisForm.stockCode.trim()) {
    validateStockCodeInput()
  } else {
    // 显示新市场的格式提示
    stockCodeHelp.value = getStockCodeFormatHelp(analysisForm.market)
  }
}

// 验证股票代码输入
const validateStockCodeInput = () => {
  const code = analysisForm.stockCode.trim()

  if (!code) {
    stockCodeError.value = ''
    stockCodeHelp.value = ''
    return
  }

  // 验证股票代码格式
  const validation = validateStockCode(code, analysisForm.market)

  if (!validation.valid) {
    stockCodeError.value = validation.message || '股票代码格式不正确'
    stockCodeHelp.value = ''
  } else {
    stockCodeError.value = ''
    stockCodeHelp.value = `✓ ${validation.market}代码格式正确`

    // 自动更新市场类型（如果识别出的市场与当前选择不同）
    if (validation.market && validation.market !== analysisForm.market) {
      analysisForm.market = validation.market
      ElMessage.success(`已自动识别为${validation.market}`)
    }

    // 标准化代码
    if (validation.normalizedCode) {
      analysisForm.stockCode = validation.normalizedCode
    }
  }

  // 获取股票信息
  fetchStockInfo()
}

// 获取股票信息
const fetchStockInfo = () => {
  // TODO: 实现股票信息获取
}

// 切换分析师
const toggleAnalyst = (analystName: string) => {
  const index = analysisForm.selectedAnalysts.indexOf(analystName)
  if (index > -1) {
    analysisForm.selectedAnalysts.splice(index, 1)
  } else {
    analysisForm.selectedAnalysts.push(analystName)
  }
}

// 提交分析
const submitAnalysis = async () => {
  const stockCode = analysisForm.stockCode.trim()
  if (!stockCode) {
    ElMessage.warning('请输入股票代码')
    return
  }

  // 验证股票代码格式
  const validation = validateStockCode(stockCode, analysisForm.market)
  if (!validation.valid) {
    ElMessage.error(validation.message || '股票代码格式不正确')
    stockCodeError.value = validation.message || '股票代码格式不正确'
    return
  }

  // 使用标准化后的代码
  analysisForm.symbol = validation.normalizedCode || stockCode.toUpperCase()

  if (analysisForm.selectedAnalysts.length === 0) {
    ElMessage.warning('请至少选择一个分析师')
    return
  }

  submitting.value = true

  try {
    // 确保 analysisDate 是 Date 对象
    const analysisDate = analysisForm.analysisDate instanceof Date
      ? analysisForm.analysisDate
      : new Date(analysisForm.analysisDate)

    const request: SingleAnalysisRequest = {
      symbol: analysisForm.symbol,
      stock_code: analysisForm.symbol,  // 兼容字段
      parameters: {
        market_type: analysisForm.market,
        analysis_date: analysisDate.toISOString().split('T')[0],
        research_depth: getDepthDescription(analysisForm.researchDepth),
        selected_analysts: convertAnalystNamesToIds(analysisForm.selectedAnalysts),
        include_sentiment: analysisForm.includeSentiment,
        include_risk: analysisForm.includeRisk,
        language: analysisForm.language,
        quick_analysis_model: modelSettings.value.quickAnalysisModel,
        deep_analysis_model: modelSettings.value.deepAnalysisModel
      }
    }

    const response = await analysisApi.startSingleAnalysis(request)

    console.log('🔍 分析响应数据:', response)
    console.log('🔍 响应数据结构:', response.data)
    console.log('🔍 任务ID:', response.data?.task_id)

    ElMessage.success('分析任务已提交，正在处理中...')

    // 响应拦截器已返回 response.data，所以直接访问 response.data.task_id
    currentTaskId.value = response.data.task_id

    if (!currentTaskId.value) {
      console.error('❌ 任务ID为空:', response)
      ElMessage.error('任务ID获取失败，请重试')
      return
    }

    console.log('✅ 任务ID设置成功:', currentTaskId.value)

    // 保存任务状态到缓存
    saveTaskToCache(currentTaskId.value, {
      parameters: { ...analysisForm },
      submitTime: new Date().toISOString()
    })

    analysisStatus.value = 'running'
    showResults.value = false
    progressInfo.value = {
      progress: 0,
      currentStep: '正在初始化分析...',
      currentStepDescription: '分析任务已提交，正在启动分析流程',
      message: '分析任务已提交，正在启动分析流程',
      elapsedTime: 0,
      remainingTime: 0,
      totalTime: 0
    }

    // 初始化空的步骤列表，等待后端数据
    analysisSteps.value = []

    // 开始轮询任务状态
    startPollingTaskStatus()

    // 立即查询一次状态（不等待第一次轮询）
    setTimeout(async () => {
      try {
        const response = await analysisApi.getTaskStatus(currentTaskId.value)
        const status = response.data // 响应拦截器已返回 response.data
        console.log('🔄 立即查询状态:', status)
        console.log('🔄 当前 analysisStatus:', analysisStatus.value)
        if (status.status === 'running') {
          analysisStatus.value = 'running'
          console.log('✅ 设置 analysisStatus 为 running')
          updateProgressInfo(status)
        }
      } catch (error) {
        console.error('立即查询状态失败:', error)
      }
    }, 1000) // 1秒后查询

  } catch (error: any) {
    ElMessage.error(error.message || '提交分析失败')
  } finally {
    submitting.value = false
  }
}

// 轮询任务状态
const startPollingTaskStatus = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }

  // 检查任务ID是否有效
  if (!currentTaskId.value) {
    console.error('❌ 任务ID为空，无法开始轮询')
    return
  }

  console.log('🔄 开始轮询任务状态:', currentTaskId.value)

  pollingTimer.value = setInterval(async () => {
    try {
      if (!currentTaskId.value) {
        console.error('❌ 轮询中任务ID为空')
        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
        }
        return
      }

      console.log('🔄 开始查询任务状态:', currentTaskId.value)
      const response = await analysisApi.getTaskStatus(currentTaskId.value)
      const status = response.data // 响应拦截器已返回 response.data

      console.log('🔍 任务状态响应:', response)
      console.log('🔍 任务状态数据:', status)
      console.log('🔍 当前状态:', status.status, '进度:', status.progress)

      if (status.status === 'completed') {
        // 分析完成，调用专门的结果API获取完整数据
        console.log('🎉 分析完成，正在获取完整结果...')

        try {
          const resultResponse = await fetch(`/api/analysis/tasks/${currentTaskId.value}/result`, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          })

          if (resultResponse.ok) {
            const resultData = await resultResponse.json()
            if (resultData.success) {
              analysisResults.value = resultData.data
              console.log('✅ 获取完整分析结果成功:', resultData.data)

              // 添加调试信息
              console.log('🔍 完整结果数据结构:', {
                hasDecision: !!resultData.data?.decision,
                hasState: !!resultData.data?.state,
                hasReports: !!resultData.data?.reports,
                hasSummary: !!resultData.data?.summary,
                hasRecommendation: !!resultData.data?.recommendation,
                keys: Object.keys(resultData.data || {})
              })
            } else {
              console.error('❌ 获取分析结果失败:', resultData.message)
              analysisResults.value = status.result_data // 回退到状态中的数据
            }
          } else {
            console.error('❌ 结果API调用失败:', resultResponse.status)
            analysisResults.value = status.result_data // 回退到状态中的数据
          }
        } catch (error) {
          console.error('❌ 获取分析结果异常:', error)
          analysisResults.value = status.result_data // 回退到状态中的数据
        }

        analysisStatus.value = 'completed'
        showResults.value = true
        progressInfo.value.progress = 100
        progressInfo.value.currentStep = '分析完成'
        progressInfo.value.message = '分析已完成！'

        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
          pollingTimer.value = null
        }

        // 任务完成后保持缓存，以便刷新后能看到结果
        // clearTaskCache() // 不清除，让用户能在30分钟内刷新查看结果

        ElMessage.success('分析完成！')

      } else if (status.status === 'failed') {
        // 分析失败
        analysisStatus.value = 'failed'
        progressInfo.value.currentStep = '分析失败'

        // 格式化错误消息（保留换行符）
        const errorMessage = status.error_message || '分析过程中发生错误'
        progressInfo.value.message = errorMessage

        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
          pollingTimer.value = null
        }

        // 任务失败时清除缓存
        clearTaskCache()

        // 显示友好的错误提示（使用 dangerouslyUseHTMLString 支持换行）
        ElMessage({
          type: 'error',
          message: errorMessage.replace(/\n/g, '<br>'),
          dangerouslyUseHTMLString: true,
          duration: 10000, // 显示10秒，让用户有时间阅读
          showClose: true
        })

      } else if (status.status === 'running') {
        // 分析进行中，更新进度
        console.log('🔄 轮询中设置 analysisStatus 为 running')
        analysisStatus.value = 'running'
        updateProgressInfo(status)
      }

    } catch (error) {
      console.error('获取任务状态失败:', error)
      // 继续轮询，不中断
    }
  }, 5000) // 每5秒轮询一次
}

// 更新进度信息
const updateProgressInfo = (status: any) => {
  console.log('🔄 更新进度信息:', status)
  console.log('🔄 当前进度信息:', progressInfo.value)

  // 使用后端返回的实际进度数据
  if (status.progress !== undefined) {
    console.log('📊 更新进度:', status.progress)
    progressInfo.value.progress = status.progress
  }

  if (status.current_step_name) {
    console.log('📋 更新步骤:', status.current_step_name)
    progressInfo.value.currentStep = status.current_step_name
  }

  if (status.current_step_description) {
    console.log('📝 更新步骤描述:', status.current_step_description)
    progressInfo.value.currentStepDescription = status.current_step_description
  }

  if (status.message) {
    console.log('💬 更新消息:', status.message)
    progressInfo.value.message = status.message
  }

  // 接收后端返回的时间数据
  if (status.elapsed_time !== undefined) {
    progressInfo.value.elapsedTime = status.elapsed_time
  }

  if (status.remaining_time !== undefined) {
    progressInfo.value.remainingTime = status.remaining_time
  }

  if (status.estimated_total_time !== undefined) {
    progressInfo.value.totalTime = status.estimated_total_time
  }

  // 如果后端提供了步骤数据，更新步骤列表
  if (status.steps && Array.isArray(status.steps)) {
    if (analysisSteps.value.length === 0) {
      // 首次生成步骤列表
      analysisSteps.value = generateStepsFromBackend(status.steps)
      console.log('📋 从后端生成步骤列表:', analysisSteps.value.length, '个步骤')
    }
  }

  console.log('🔄 更新后进度信息:', progressInfo.value)

  // 更新分析步骤状态
  updateAnalysisSteps(status)

  // 前端不进行估算，只展示后端返回的数据
  progressInfo.value.message = status.message || '分析正在进行中...'
}

// 重新开始分析
const restartAnalysis = () => {
  // 清除任务缓存
  clearTaskCache()

  analysisStatus.value = 'idle'
  showResults.value = false
  analysisResults.value = null
  currentTaskId.value = ''
  progressInfo.value = {
    progress: 0,
    currentStep: '',
    currentStepDescription: '',
    message: '',
    elapsedTime: 0,
    remainingTime: 0,
    totalTime: 0
  }

  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}


// 通用字段提取辅助：从对象中按多个候选 key 依次取值
const pickFieldValue = (obj: any, candidates: string[], fallback: any = null): any => {
  if (!obj) return fallback
  for (const k of candidates) {
    const v = (obj as any)[k]
    if (v !== undefined && v !== null && v !== '' && v !== 'N/A') return v
  }
  return fallback
}

// 格式化普通字段（优先中文 key，兼容英文 key）
const formatFieldValue = (obj: any, candidates: string[]): string => {
  const v = pickFieldValue(obj, candidates)
  if (v === null || v === undefined || v === '') return '--'
  if (typeof v === 'number') {
    return Number.isInteger(v) ? String(v) : v.toFixed(2)
  }
  return String(v)
}

// 格式化为百分比（0~1 → 0%~100%）
const formatPctField = (obj: any, candidates: string[]): string => {
  const v = pickFieldValue(obj, candidates)
  if (v === null || v === undefined || v === '' || v === '--') return '0'
  const n = parseFloat(String(v))
  if (isNaN(n)) return '0'
  if (n > 1) return Math.round(n).toString()
  return Math.round(n * 100).toString()
}

// 🔹 内容精炼函数：智能选择高价值句子
const refineContent = (rawContent: string, maxLen: number = 260): string => {
  if (!rawContent || typeof rawContent !== 'string') return ''
  let text = rawContent.trim()
  if (!text) return ''

  // 1. 清理：去除 Markdown 标题、表格、分隔线
  text = text.replace(/^[>#]{2,}\s*/gm, '')
  text = text.replace(/^[#*]{1,3}\s*/gm, '')
  text = text.replace(/\|[\s\S]*?\|/gm, '') // 移除表格
  text = text.replace(/(?:---|\*{3,})/gm, '')
  text = text.replace(/\*\*/g, '')

  // 2. 按段落分割成段落数组
  let paragraphs = text.split(/\n\s*\n/)
  if (paragraphs.length === 1) {
    // 没有空行分割，按句号分割
    const sentences = text.split(/(?<=[。！？!?])/).filter(s => s.trim().length > 0)
    paragraphs = sentences.length > 1 ? sentences : [text]
  }

  // 3. 过滤掉太短（去除无效内容（包含无效段落（删除
  // 3. 评分后）-type
  // 3. 评分后）：去除过的内容）：
  // 3. 评分过后，保留有价值的句子
  const valid_paragraphs = paragraphs.filter(p => {
    const trimmed = p.trim()
    if (trimmed.length < 5) return false
    // 过滤掉"开始，获取内容" 是一个非常的内容
    // 过滤掉明显的套话/模板文本去除短信息的内容
    if (/^(好的|数据已|数据|以下|分析|基于)/i.test(trimmed.slice(0, 20)))
      return false
    return true
  })

  if (valid_paragraphs.length === 0) {
    valid_paragraphs.push(paragraphs[0])
  }

  // 4. 对每个段落进行句子级精选，确保不超过 maxLen 字符
  const result_parts: string[] = []
  let current_len = 0

  for (const para of valid_paragraphs) {
    const trimmed = para.trim()
    if (current_len + trimmed.length <= maxLen) {
      result_parts.push(trimmed)
      current_len += trimmed.length + 2
    } else {
      // 找到最后一个句号，保留句子级精选句子级句子结束处的前一句，确保句子完整
      const remaining = maxLen - current_len - 2
      if (remaining > 30) {
        // 智能截断到最后一个中文句号
        const lastPeriod = trimmed.lastIndexOf('。', remaining)
        const cutPos = Math.max(lastPeriod, trimmed.indexOf('。'))
        const cutLen = Math.min(trimmed.length, cutPos === -1 ? remaining : cutPos + 1)
        result_parts.push(trimmed.substring(0, cutLen))
      }
      break
    }
  }

  // 5. 合并并确保总长度限制
  const result = result_parts.join('；')
  return result.length > maxLen ? result.substring(0, maxLen) + '...' : result
}

// 🔹 获取情绪分析内容（从多个字段提取并精炼
const getSentimentContent = (results: any): string => {
  if (!results) return ''
  const reports = results.reports || results.state || {}
  const decision = results.decision || {}

  // 优先级：决策中的情绪字段 > sentiment_report
  const candidates = [
    decision.情绪分析 || decision.sentiment_summary || '',
    reports.sentiment_report || '',
    reports.news_report || '',
    reports.market_report || ''
  ]

  for (const c of candidates) {
    if (c && c.length > 10) {
      return refineContent(c, 260)
    }
  }
  return ''
}

// 🔹 获取精炼后的决策字段
const getRefinedField = (results: any, field: string, maxLen: number = 260): string => {
  if (!results || !results.decision) return ''
  const value = results.decision[field]
  if (!value) return ''
  return refineContent(String(value), maxLen)
}

// 获取操作标签类型（支持完整 5 档中文评级）
const getActionTagType = (action: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  if (!action) return 'info'
  // 按关键字匹配（支持 "强烈买入" / "买入" / "减仓" / "卖出" 等）
  if (action.includes('强烈买入') || action.includes('强力买入')) return 'success'
  if (action.includes('买入') || action.includes('BUY') || action.includes('buy')) return 'success'
  if (action.includes('卖出') || action.includes('SELL') || action.includes('sell')) return 'danger'
  if (action.includes('减仓') || action.includes('减持')) return 'danger'
  if (action.includes('持有') || action.includes('HOLD') || action.includes('hold')) return 'warning'
  if (action.includes('观望') || action.includes('中性')) return 'info'
  // 兜底映射表
  const actionTypes: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    '买入': 'success',
    '持有': 'warning',
    '卖出': 'danger',
    '观望': 'info',
    '强烈买入': 'success',
    '减仓': 'danger',
    '中性': 'info',
    'BUY': 'success',
    'HOLD': 'warning',
    'SELL': 'danger',
  }
  return actionTypes[action] || 'info'
}

// 获取分析报告
const getAnalysisReports = (data: any) => {
  console.log('📊 getAnalysisReports 输入数据:', data)
  const reports: Array<{title: string, content: any}> = []

  // 优先从 reports 字段获取数据（新的API格式）
  let reportsData = data
  if (data && data.reports && typeof data.reports === 'object') {
    reportsData = data.reports
    console.log('📊 使用 data.reports:', reportsData)
  } else if (data && data.state && typeof data.state === 'object') {
    reportsData = data.state
    console.log('📊 使用 data.state:', reportsData)
  } else {
    console.log('📊 没有找到有效的报告数据')
    return reports
  }

  // 定义报告映射（按照完整的分析流程顺序）
  const reportMappings = [
    // 分析师团队 (7个) - A股特有：政策、游资、解禁
    { key: 'market_report', title: '📈 市场技术分析', category: '分析师团队' },
    { key: 'sentiment_report', title: '💭 市场情绪分析', category: '分析师团队' },
    { key: 'news_report', title: '📰 新闻事件分析', category: '分析师团队' },
    { key: 'fundamentals_report', title: '💰 基本面分析', category: '分析师团队' },
    { key: 'policy_report', title: '🏛️ 政策分析师', category: '分析师团队' },
    { key: 'hot_money_report', title: '🔥 游资追踪师', category: '分析师团队' },
    { key: 'lockup_report', title: '🔒 解禁监控师', category: '分析师团队' },

    // 研究团队 (3个)
    { key: 'bull_researcher', title: '🐂 多头研究员', category: '研究团队' },
    { key: 'bear_researcher', title: '🐻 空头研究员', category: '研究团队' },
    { key: 'research_team_decision', title: '🔬 研究经理决策', category: '研究团队' },

    // 交易团队 (1个)
    { key: 'trader_investment_plan', title: '💼 交易员计划', category: '交易团队' },

    // 风险管理团队 (4个)
    { key: 'risky_analyst', title: '⚡ 激进分析师', category: '风险管理团队' },
    { key: 'safe_analyst', title: '🛡️ 保守分析师', category: '风险管理团队' },
    { key: 'neutral_analyst', title: '⚖️ 中性分析师', category: '风险管理团队' },
    { key: 'risk_management_decision', title: '👔 投资组合经理', category: '风险管理团队' },

    // 最终决策 (1个)
    { key: 'final_trade_decision', title: '🎯 最终交易决策', category: '最终决策' },

    // 兼容旧格式
    { key: 'investment_plan', title: '📋 投资建议', category: '其他' },
    { key: 'investment_debate_state', title: '🔬 研究团队决策（旧）', category: '其他' },
    { key: 'risk_debate_state', title: '⚖️ 风险管理团队（旧）', category: '其他' }
  ]

  // 遍历所有可能的报告
  reportMappings.forEach(mapping => {
    const content = reportsData[mapping.key]
    if (content) {
      console.log(`📊 找到报告: ${mapping.key} -> ${mapping.title}`)
      reports.push({
        title: mapping.title,
        content: content
      })
    }
  })

  console.log(`📊 总共找到 ${reports.length} 个报告`)

  // 设置第一个报告为默认激活标签页
  if (reports.length > 0 && !activeReportTab.value) {
    activeReportTab.value = '0'
  }

  return reports
}

// 获取报告图标
const getReportIcon = (title: string) => {
  const iconMap: Record<string, string> = {
    '📈 市场技术分析': '📈',
    '💰 基本面分析': '💰',
    '📰 新闻事件分析': '📰',
    '💭 市场情绪分析': '💭',
    '📋 投资建议': '📋',
    '🔬 研究团队决策': '🔬',
    '💼 交易团队计划': '💼',
    '⚖️ 风险管理团队': '⚖️',
    '🎯 最终交易决策': '🎯'
  }
  return iconMap[title] || '📊'
}

// 获取报告名称（去掉图标）
const getReportName = (title: string) => {
  return title.replace(/^[^\s]+\s/, '')
}

// 获取报告描述
const getReportDescription = (title: string) => {
  const descMap: Record<string, string> = {
    '📈 市场技术分析': '技术指标、价格趋势、支撑阻力位分析',
    '💰 基本面分析': '财务数据、估值水平、盈利能力分析',
    '📰 新闻事件分析': '相关新闻事件、市场动态影响分析',
    '💭 市场情绪分析': '投资者情绪、社交媒体情绪指标',
    '📋 投资建议': '具体投资策略、仓位管理建议',
    '🔬 研究团队决策': '多头/空头研究员辩论分析，研究经理综合决策',
    '💼 交易团队计划': '专业交易员制定的具体交易执行计划',
    '⚖️ 风险管理团队': '激进/保守/中性分析师风险评估，投资组合经理最终决策',
    '🎯 最终交易决策': '综合所有团队分析后的最终投资决策'
  }
  return descMap[title] || '详细分析报告'
}

// 格式化报告内容
const formatReportContent = (content: any) => {
  console.log('🎨 [DEBUG] formatReportContent 被调用:', {
    content: content,
    type: typeof content,
    length: typeof content === 'string' ? content.length : 'N/A'
  })

  // 确保content是字符串类型
  if (!content) {
    console.log('⚠️ [DEBUG] content为空，返回空字符串')
    return ''
  }

  // 如果content不是字符串，转换为字符串
  let stringContent = ''
  if (typeof content === 'string') {
    stringContent = content
    console.log('✅ [DEBUG] content是字符串，长度:', stringContent.length)
  } else if (typeof content === 'object') {
    // 如果是对象，尝试提取有用信息
    if (content.judge_decision) {
      stringContent = content.judge_decision
      console.log('📝 [DEBUG] 从对象中提取judge_decision')
    } else {
      stringContent = JSON.stringify(content, null, 2)
      console.log('📝 [DEBUG] 将对象转换为JSON字符串')
    }
  } else {
    stringContent = String(content)
    console.log('📝 [DEBUG] 将内容转换为字符串')
  }

  try {
    // 使用marked库将Markdown转换为HTML
    const htmlContent = marked.parse(stringContent) as string

    console.log('🎨 [DEBUG] Marked转换完成，HTML长度:', htmlContent.length)
    console.log('🎨 [DEBUG] HTML前200字符:', htmlContent.substring(0, 200))

    return htmlContent
  } catch (error) {
    console.error('❌ [ERROR] Marked转换失败:', error)
    // 如果marked转换失败，回退到简单的文本显示
    return `<pre style="white-space: pre-wrap; font-family: inherit;">${stringContent}</pre>`
  }
}

// 下载报告
const downloadReport = async (format: string = 'markdown') => {
  try {
    if (!analysisResults.value && !currentTaskId.value) {
      ElMessage.error('报告尚未生成，无法下载')
      return
    }

    // 显示加载提示
    const loadingMsg = ElMessage({
      message: `正在生成${getFormatName(format)}格式报告...`,
      type: 'info',
      duration: 0
    })

    const reportId = (analysisResults.value?.id as any) || currentTaskId.value
    const res = await fetch(`/api/reports/${reportId}/download?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    loadingMsg.close()

    if (!res.ok) {
      const errorText = await res.text()
      throw new Error(errorText || `HTTP ${res.status}`)
    }

    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const code =
      analysisResults.value?.stock_code ||
      analysisResults.value?.stock_symbol ||
      analysisResults.value?.symbol ||
      'stock'
    const dateStr = analysisResults.value?.analysis_date || new Date().toISOString().slice(0, 10)

    // 根据格式设置文件扩展名
    const ext = getFileExtension(format)
    a.download = `${String(code)}_分析报告_${String(dateStr).slice(0, 10)}.${ext}`

    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    ElMessage.success(`${getFormatName(format)}报告下载成功`)
  } catch (err: any) {
    console.error('下载报告出错:', err)

    // 显示详细错误信息
    if (err.message && err.message.includes('pandoc')) {
      ElMessage.error({
        message: 'PDF/Word 导出需要安装 pandoc 工具',
        duration: 5000
      })
    } else {
      ElMessage.error(`下载报告失败: ${err.message || '未知错误'}`)
    }
  }
}

// 辅助函数：获取格式名称
const getFormatName = (format: string): string => {
  const names: Record<string, string> = {
    'markdown': 'Markdown',
    'docx': 'Word',
    'pdf': 'PDF',
    'json': 'JSON'
  }
  return names[format] || format
}

// 辅助函数：获取文件扩展名
const getFileExtension = (format: string): string => {
  const extensions: Record<string, string> = {
    'markdown': 'md',
    'docx': 'docx',
    'pdf': 'pdf',
    'json': 'json'
  }
  return extensions[format] || 'txt'
}

// 辅助函数：将字符串内容转换为 DebateRoundItem 数组
const convertToDebateRounds = (content: string | string[] | any[] | undefined, index: number = 1): any[] => {
  if (!content) return []
  if (Array.isArray(content)) {
    return content.map((item, i) => {
      if (typeof item === 'string') {
        return { round: i + 1, content: item, timestamp: '' }
      } else if (item && typeof item === 'object') {
        return { round: item.round || i + 1, content: item.content || JSON.stringify(item), timestamp: item.timestamp || '' }
      }
      return { round: i + 1, content: String(item), timestamp: '' }
    })
  }
  if (typeof content === 'string') {
    // 如果是字符串，尝试按 "Round" 或 "第X轮" 分割为多轮
    let rounds: string[] = []
    const roundPatterns = [
      /\n\s*(第\s*\d+\s*轮|Round\s*\d+)\s*[:：]?\s*\n/gi,
      /\n\s*(--+\s*\n|==+\s*\n)/g
    ]

    let splitted = false
    for (const pattern of roundPatterns) {
      if (pattern.test(content)) {
        rounds = content.split(pattern).filter((r: string) => r.trim().length > 10)
        splitted = true
        break
      }
    }

    if (!splitted) {
      rounds = [content]
    }

    return rounds.map((text: string, i: number) => ({
      round: i + 1,
      content: text.trim(),
      timestamp: ''
    }))
  }
  return []
}

// 打开辩论抽屉
const openDebateDrawer = () => {
  // 从 reports 中提取辩论数据
  const reports = analysisResults.value?.reports || {}
  const state = analysisResults.value?.state || {}

  debateData.value = {
    // 多头研究员历史
    bull_history: convertToDebateRounds(reports.bull_researcher || state.bull_researcher, 1),
    // 空头研究员历史
    bear_history: convertToDebateRounds(reports.bear_researcher || state.bear_researcher, 2),
    // 激进分析师历史
    risky_history: convertToDebateRounds(reports.risky_analyst || state.risky_analyst, 3),
    // 保守分析师历史
    safe_history: convertToDebateRounds(reports.safe_analyst || state.safe_analyst, 4),
    // 中性分析师历史
    neutral_history: convertToDebateRounds(reports.neutral_analyst || state.neutral_analyst, 5),
    // 研究总监裁决
    judge_decision: reports.research_team_decision || state.research_team_decision || '',
    // 组合经理最终决策
    final_decision: reports.risk_management_decision || state.risk_management_decision || ''
  }

  // 调试信息
  console.log('🔥 辩论抽屉数据已加载:', {
    bull_len: debateData.value?.bull_history?.length || 0,
    bear_len: debateData.value?.bear_history?.length || 0,
    risky_len: debateData.value?.risky_history?.length || 0,
    safe_len: debateData.value?.safe_history?.length || 0,
    neutral_len: debateData.value?.neutral_history?.length || 0,
    has_judge: !!debateData.value?.judge_decision,
    has_final: !!debateData.value?.final_decision
  })

  debateDrawerVisible.value = true
}

// 解析投资建议
const parseRecommendation = () => {
  if (!analysisResults.value) return null

  // 从多个可能的字段中提取投资建议
  const rec = analysisResults.value.recommendation ||
              analysisResults.value.summary ||
              analysisResults.value.decision?.action || ''

  const traderPlan = analysisResults.value.reports?.trader_investment_plan || ''
  const allReports = Object.values(analysisResults.value.reports || {}).join(' ')

  // 解析操作类型
  let action: 'buy' | 'sell' | null = null
  const recStr = String(rec).toLowerCase()
  const allText = (recStr + ' ' + String(traderPlan).toLowerCase() + ' ' + allReports.toLowerCase())

  if (allText.includes('买入') || allText.includes('buy') || allText.includes('增持')) {
    action = 'buy'
  } else if (allText.includes('卖出') || allText.includes('sell') || allText.includes('减持')) {
    action = 'sell'
  }

  if (!action) return null

  // 解析目标价格
  // 🔥 严格模式：只匹配明确的"目标价"或"目标价格"关键词，不匹配通用的"价格"或"当前价格"
  // 排除：止损价格、当前价格、参考价格 等
  let targetPrice: number | null = null
  const priceMatch = allText.match(/目标价[格]?[：:]\s*([0-9.]+)/)
  if (priceMatch) {
    const extracted = parseFloat(priceMatch[1])
    // 验证：只接受合理范围内的价格（中国A股一般在 1-1000 元）
    // 排除明显不合理的捏造价格（如 15.0 这种不合理的持有目标）
    if (extracted > 0 && extracted < 10000) {
      targetPrice = extracted
    }
  }

  // 解析置信度
  const confidence = analysisResults.value.decision?.confidence ||
                    analysisResults.value.confidence_score ||
                    0

  // 解析风险等级
  const riskLevel = analysisResults.value.risk_level ||
                   analysisResults.value.decision?.risk_level ||
                   '中等'

  return {
    action,
    targetPrice,
    confidence: typeof confidence === 'number' ? confidence : 0,
    riskLevel: String(riskLevel)
  }
}

// 一键模拟下单（应用到交易）
const goSimOrder = async () => {
  try {
    if (!analysisResults.value) {
      ElMessage.warning('暂无可用的分析结果')
      return
    }

    // 获取股票代码（兼容新旧字段）
    const code = analysisResults.value.symbol ||
                 analysisResults.value.stock_symbol ||
                 analysisResults.value.stock_code ||
                 analysisForm.symbol ||
                 analysisForm.stockCode
    if (!code) {
      ElMessage.warning('未识别到股票代码')
      return
    }

    // 解析投资建议
    const recommendation = parseRecommendation()
    if (!recommendation) {
      ElMessage.warning('无法解析投资建议，请检查分析结果')
      return
    }

    // 获取账户信息
    const accountRes = await paperApi.getAccount()
    if (!accountRes.success || !accountRes.data) {
      ElMessage.error('获取账户信息失败')
      return
    }

    const account = accountRes.data.account
    const positions = accountRes.data.positions

    // 查找当前持仓
    const currentPosition = positions.find(p => p.code === code)

    // 获取当前实时价格
    let currentPrice = 10 // 默认价格
    try {
      const quoteRes = await stocksApi.getQuote(code)
      if (quoteRes.success && quoteRes.data && quoteRes.data.price) {
        currentPrice = quoteRes.data.price
      }
    } catch (error) {
      console.warn('获取实时价格失败，使用默认价格')
    }

    // 计算建议交易数量
    let suggestedQuantity = 0
    let maxQuantity = 0

    if (recommendation.action === 'buy') {
      // 买入：根据可用资金和当前价格计算
      const availableCash = account.cash
      maxQuantity = Math.floor(Number(availableCash) / Number(currentPrice) / 100) * 100 // 100股为单位
      const suggested = Math.floor(maxQuantity * 0.2) // 建议使用20%资金
      suggestedQuantity = Math.floor(suggested / 100) * 100 // 向下取整到100的倍数
      suggestedQuantity = Math.max(100, suggestedQuantity) // 至少100股
    } else {
      // 卖出：根据当前持仓计算
      if (!currentPosition || currentPosition.quantity === 0) {
        ElMessage.warning('当前没有持仓，无法卖出')
        return
      }
      maxQuantity = currentPosition.quantity
      suggestedQuantity = Math.floor(maxQuantity / 100) * 100 // 向下取整到100的倍数
      suggestedQuantity = Math.max(100, suggestedQuantity) // 至少100股
    }

    // 用户可修改的价格和数量（使用reactive）
    const tradeForm = reactive({
      price: currentPrice,
      quantity: suggestedQuantity
    })

    // 显示可编辑的确认对话框
    const actionText = recommendation.action === 'buy' ? '买入' : '卖出'
    const actionColor = recommendation.action === 'buy' ? '#67C23A' : '#F56C6C'

    // 创建一个响应式的消息组件
    const MessageComponent = {
      setup() {
        // 计算预计金额
        const estimatedAmount = computed(() => {
          return (tradeForm.price * tradeForm.quantity).toFixed(2)
        })

        return () => h('div', { style: 'line-height: 2;' }, [
          h('p', [
            h('strong', '股票代码：'),
            h('span', code)
          ]),
          h('p', [
            h('strong', '操作类型：'),
            h('span', { style: `color: ${actionColor}; font-weight: bold;` }, actionText)
          ]),
          h('p', [
            h('strong', '当前价格：'),
            h('span', `${currentPrice.toFixed(2)}元`)
          ]),
          h('div', { style: 'margin: 16px 0;' }, [
            h('p', { style: 'margin-bottom: 8px;' }, [
              h('strong', '交易价格：'),
              h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(可修改)')
            ]),
            h(ElInputNumber, {
              modelValue: tradeForm.price,
              'onUpdate:modelValue': (val: number | undefined) => { tradeForm.price = val ?? 0 },
              min: 0.01,
              max: 9999,
              precision: 2,
              step: 0.01,
              style: 'width: 200px;',
              controls: true
            })
          ]),
          h('div', { style: 'margin: 16px 0;' }, [
            h('p', { style: 'margin-bottom: 8px;' }, [
              h('strong', '交易数量：'),
              h('span', { style: 'color: #909399; font-size: 12px; margin-left: 8px;' }, '(可修改，100股为单位)')
            ]),
            h(ElInputNumber, {
              modelValue: tradeForm.quantity,
              'onUpdate:modelValue': (val: number | undefined) => { tradeForm.quantity = val ?? 0 },
              min: 100,
              max: maxQuantity,
              step: 100,
              style: 'width: 200px;',
              controls: true
            })
          ]),
          h('p', [
            h('strong', '预计金额：'),
            h('span', { style: 'color: #409EFF; font-weight: bold;' }, `${estimatedAmount.value}元`)
          ]),
          h('p', [
            h('strong', '置信度：'),
            h('span', `${(recommendation.confidence * 100).toFixed(1)}%`)
          ]),
          h('p', [
            h('strong', '风险等级：'),
            h('span', recommendation.riskLevel)
          ]),
          recommendation.action === 'buy' ? h('p', { style: 'color: #909399; font-size: 12px; margin-top: 12px;' },
            `可用资金：${typeof account.cash === 'number' ? account.cash.toFixed(2) : account.cash}元，最大可买：${maxQuantity}股`
          ) : null,
          recommendation.action === 'sell' ? h('p', { style: 'color: #909399; font-size: 12px; margin-top: 12px;' },
            `当前持仓：${maxQuantity}股`
          ) : null
        ])
      }
    }

    await ElMessageBox({
      title: '确认交易',
      message: h(MessageComponent),
      confirmButtonText: '确认下单',
      cancelButtonText: '取消',
      type: 'warning',
      beforeClose: (action, _instance, done) => {
        if (action === 'confirm') {
          // 验证输入
          if (tradeForm.quantity < 100 || tradeForm.quantity % 100 !== 0) {
            ElMessage.error('交易数量必须是100的整数倍')
            return
          }
          if (tradeForm.quantity > maxQuantity) {
            ElMessage.error(`交易数量不能超过${maxQuantity}股`)
            return
          }
          if (tradeForm.price <= 0) {
            ElMessage.error('交易价格必须大于0')
            return
          }

          // 检查资金是否充足
          if (recommendation.action === 'buy') {
            const totalAmount = tradeForm.price * tradeForm.quantity
            if (totalAmount > Number(account.cash)) {
              ElMessage.error('可用资金不足')
              return
            }
          }
        }
        done()
      }
    })

    // 执行交易
    const analysisId = analysisResults.value.id || currentTaskId.value
    const orderRes = await paperApi.placeOrder({
      code: code,
      side: recommendation.action,
      quantity: tradeForm.quantity,
      analysis_id: analysisId ? String(analysisId) : undefined
    })

    if (orderRes.success) {
      ElMessage.success(`${actionText}订单已提交成功！`)
      // 可选：跳转到模拟交易页面
      setTimeout(() => {
        router.push({ name: 'PaperTradingHome' })
      }, 1500)
    } else {
      ElMessage.error(orderRes.message || '下单失败')
    }

  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('一键模拟下单失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 组件销毁时清理定时器
onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
})

// keep-alive 组件被缓存时：保持轮询，但记录状态
onDeactivated(() => {
  console.log('⏸️ 单股分析组件被缓存 (deactivated)')
})

// keep-alive 组件被重新激活：恢复轮询状态
onActivated(() => {
  console.log('▶️ 单股分析组件被激活 (activated)')
  // 如果有正在运行的任务，立即查询一次状态
  if (currentTaskId.value && analysisStatus.value === 'running') {
    // 确保轮询仍在进行
    startPollingTaskStatus()
    // 立即查询一次状态
    setTimeout(async () => {
      try {
        const response = await analysisApi.getTaskStatus(currentTaskId.value)
        const status = response.data
        updateProgressInfo(status)
      } catch (e) {
        console.error('激活时查询任务状态失败:', e)
      }
    }, 300)
  }
})

// 页面可见性变化时的处理
const handleVisibilityChange = () => {
  if (document.hidden) {
    console.log('📱 页面隐藏，暂停轮询')
  } else {
    console.log('📱 页面显示，恢复轮询')
    // 页面重新可见时，立即查询一次状态
    if (currentTaskId.value && analysisStatus.value === 'running') {
      setTimeout(async () => {
        try {
          const response = await analysisApi.getTaskStatus(currentTaskId.value)
          const status = response.data // 响应拦截器已返回 response.data
          console.log('🔄 页面恢复查询状态:', status)
          if (status.status === 'running') {
            analysisStatus.value = 'running'
            updateProgressInfo(status)
          }
        } catch (error) {
          console.error('页面恢复查询状态失败:', error)
        }
      }, 500)
    }
  }
}

// 监听页面可见性变化
document.addEventListener('visibilitychange', handleVisibilityChange)

// 获取深度描述
const getDepthDescription = (depth: number) => {
  const descriptions = ['快速', '基础', '标准', '深度', '全面']
  return descriptions[depth - 1] || '标准'
}

// 获取进度条状态
const getProgressStatus = () => {
  if (analysisStatus.value === 'completed') {
    return 'success'
  } else if (analysisStatus.value === 'failed') {
    return 'exception'
  } else if (analysisStatus.value === 'running') {
    return '' // 默认状态，显示蓝色进度条
  }
  return ''
}

// 简单的时间格式化方法（只用于显示后端返回的时间）
const formatTime = (seconds: number) => {
  if (!seconds || seconds <= 0) {
    return '计算中...'
  }

  if (seconds < 60) {
    return `${Math.floor(seconds)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

// 更新分析步骤状态
const updateAnalysisSteps = (status: any) => {
  console.log('📋 步骤更新输入:', status)

  if (analysisSteps.value.length === 0) {
    console.log('📋 没有步骤定义，跳过更新')
    return
  }

  // 优先使用后端提供的详细步骤信息
  let currentStepIndex = 0

  if (status.current_step !== undefined) {
    // 后端提供了精确的步骤索引
    currentStepIndex = status.current_step
    console.log('📋 使用后端步骤索引:', currentStepIndex)
  } else {
    // 兜底方案：使用进度百分比估算
    const progress = status.progress_percentage || status.progress || 0
    if (progress > 0) {
      const progressRatio = progress / 100
      currentStepIndex = Math.floor(progressRatio * (analysisSteps.value.length - 1))
      if (progress > 0 && currentStepIndex === 0) {
        currentStepIndex = 1
      }
    }
    console.log('📋 使用进度估算步骤索引:', currentStepIndex, '进度:', progress)
  }

  // 确保索引在有效范围内
  currentStepIndex = Math.max(0, Math.min(currentStepIndex, analysisSteps.value.length - 1))

  console.log('📋 最终步骤索引:', currentStepIndex, '/', analysisSteps.value.length)

  // 更新所有步骤状态
  analysisSteps.value.forEach((step, index) => {
    if (index < currentStepIndex) {
      step.status = 'completed'
    } else if (index === currentStepIndex) {
      step.status = 'current'
    } else {
      step.status = 'pending'
    }
  })

  const statusSummary = analysisSteps.value.map((s, i) => `${i}:${s.status}`).join(', ')
  console.log('📋 步骤状态更新完成:', statusSummary)
}

// 初始化模型设置
const initializeModelSettings = async () => {
  try {
    const sortModelsByNewest = (configs: any[]) => {
      const getTimestamp = (config: any) => {
        const timeValue = config.created_at || config.updated_at
        const timestamp = timeValue ? new Date(timeValue).getTime() : 0
        return Number.isNaN(timestamp) ? 0 : timestamp
      }

      return [...configs].sort((a, b) => getTimestamp(b) - getTimestamp(a))
    }

    // 获取默认模型
    const defaultModels = await configApi.getDefaultModels()
    modelSettings.value.quickAnalysisModel = defaultModels.quick_analysis_model
    modelSettings.value.deepAnalysisModel = defaultModels.deep_analysis_model

    // 获取所有可用的模型列表
    const llmConfigs = await configApi.getLLMConfigs()
    availableModels.value = sortModelsByNewest(
      llmConfigs.filter((config: any) => config.enabled)
    )

    console.log('✅ 加载模型配置成功:', {
      quick: modelSettings.value.quickAnalysisModel,
      deep: modelSettings.value.deepAnalysisModel,
      available: availableModels.value.length
    })
    console.log('🔍 可用模型详细信息:', availableModels.value.map(m => ({
      model_name: m.model_name,
      model_display_name: m.model_display_name,
      provider: m.provider
    })))
  } catch (error) {
    console.error('加载默认模型配置失败:', error)
    modelSettings.value.quickAnalysisModel = 'qwen-turbo'
    modelSettings.value.deepAnalysisModel = 'qwen-max'
  }
}

// 任务状态缓存管理
const TASK_CACHE_KEY = 'trading_analysis_task'
const TASK_CACHE_DURATION = 30 * 60 * 1000 // 30分钟

// 保存任务状态到缓存
const saveTaskToCache = (taskId: string, taskData: any) => {
  const cacheData = {
    taskId,
    taskData,
    timestamp: Date.now()
  }
  localStorage.setItem(TASK_CACHE_KEY, JSON.stringify(cacheData))
  console.log('💾 任务状态已缓存:', taskId)
}

// 从缓存获取任务状态
const getTaskFromCache = () => {
  try {
    const cached = localStorage.getItem(TASK_CACHE_KEY)
    if (!cached) return null

    const cacheData = JSON.parse(cached)
    const now = Date.now()

    // 检查是否过期（30分钟）
    if (now - cacheData.timestamp > TASK_CACHE_DURATION) {
      localStorage.removeItem(TASK_CACHE_KEY)
      console.log('🗑️ 缓存已过期，已清理')
      return null
    }

    console.log('📦 从缓存恢复任务:', cacheData.taskId)
    return cacheData
  } catch (error) {
    console.error('❌ 读取缓存失败:', error)
    localStorage.removeItem(TASK_CACHE_KEY)
    return null
  }
}

// 清除任务缓存
const clearTaskCache = () => {
  localStorage.removeItem(TASK_CACHE_KEY)
  console.log('🗑️ 任务缓存已清除')
}

// 恢复任务状态
const restoreTaskFromCache = async () => {
  const cached = getTaskFromCache()
  if (!cached) return false

  try {
    console.log('🔄 尝试恢复任务状态:', cached.taskId)

    // 查询任务当前状态
    const response = await analysisApi.getTaskStatus(cached.taskId)
    const status = response.data // 响应拦截器已返回 response.data

    console.log('📊 恢复的任务状态:', status)

    if (status.status === 'completed') {
      // 任务已完成，显示结果
      currentTaskId.value = cached.taskId
      analysisStatus.value = 'completed'
      showResults.value = true
      analysisResults.value = status.result_data
      progressInfo.value.progress = 100
      progressInfo.value.currentStep = '分析完成'
      progressInfo.value.message = '分析已完成'

      // 恢复分析参数
      if (cached.taskData.parameters) {
        Object.assign(analysisForm, cached.taskData.parameters)
      }

      console.log('✅ 任务已完成，显示结果')
      return true

    } else if (status.status === 'running') {
      // 任务仍在运行，恢复进度显示
      currentTaskId.value = cached.taskId
      analysisStatus.value = 'running'
      showResults.value = false
      updateProgressInfo(status)

      // 恢复分析参数
      if (cached.taskData.parameters) {
        Object.assign(analysisForm, cached.taskData.parameters)
      }

      // 启动轮询
      startPollingTaskStatus()

      console.log('🔄 任务仍在运行，恢复进度显示')
      return true

    } else if (status.status === 'failed') {
      // 任务失败
      analysisStatus.value = 'failed'
      progressInfo.value.currentStep = '分析失败'
      progressInfo.value.message = status.error_message || '分析过程中发生错误'

      // 清除缓存
      clearTaskCache()

      console.log('❌ 任务失败')
      return true

    } else {
      // 其他状态，清除缓存
      clearTaskCache()
      console.log('🤔 未知任务状态，清除缓存')
      return false
    }

  } catch (error) {
    console.error('❌ 恢复任务状态失败:', error)
    // 如果查询失败，可能是任务不存在了，清除缓存
    clearTaskCache()
    return false
  }
}

// 🆕 模型能力相关辅助函数

/**
 * 获取能力等级文本
 */
const getCapabilityText = (level: number): string => {
  const texts: Record<number, string> = {
    1: '⚡基础',
    2: '📊标准',
    3: '🎯高级',
    4: '🔥专业',
    5: '👑旗舰'
  }
  return texts[level] || '📊标准'
}

/**
 * 获取能力等级标签类型
 */
const getCapabilityTagType = (level: number): 'success' | 'info' | 'warning' | 'danger' => {
  if (level >= 4) return 'danger'
  if (level >= 3) return 'warning'
  if (level >= 2) return 'success'
  return 'info'
}

/**
 * 判断是否适合快速分析
 */
const isQuickAnalysisRole = (roles: string[] | undefined): boolean => {
  if (!roles || !Array.isArray(roles)) return false
  return roles.includes('quick_analysis') || roles.includes('both')
}

/**
 * 判断是否适合深度分析
 */
/**
 * 显示分析深度的模型推荐说明
 */
const checkModelSuitability = async () => {
  const depthNames: Record<number, string> = {
    1: '快速',
    2: '基础',
    3: '标准',
    4: '深度',
    5: '全面'
  }
  const depthName = depthNames[analysisForm.researchDepth] || '标准'

  try {
    // 获取推荐模型
    const recommendRes = await recommendModels(depthName)
    const responseData = recommendRes?.data?.data

    if (responseData) {
      const quickModel = responseData.quick_model || '未知'
      const deepModel = responseData.deep_model || '未知'

      // 获取模型的显示名称
      const quickModelInfo = availableModels.value.find(m => m.model_name === quickModel)
      const deepModelInfo = availableModels.value.find(m => m.model_name === deepModel)

      const quickDisplayName = quickModelInfo?.model_display_name || quickModel
      const deepDisplayName = deepModelInfo?.model_display_name || deepModel

      // 获取推荐理由
      const reason = responseData.reason || ''

      // 构建推荐说明
      const depthDescriptions: Record<number, string> = {
        1: '快速浏览，获取基本信息',
        2: '基础分析，了解主要指标',
        3: '标准分析，全面评估股票',
        4: '深度研究，挖掘投资机会',
        5: '全面分析，专业投资决策'
      }

      const message = `${depthDescriptions[analysisForm.researchDepth] || '标准分析'}\n\n推荐模型配置：\n• 快速模型：${quickDisplayName}\n• 深度模型：${deepDisplayName}\n\n${reason}`

      modelRecommendation.value = {
        title: '💡 模型推荐',
        message,
        type: 'info',
        quickModel,
        deepModel
      }
    } else {
      // 如果没有推荐数据，显示通用说明
      const generalDescriptions: Record<number, string> = {
        1: '快速分析：使用基础模型即可，注重速度和成本',
        2: '基础分析：快速模型用基础级，深度模型用标准级',
        3: '标准分析：快速模型用基础级，深度模型用标准级以上',
        4: '深度分析：快速模型用标准级，深度模型用高级以上，需要推理能力',
        5: '全面分析：快速模型用标准级，深度模型用专业级以上，强推理能力'
      }

      modelRecommendation.value = {
        title: '💡 模型推荐',
        message: generalDescriptions[analysisForm.researchDepth] || generalDescriptions[3],
        type: 'info'
      }
    }
  } catch (error) {
    console.error('获取模型推荐失败:', error)
    // 显示通用说明
    const generalDescriptions: Record<number, string> = {
      1: '快速分析：使用基础模型即可，注重速度和成本',
      2: '基础分析：快速模型用基础级，深度模型用标准级',
      3: '标准分析：快速模型用基础级，深度模型用标准级以上',
      4: '深度分析：快速模型用标准级，深度模型用高级以上，需要推理能力',
      5: '全面分析：快速模型用标准级，深度模型用专业级以上，强推理能力'
    }

    modelRecommendation.value = {
      title: '💡 模型推荐',
      message: generalDescriptions[analysisForm.researchDepth] || generalDescriptions[3],
      type: 'info'
    }
  }
}

// 应用推荐的模型配置
const applyRecommendedModels = () => {
  if (modelRecommendation.value?.quickModel && modelRecommendation.value?.deepModel) {
    modelSettings.value.quickAnalysisModel = modelRecommendation.value.quickModel
    modelSettings.value.deepAnalysisModel = modelRecommendation.value.deepModel

    // 清除推荐提示
    modelRecommendation.value = null

    ElMessage.success('已应用推荐的模型配置')
  }
}

// 监听分析深度变化
import { watch } from 'vue'
watch(() => analysisForm.researchDepth, () => {
  checkModelSuitability()
})

// 监听模型选择变化
watch([() => modelSettings.value.quickAnalysisModel, () => modelSettings.value.deepAnalysisModel], () => {
  checkModelSuitability()
})

// 页面初始化
onMounted(async () => {
  initializeModelSettings()

  // 🆕 从用户偏好加载默认设置
  const authStore = useAuthStore()
  const appStore = useAppStore()

  // 优先从 authStore.user.preferences 读取，其次从 appStore.preferences 读取
  const userPrefs = authStore.user?.preferences
  if (userPrefs) {
    // 加载默认市场
    if (userPrefs.default_market) {
      analysisForm.market = userPrefs.default_market as MarketType
    }

    // 加载默认分析深度（转换为数字）
    if (userPrefs.default_depth) {
      analysisForm.researchDepth = parseInt(userPrefs.default_depth)
    }

    // 加载默认分析师
    if (userPrefs.default_analysts && userPrefs.default_analysts.length > 0) {
      analysisForm.selectedAnalysts = [...userPrefs.default_analysts]
    }

    console.log('✅ 已加载用户偏好设置:', {
      market: analysisForm.market,
      depth: analysisForm.researchDepth,
      analysts: analysisForm.selectedAnalysts
    })
  } else {
    // 降级到 appStore.preferences
    if (appStore.preferences.defaultMarket) {
      analysisForm.market = appStore.preferences.defaultMarket as MarketType
    }
    if (appStore.preferences.defaultDepth) {
      analysisForm.researchDepth = parseInt(appStore.preferences.defaultDepth)
    }
    console.log('✅ 已加载应用偏好设置（降级）')
  }

  // 接收一次路由参数（从筛选页带入）- 路由参数优先级最高
  const q = route.query as any
  const hasNewStock = !!q?.stock
  if (hasNewStock) {
    analysisForm.stockCode = String(q.stock)
    // 🔥 关键修复：如果有新的股票代码，清除旧任务缓存
    clearTaskCache()
    console.log('🔄 检测到新股票代码，已清除旧任务缓存:', q.stock)

    // 🆕 自动识别市场类型（如果URL中没有明确指定market参数）
    if (!q?.market) {
      const detectedMarket = getMarketByStockCode(analysisForm.stockCode)
      analysisForm.market = detectedMarket as MarketType
      console.log('🔍 自动识别市场类型:', analysisForm.stockCode, '->', detectedMarket)
    }
  }
  if (q?.market) analysisForm.market = normalizeMarketForAnalysis(q.market) as MarketType

  // 尝试恢复任务状态（仅当没有新股票代码时）
  if (!hasNewStock) {
    await restoreTaskFromCache()
  }

  // 🆕 初始检查模型适用性
  await checkModelSuitability()
})
</script>

<style lang="scss" scoped>
.single-analysis {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 24px;

  .page-header {
    margin-bottom: 32px;

    .header-content {
      background: var(--el-bg-color);
      padding: 32px;
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .title-section {
      .page-title {
        display: flex;
        align-items: center;
        font-size: 32px;
        font-weight: 700;
        color: #1a202c;
        margin: 0 0 8px 0;

        .title-icon {
          margin-right: 12px;
          color: #3b82f6;
        }
      }

      .page-description {
        font-size: 16px;
        color: #64748b;
        margin: 0;
      }
    }
  }

  .analysis-container {
    .main-form-card, .config-card {
      border-radius: 16px;
      border: none;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

      :deep(.el-card__header) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 16px 16px 0 0;
        padding: 20px 24px;

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;

          h3 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
          }
        }
      }

      :deep(.el-card__body) {
        padding: 24px;
      }
    }

    .analysis-form {
      .form-section {
        margin-bottom: 32px;
        width: 100%;
        display: flex;
        flex-direction: column;

        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: #1a202c;
          margin: 0 0 16px 0;
          padding-bottom: 8px;
          border-bottom: 2px solid #e2e8f0;
        }
      }

      .stock-input {
        :deep(.el-input__inner) {
          font-weight: 600;
          text-transform: uppercase;
        }

        &.is-error {
          :deep(.el-input__inner) {
            border-color: #f56c6c;
          }
        }
      }

      .error-message {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 8px;
        font-size: 12px;
        color: #f56c6c;

        .el-icon {
          font-size: 14px;
        }
      }

      .help-message {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 8px;
        font-size: 12px;
        color: #67c23a;

        .el-icon {
          font-size: 14px;
        }
      }

      .depth-selector {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;

        .depth-option {
          display: flex;
          align-items: center;
          padding: 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;

          &:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
          }

          &.active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: #1e40af;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
          }

          .depth-icon {
            font-size: 24px;
            margin-right: 12px;
          }

          .depth-info {
            .depth-name {
              font-weight: 600;
              margin-bottom: 4px;
            }

            .depth-desc {
              font-size: 12px;
              opacity: 0.8;
              margin-bottom: 2px;
            }

            .depth-time {
              font-size: 11px;
              opacity: 0.7;
            }
          }
        }
      }

      .analysts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;

        .analyst-card {
          display: flex;
          align-items: center;
          padding: 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;

          &:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
          }

          &.active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: #1e40af;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
          }

          &.disabled {
            opacity: 0.5;
            cursor: not-allowed;

            &:hover {
              transform: none;
              box-shadow: none;
              border-color: #e2e8f0;
            }
          }

          .analyst-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            font-size: 20px;
          }

          .analyst-content {
            flex: 1;

            .analyst-name {
              font-weight: 600;
              margin-bottom: 4px;
            }

            .analyst-desc {
              font-size: 12px;
              opacity: 0.8;
            }
          }

          .analyst-check {
            .check-icon {
              font-size: 20px;
              color: #3b82f6;
            }
          }

          &.active .analyst-check .check-icon {
            color: #1e40af;
          }
        }
      }
    }

    .config-card {
      .config-content {
        .config-section {
          margin-bottom: 24px;

          .config-title {
            font-size: 14px;
            font-weight: 600;
            color: #1a202c;
            margin: 0 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .model-config {
            .model-item {
              margin-bottom: 16px;

              .model-label {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 13px;
                color: #374151;

                .help-icon {
                  color: #9ca3af;
                  cursor: help;
                }
              }
            }
          }

          .option-list {
            .option-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 12px 0;
              border-bottom: 1px solid #f3f4f6;

              &:last-child {
                border-bottom: none;
              }

              .option-info {
                .option-name {
                  font-size: 14px;
                  font-weight: 500;
                  color: #374151;
                  display: block;
                  margin-bottom: 2px;
                }

                .option-desc {
                  font-size: 12px;
                  color: #6b7280;
                }
              }
            }
          }

          .custom-input {
            :deep(.el-textarea__inner) {
              border-radius: 8px;
              border: 1px solid #d1d5db;

              &:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
              }
            }
          }

          .input-help {
            font-size: 12px;
            color: #6b7280;
            margin-top: 8px;
          }

          .action-buttons {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin-top: 24px !important;
            width: 100% !important;
            text-align: center !important;

            .submit-btn.el-button {
              width: 280px !important;
              height: 56px !important;
              font-size: 18px !important;
              font-weight: 700 !important;
              background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
              border: none !important;
              border-radius: 16px !important;
              transition: all 0.3s ease !important;
              box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2) !important;
              min-width: 280px !important;
              max-width: 280px !important;

              &:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 12px 30px rgba(59, 130, 246, 0.4) !important;
                background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
              }

              &:disabled {
                opacity: 0.6 !important;
                transform: none !important;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1) !important;
              }

              .el-icon {
                margin-right: 8px !important;
                font-size: 20px !important;
              }

              span {
                font-size: 18px !important;
                font-weight: 700 !important;
              }
            }
          }
        }
      }
    }

    .action-section {
      margin-top: 24px;
      display: flex;
      gap: 16px;

      .submit-btn {
        flex: 1;
        height: 48px;
        font-size: 16px;
        font-weight: 600;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border: none;
        border-radius: 12px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
        }

        &:disabled {
          opacity: 0.6;
          transform: none;
          box-shadow: none;
        }
      }

      .reset-btn {
        height: 48px;
        font-size: 16px;
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        color: #6b7280;
        transition: all 0.3s ease;

        &:hover {
          border-color: #d1d5db;
          color: #374151;
          transform: translateY(-1px);
        }
      }
    }
  }
}

// 分析步骤样式
.step-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-left: 3px solid #e5e7eb;
  margin-left: 15px;
  position: relative;
  transition: all 0.3s ease;

  &.step-completed {
    border-left-color: #10b981;

    .step-icon {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }

    .step-title {
      color: #10b981;
      font-weight: 600;
    }

    .step-description {
      color: #059669;
    }
  }

  &.step-current {
    border-left-color: #3b82f6;
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.05) 0%, transparent 100%);

    .step-icon {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      color: white;
      box-shadow: 0 2px 12px rgba(59, 130, 246, 0.4);
    }

    .step-title {
      color: #3b82f6;
      font-weight: 700;
    }

    .step-description {
      color: #1d4ed8;
      font-weight: 500;
    }
  }

  &.step-pending {
    .step-icon {
      background: #f3f4f6;
      color: #9ca3af;
      border: 2px solid #e5e7eb;
    }

    .step-title {
      color: #6b7280;
    }

    .step-description {
      color: #9ca3af;
    }
  }
}

.step-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: -16px;
  margin-right: 16px;
  font-size: 14px;
  flex-shrink: 0;
  z-index: 1;
  transition: all 0.3s ease;
}

.completed-icon {
  color: white;
}

.current-icon {
  color: white;
}

.pending-icon {
  color: #9ca3af;
}

.step-content {
  flex: 1;
  min-width: 0;
  padding-right: 16px;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.4;
}

.step-description {
  font-size: 12px;
  line-height: 1.4;
  opacity: 0.9;
}

/* 脉冲动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

/* 为当前步骤图标添加脉冲效果 */
.step-current .step-icon {
  animation: pulse 2s ease-in-out infinite;
}
</style>

<style>
/* 全局样式确保按钮样式生效 */
.action-buttons {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 100% !important;
  text-align: center !important;
}

.large-analysis-btn.el-button {
  width: 280px !important;
  height: 56px !important;
  font-size: 18px !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
  border: none !important;
  border-radius: 16px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2) !important;
  min-width: 280px !important;
  max-width: 280px !important;
}

.large-analysis-btn.el-button:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 12px 30px rgba(59, 130, 246, 0.4) !important;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
}

.large-analysis-btn.el-button:disabled {
  opacity: 0.6 !important;
  transform: none !important;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1) !important;
}

.large-analysis-btn.el-button .el-icon {
  margin-right: 8px !important;
  font-size: 20px !important;
}

.large-analysis-btn.el-button span {
  font-size: 18px !important;
  font-weight: 700 !important;
}

/* 进度显示样式 */
.progress-section {
  margin-top: 24px;
}

.progress-card .progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-card .progress-header h4 {
  margin: 0;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 旋转动画 */
.rotating-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 总体进度信息 */
.overall-progress-info {
  margin-bottom: 24px;
}

.progress-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 进度条区域 */
.progress-bar-section {
  margin-bottom: 24px;
}

.main-progress-bar {
  :deep(.el-progress-bar__outer) {
    background-color: var(--el-fill-color);
    border-radius: 8px;
  }

  :deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
    border-radius: 8px;
    transition: width 0.6s ease;
  }

  :deep(.el-progress__text) {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

/* 当前任务信息 */
.current-task-info {
  background: var(--el-fill-color-light);
  border: 1px solid #3b82f6;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 8px;
}

.task-icon {
  color: #3b82f6;
}

.task-description {
  font-size: 14px;
  color: #1e40af;
  line-height: 1.5;
}

/* 分析步骤 */
.analysis-steps {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  padding: 20px;
}

.steps-title {
  margin: 0 0 16px 0;
  color: #1e293b;
  font-size: 16px;
  font-weight: 600;
}

.steps-container {
  max-height: 300px;
  overflow-y: auto;
}

/* 结果显示样式 */
.results-section {
  margin-top: 24px;
}

.results-card .results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-card .results-header h3 {
  margin: 0;
  color: #1f2937;
}

.results-card .result-meta {
  display: flex;
  gap: 8px;
}

/* 风险提示样式 */
.risk-disclaimer {
  margin-bottom: 24px;
  animation: fadeInDown 0.5s ease-out;
}

.risk-disclaimer :deep(.el-alert) {
  background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
  border: 2px solid #ffc107;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
}

.risk-disclaimer :deep(.el-alert__icon) {
  font-size: 24px;
  color: #ff6b00;
}

.disclaimer-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  line-height: 1.6;
}

.disclaimer-icon {
  font-size: 24px;
  color: #ff6b00;
  flex-shrink: 0;
  animation: pulse 2s ease-in-out infinite;
}

.disclaimer-text {
  color: #856404;
  flex: 1;
}

.disclaimer-text strong {
  color: #d63031;
  font-size: 16px;
  font-weight: 700;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.decision-section {
  margin-bottom: 32px;
}

.decision-section h4 {
  color: #1f2937;
  margin-bottom: 16px;
}

.decision-card {
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  padding: 20px;
}

.decision-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.decision-action {
  display: flex;
  align-items: center;
  gap: 12px;
}

.decision-action .label {
  font-weight: 600;
  color: #374151;
}

.decision-metrics {
  display: flex;
  gap: 24px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.metric-item .label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.metric-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 🔹 核心洞察卡片（6 张彩色卡片 + 可选持仓周期） */
.decision-insights {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

@media (max-width: 900px) {
  .decision-insights {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .decision-insights {
    grid-template-columns: 1fr;
  }
}

/* 通用卡片样式 */
.insight-card {
  position: relative;
  padding: 14px 16px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  transition: all 0.25s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 130px;
}

.insight-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  opacity: 0.8;
}

.insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}

.insight-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.insight-icon {
  font-size: 20px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 600;
}

.insight-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.insight-card-body {
  font-size: 13px;
  line-height: 1.75;
  color: #374151;
  flex: 1;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 每张卡片的专属配色 */
.insight-card.insight-core {
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 80%);
  border-color: #fde68a;
}
.insight-card.insight-core::before { background: #f59e0b; }
.insight-card.insight-core .insight-icon { background: #fef3c7; color: #f59e0b; }
.insight-card.insight-core .insight-title { color: #b45309; }

.insight-card.insight-investment {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 80%);
  border-color: #bfdbfe;
}
.insight-card.insight-investment::before { background: #3b82f6; }
.insight-card.insight-investment .insight-icon { background: #dbeafe; color: #3b82f6; }
.insight-card.insight-investment .insight-title { color: #1d4ed8; }

.insight-card.insight-sentiment {
  background: linear-gradient(135deg, #fdf2f8 0%, #ffffff 80%);
  border-color: #fbcfe8;
}
.insight-card.insight-sentiment::before { background: #ec4899; }
.insight-card.insight-sentiment .insight-icon { background: #fce7f3; color: #ec4899; }
.insight-card.insight-sentiment .insight-title { color: #be185d; }

.insight-card.insight-trend {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 80%);
  border-color: #bbf7d0;
}
.insight-card.insight-trend::before { background: #10b981; }
.insight-card.insight-trend .insight-icon { background: #d1fae5; color: #10b981; }
.insight-card.insight-trend .insight-title { color: #047857; }

.insight-card.insight-strategy {
  background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 80%);
  border-color: #ddd6fe;
}
.insight-card.insight-strategy::before { background: #8b5cf6; }
.insight-card.insight-strategy .insight-icon { background: #ede9fe; color: #8b5cf6; }
.insight-card.insight-strategy .insight-title { color: #6d28d9; }

.insight-card.insight-risk {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 80%);
  border-color: #fecaca;
}
.insight-card.insight-risk::before { background: #ef4444; }
.insight-card.insight-risk .insight-icon { background: #fee2e2; color: #ef4444; }
.insight-card.insight-risk .insight-title { color: #b91c1c; }

.insight-card.insight-holding {
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 80%);
  border-color: #bbf7d0;
}
.insight-card.insight-holding::before { background: #059669; }
.insight-card.insight-holding .insight-icon { background: #d1fae5; color: #059669; }
.insight-card.insight-holding .insight-title { color: #065f46; }

/* 旧 insight-item 样式（向后兼容） */
.insight-item {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.85);
  border-left: 3px solid #409EFF;
  border-radius: 4px;
}

.insight-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
  padding: 2px 8px;
  background: #e5f2ff;
  border-radius: 4px;
}

.insight-value {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 置信度/评分条 */
.decision-confidence {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(255, 251, 235, 0.55);
  border-radius: 8px;
}

.confidence-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 70px;
}

.confidence-item .label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.confidence-item .value {
  font-size: 14px;
  font-weight: 600;
  color: #f59e0b;
}

.decision-reasoning h5 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.decision-reasoning p {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.reports-section {
  margin-bottom: 32px;
}

.reports-section h4 {
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.report-content {
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.report-content h1,
.report-content h2,
.report-content h3 {
  color: var(--el-text-color-primary);
  margin: 16px 0 8px 0;
}

.report-content strong {
  color: var(--el-text-color-primary);
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* 分析报告标签页样式 */
.analysis-tabs-container {
  margin-top: 16px;
}

.analysis-tabs {
  /* 标签页头部样式 */
  :deep(.el-tabs__header) {
    margin: 0 0 20px 0;
    background: var(--el-fill-color-light);
    padding: 12px;
    border-radius: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border: 1px solid var(--el-border-color);
  }

  /* 标签页导航 */
  :deep(.el-tabs__nav-wrap) {
    &::after {
      display: none; /* 隐藏默认的底部边框 */
    }
  }

  /* 单个标签页样式 */
  :deep(.el-tabs__item) {
    height: 55px !important;
    line-height: 55px !important;
    padding: 0 20px !important;
    margin-right: 8px !important;
    background: var(--el-bg-color) !important;
    border: 2px solid var(--el-border-color) !important;
    border-radius: 12px !important;
    color: var(--el-text-color-regular) !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    position: relative !important;
    overflow: hidden !important;
    border-bottom: 2px solid var(--el-border-color) !important; /* 确保底部边框存在 */

    &:hover {
      background: var(--el-fill-color-light) !important;
      border-color: #2196f3 !important;
      transform: translateY(-2px) scale(1.02) !important;
      box-shadow: 0 4px 15px rgba(33,150,243,0.3) !important;
      color: #1976d2 !important;
    }

    &.is-active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
      color: white !important;
      border-color: #667eea !important;
      box-shadow: 0 6px 20px rgba(102,126,234,0.4) !important;
      transform: translateY(-3px) scale(1.05) !important;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 100%);
        border-radius: 10px;
        pointer-events: none;
      }
    }
  }

  /* 标签页内容区域 */
  :deep(.el-tabs__content) {
    padding: 0;
  }

  :deep(.el-tab-pane) {
    padding: 25px;
    background: var(--el-bg-color);
    border-radius: 15px;
    border: 1px solid var(--el-border-color);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin-top: 10px;
  }
}

/* 报告头部样式 */
.report-header {
  margin-bottom: 25px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 15px;
  border-left: 5px solid var(--el-color-primary);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);

  .report-title {
    display: flex;
    align-items: center;
    margin-bottom: 8px;

    .report-icon {
      font-size: 24px;
      margin-right: 12px;
    }

    .report-name {
      font-size: 20px;
      font-weight: 700;
      color: var(--el-text-color-primary);
    }
  }

  .report-description {
    color: var(--el-text-color-secondary);
    font-size: 16px;
    line-height: 1.5;
    margin-left: 36px; /* 对齐图标后的文字 */
  }
}

/* 报告内容包装器 */
.report-content-wrapper {
  background: var(--el-bg-color);
  padding: 25px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 报告内容样式增强 */
.report-content {
  line-height: 1.7;
  color: var(--el-text-color-regular);
  font-size: 16px;

  /* 标题样式 */
  h1, h2, h3, h4, h5, h6 {
    color: var(--el-text-color-primary) !important;
    margin: 20px 0 12px 0 !important;
    font-weight: 600 !important;
  }

  h1 { font-size: 24px !important; }
  h2 { font-size: 20px !important; }
  h3 { font-size: 18px !important; }
  h4 { font-size: 16px !important; }

  /* 段落样式 */
  p {
    margin: 12px 0 !important;
    line-height: 1.7 !important;
  }

  /* 强调文本 */
  strong, b {
    color: var(--el-text-color-primary) !important;
    font-weight: 600 !important;
  }

  /* 斜体文本 */
  em, i {
    color: var(--el-text-color-regular) !important;
    font-style: italic !important;
  }

  /* 列表样式 */
  ul, ol {
    margin: 12px 0 !important;
    padding-left: 24px !important;

    li {
      margin: 6px 0 !important;
      line-height: 1.6 !important;
    }
  }

  /* 代码样式 */
  code {
    background: var(--el-fill-color-light) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
    font-size: 14px !important;
    color: var(--el-color-danger) !important;
  }

  /* 引用样式 */
  blockquote {
    border-left: 4px solid var(--el-color-primary) !important;
    padding-left: 16px !important;
    margin: 16px 0 !important;
    background: var(--el-fill-color-light) !important;
    padding: 12px 16px !important;
    border-radius: 0 8px 8px 0 !important;
    font-style: italic !important;
    color: var(--el-text-color-regular) !important;
  }
}

/* 风险提示样式 */
.risk-disclaimer {
  margin-top: 24px;
  border-radius: 8px;

  :deep(.el-alert__content) {
    width: 100%;
  }

  :deep(.el-alert__title) {
    font-size: 14px;
    line-height: 1.6;
    color: #e6a23c;
  }
}
</style>
