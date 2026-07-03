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
            <el-tag type="warning" size="small" effect="plain">龙回头/N字反包</el-tag>
          </div>
        </div>
      </template>

      <div class="strategy-detail">
        <p class="strategy-overview">
          <strong>核心逻辑：</strong>主力用涨停板快速建仓或拉升后，会进行3-5天的缩量洗盘，清洗浮筹、测试支撑。
          当洗盘末端出现<strong>地量+长下影线</strong>（抛压衰竭）或<strong>放量突破5日线</strong>（洗盘结束）时，
          就是最佳介入时机，博弈主升浪启动。
        </p>
        
        <el-row :gutter="16" style="margin-top: 16px;">
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>涨停建仓</h4>
                <p>涨停板是主力信号：快速吸筹或启动，表明有市场地位和资金关注。筛选近期涨停股作为候选池。</p>
              </div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>缩量洗盘</h4>
                <p>涨停后3-8天缩量回调，成交量萎缩至涨停日的1/3以下，主力锁仓不动，散户恐慌抛售。回调期间收盘价基本在10日线上方。</p>
              </div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>地量止跌</h4>
                <p>洗盘末端第3-5天出现地量（近20日最低且涨停日1/3以下）+长下影线（实体比≥2倍），抛压衰竭，左侧潜伏买点。</p>
              </div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number">4</div>
              <div class="step-content">
                <h4>放量突破</h4>
                <p>放量（≥1.5倍均量）站上5日线和回调前高，5日线走平上翘且上穿10日线，上影线≤2.5%，洗盘确认结束，右侧确认买点。</p>
              </div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number" style="background: #f56c6c;">5</div>
              <div class="step-content">
                <h4>动态止盈止损</h4>
                <p>ATR止损（优先）：买入价下方0.4倍ATR；10日线止损（备选）；8天时间止盈；放量滞涨高位止盈；盈利后5日线/ATR移动止盈（取较高者）。</p>
              </div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="step-item">
              <div class="step-number" style="background: #409eff;">6</div>
              <div class="step-content">
                <h4>大盘环境过滤</h4>
                <p>市场上涨比例低于30%时空仓回避，极端熊市不交易，只在市场环境较好时操作，大幅降低系统性风险。</p>
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="signal-types" style="margin-top: 16px;">
          <el-divider content-position="left">信号演化路径（按时间顺序）</el-divider>
          <div class="signal-flow">
            <div class="signal-watch">
              <el-tag type="primary" effect="plain">缩量回调中</el-tag>
              <p class="signal-desc">缩量达标但未现止跌信号</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-watch">
              <el-tag type="info" effect="plain">底部观察</el-tag>
              <p class="signal-desc">地量出现，接近底部区域</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-buy-point">
              <el-tag type="warning" effect="dark">买点1</el-tag>
              <el-tag type="warning" effect="plain" style="margin-left: 4px;">左侧潜伏</el-tag>
              <p class="signal-desc">地量+长下影线（实体比≥2倍），地量日在第3-5天</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-buy-point">
              <el-tag type="success" effect="dark">买点2</el-tag>
              <el-tag type="success" effect="plain" style="margin-left: 4px;">右侧确认</el-tag>
              <p class="signal-desc">放量突破5日线+回调前高，5日线上穿10日线</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-sell-point">
              <el-tag type="danger" effect="dark">ATR止损</el-tag>
              <el-tag type="danger" effect="plain" style="margin-left: 4px;">优先</el-tag>
              <p class="signal-desc">买入价下方0.4倍ATR，动态止损适应波动率</p>
            </div>
          </div>
          <div class="signal-flow" style="margin-top: 12px;">
            <div class="signal-sell-point">
              <el-tag type="danger" effect="dark">10日止损</el-tag>
              <el-tag type="danger" effect="plain" style="margin-left: 4px;">备选</el-tag>
              <p class="signal-desc">收盘跌破10日线，趋势破坏止损</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-sell-point">
              <el-tag type="warning" effect="dark">时间止盈</el-tag>
              <el-tag type="warning" effect="plain" style="margin-left: 4px;">8天不过高</el-tag>
              <p class="signal-desc">涨停后8天未突破涨停价，上攻乏力</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-sell-point">
              <el-tag type="success" effect="dark">高位止盈</el-tag>
              <el-tag type="success" effect="plain" style="margin-left: 4px;">放量滞涨</el-tag>
              <p class="signal-desc">拉升途中天量滞涨，主力对敲出货</p>
            </div>
            <el-icon class="flow-arrow"><ArrowRight /></el-icon>
            <div class="signal-sell-point">
              <el-tag type="success" effect="dark">移动止盈</el-tag>
              <el-tag type="success" effect="plain" style="margin-left: 4px;">5日线/ATR取高</el-tag>
              <p class="signal-desc">盈利>3%开启，5日线与高点下方1倍ATR取较高者，让利润奔跑</p>
            </div>
          </div>
          <div class="signal-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>战法六大核心：涨停建仓→缩量洗盘→地量止跌→放量突破→动态止盈止损→大盘过滤。两个买点：左侧潜伏（试探轻仓）和右侧确认（重仓）。卖点按优先级：ATR止损→10日线止损→8日时间止盈→高位止盈→移动止盈。大盘上涨比例&lt;30%时空仓回避。</span>
          </div>
        </div>
      </div>
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
            <el-form-item>
              <template #label>
                <span>涨停回溯天数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">从当前日往前搜索涨停板的最大天数范围。注意：这是找涨停板的范围，与持仓天数无关。持仓时间由卖点规则（10日止损、8日时间止盈、高位止盈、5日线移动止盈）决定，通常持有3-15天。涨停阈值自动识别：主板10%，创业板/科创板20%，ST股5%，北交所30%</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>最少回调天数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">涨停后至少需要回调多少天才入选。太少则洗盘不充分，建议2-3天</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>最多回调天数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">涨停后最多回调多少天仍在关注范围。超过则可能趋势走弱，建议8天（战法要求超8天未收复则出局）</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>最低评分阈值</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">综合评分满分100分，包含：缩量20分、回调幅度15分、地量15分、下影线15分、空间位置10分、10日线10分、小阴小阳5分、突破5日线10分</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>缩量比例阈值</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">回调期均量相对于涨停日量的比例。0.5表示均量≤涨停日一半才算缩量达标。越小越严格，建议0.3-0.5</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>最少缩量天数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">回调期间至少有多少天的成交量达到缩量标准。建议2天以上确认洗盘有效</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>地量比例阈值</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">地量日成交量相对于涨停日的比例。0.35表示≤涨停日35%为地量。实际判断还包含"近20日最低量"标准</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>下影线比例阈值</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">下影线占最低价的比例，备用判断标准。实际主要用"下影线/实体≥1.5倍"判断，十字星时实体为0视为满足</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>站上10日线</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">10日线是洗盘生命线。开启后要求回调期间收盘价始终在10日线上方（允许1天跌破作为盘中洗盘）。跌破则趋势可能逆转</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-switch v-model="params.above_ma10" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item>
              <template #label>
                <span>突破5日线</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">右侧确认买点：开启后要求收盘站上5日线+5日线走平或上翘+放量≥指定倍数+无假突破（上影线&lt;3%）</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-switch v-model="params.breakout_ma5" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item v-if="params.breakout_ma5">
              <template #label>
                <span>突破放量倍数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">突破当天成交量需达到近5日均量的多少倍才算有效突破。建议1.5倍以上表明主力主动攻击</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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
            <el-form-item>
              <template #label>
                <span>返回数量</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">扫描结果最多返回多少只股票，按综合评分从高到低排序</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
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

        <el-row :gutter="24" v-show="activeTab === 'backtest'">
          <el-col :span="6">
            <el-form-item label="回测开始日期">
              <el-date-picker
                v-model="backtestParams.start_date"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择开始日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="回测结束日期">
              <el-date-picker
                v-model="backtestParams.end_date"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item>
              <template #label>
                <span>最大持有天数</span>
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">安全阀：实际卖出按三条卖点规则（10日止损、8天时间止盈、高位止盈），此参数为最晚卖出天数</div>
                  </template>
                  <el-icon class="help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
              <el-input-number
                v-model="backtestParams.hold_days"
                :min="1"
                :max="60"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="每次选股数">
              <el-input-number
                v-model="backtestParams.top_n"
                :min="1"
                :max="50"
                :step="1"
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
          <el-button type="success" :loading="backtestLoading" @click="doBacktest" size="large" style="margin-left: 12px;">
            <el-icon><DataLine /></el-icon>
            开始回测
          </el-button>
          <el-button :loading="loading" @click="resetParams" size="large" style="margin-left: 12px;">
            <el-icon><Refresh /></el-icon>
            重置参数
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" style="margin-top: 16px;">
      <!-- 扫描结果Tab -->
      <el-tab-pane label="扫描结果" name="scan">
        <el-card class="result-panel" shadow="never">
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
                <router-link :to="`/stocks/${row.code}`" class="stock-code">{{ row.code }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="名称" width="100" fixed="left">
              <template #default="{ row }">
                <router-link :to="`/stocks/${row.code}`" class="stock-name">{{ row.name }}</router-link>
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
            <el-table-column label="缩量回调" width="200">
              <template #default="{ row }">
                <div class="date-range">
                  <span class="date-item">{{ row.pullback_start_date || '-' }}</span>
                  <span class="date-arrow">→</span>
                  <span class="date-item">{{ row.pullback_end_date || '-' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="bottom_watch_start_date" label="底部观察日" width="110">
              <template #default="{ row }">
                <span v-if="row.bottom_watch_start_date" class="date-tag info">{{ row.bottom_watch_start_date }}</span>
                <span v-else class="empty-tag">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="left_buy_date" label="左侧买点" width="110">
              <template #default="{ row }">
                <span v-if="row.left_buy_date" class="date-tag warning">{{ row.left_buy_date }}</span>
                <span v-else class="empty-tag">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="right_buy_date" label="右侧买点" width="110">
              <template #default="{ row }">
                <span v-if="row.right_buy_date" class="date-tag success">{{ row.right_buy_date }}</span>
                <span v-else class="empty-tag">-</span>
              </template>
            </el-table-column>
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
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <router-link :to="{ path: '/analysis/single', query: { stock: row.code } }" class="table-link">分析</router-link>
                <el-button type="success" link @click="addToFavorites(row)">自选</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 回测分析Tab -->
      <el-tab-pane label="回测分析" name="backtest">
        <!-- 回测空状态 -->
        <el-card v-if="!backtestResult && !backtestLoading" shadow="never">
          <el-empty description="配置回测参数后点击开始回测，回测可能耗时2-5分钟">
            <el-button type="success" @click="doBacktest">立即回测</el-button>
          </el-empty>
        </el-card>

        <!-- 回测loading -->
        <el-card v-if="backtestLoading" shadow="never" v-loading="backtestLoading" element-loading-text="正在回测，请耐心等待（可能需要2-5分钟）...">
          <div style="height: 200px;"></div>
        </el-card>

        <!-- 回测结果 -->
        <div v-if="backtestResult">
          <!-- 核心指标卡片 -->
          <el-row :gutter="16">
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">回测期间所有买入信号触发的交易总数。每只股票每天只能买入一次，同一只股票不同日期会产生多笔交易。</div>
                  </template>
                  <div class="metric-label">总交易次数</div>
                </el-tooltip>
                <div class="metric-value">{{ backtestResult.total_trades }}</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">盈利交易数 ÷ 总交易数 × 100%。盈利定义为卖出价 > 买入价。胜率高不代表策略好，需要结合盈亏比分析。</div>
                  </template>
                  <div class="metric-label">胜率</div>
                </el-tooltip>
                <div class="metric-value" :class="backtestResult.win_rate >= 50 ? 'up' : 'down'">
                  {{ backtestResult.win_rate.toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">所有交易收益率的简单平均值。计算公式：(盈利交易收益 + 亏损交易收益) ÷ 总交易数。反映单笔交易的平均表现。</div>
                  </template>
                  <div class="metric-label">平均收益</div>
                </el-tooltip>
                <div class="metric-value" :class="backtestResult.avg_return >= 0 ? 'up' : 'down'">
                  {{ backtestResult.avg_return >= 0 ? '+' : '' }}{{ backtestResult.avg_return.toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">从历史最高点到最低点的最大跌幅，按复利计算。计算公式：(最高点净值 - 当前净值) ÷ 最高点净值 × 100%。反映策略的最大风险暴露。</div>
                  </template>
                  <div class="metric-label">最大回撤</div>
                </el-tooltip>
                <div class="metric-value down">{{ backtestResult.max_drawdown.toFixed(2) }}%</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 其他指标 -->
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">回测期间的累计收益，按复利计算。计算公式：期末净值 ÷ 期初净值 - 1。期初净值=1，每天收益=当日选中股票平均收益。</div>
                  </template>
                  <div class="metric-label">总收益</div>
                </el-tooltip>
                <div class="metric-value" :class="backtestResult.total_return >= 0 ? 'up' : 'down'">
                  {{ backtestResult.total_return >= 0 ? '+' : '' }}{{ backtestResult.total_return.toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">仅计算盈利交易的平均收益率。反映赚钱交易的平均盈利幅度。理想值应显著大于平均亏损的绝对值。</div>
                  </template>
                  <div class="metric-label">平均盈利</div>
                </el-tooltip>
                <div class="metric-value up">+{{ backtestResult.avg_win.toFixed(2) }}%</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">仅计算亏损交易的平均收益率（取负值）。反映亏钱交易的平均亏损幅度。策略能否盈利的关键：平均盈利 > 平均亏损 × 胜率补偿。</div>
                  </template>
                  <div class="metric-label">平均亏损</div>
                </el-tooltip>
                <div class="metric-value down">{{ backtestResult.avg_loss.toFixed(2) }}</div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never" class="metric-card">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div class="tooltip-detail">回测期间实际有交易的天数（不包含无信号的交易日）。总交易次数 ÷ 回测天数 = 日均交易笔数。</div>
                  </template>
                  <div class="metric-label">回测天数</div>
                </el-tooltip>
                <div class="metric-value">{{ backtestResult.backtest_days }}</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 信号类型统计 -->
          <el-card shadow="never" style="margin-top: 16px;">
            <template #header>
              <div class="card-header">
                <span>信号类型统计</span>
              </div>
            </template>
            <el-table :data="signalStatsList" stripe style="width: 100%">
              <el-table-column prop="signal_type" label="信号类型" width="150">
                <template #default="{ row }">
                  <el-tag :type="getSignalTypeTag(row.signal_type)" size="small">
                    {{ row.signal_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="交易次数" width="120" />
              <el-table-column prop="win_rate" label="胜率" width="120">
                <template #default="{ row }">
                  <span :class="['pct', row.win_rate >= 50 ? 'up' : 'down']">{{ row.win_rate.toFixed(2) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="avg_return" label="平均收益">
                <template #default="{ row }">
                  <span :class="['pct', row.avg_return >= 0 ? 'up' : 'down']">
                    {{ row.avg_return >= 0 ? '+' : '' }}{{ row.avg_return.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 卖出原因统计 -->
          <el-card shadow="never" style="margin-top: 16px;">
            <template #header>
              <div class="card-header">
                <span>卖出原因统计</span>
              </div>
            </template>
            <el-table :data="sellReasonStatsList" stripe style="width: 100%">
              <el-table-column prop="sell_reason" label="卖出原因" width="150">
                <template #default="{ row }">
                  <el-tag :type="getSellReasonTag(row.sell_reason)" size="small">
                    {{ row.sell_reason }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="交易次数" width="120" />
              <el-table-column prop="win_rate" label="胜率" width="120">
                <template #default="{ row }">
                  <span :class="['pct', row.win_rate >= 50 ? 'up' : 'down']">{{ row.win_rate.toFixed(2) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="avg_return" label="平均收益">
                <template #default="{ row }">
                  <span :class="['pct', row.avg_return >= 0 ? 'up' : 'down']">
                    {{ row.avg_return >= 0 ? '+' : '' }}{{ row.avg_return.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 盈利最多交易 -->
          <el-card shadow="never" style="margin-top: 16px;">
            <template #header>
              <div class="card-header">
                <span>盈利最多交易</span>
              </div>
            </template>
            <el-table :data="backtestResult.top_trades" stripe style="width: 100%">
              <el-table-column prop="code" label="代码" width="80" />
              <el-table-column prop="name" label="名称" width="100" />
              <el-table-column prop="limit_up_date" label="涨停日" width="105" />
              <el-table-column label="左侧买点" width="105">
                <template #default="{ row }">
                  <span v-if="row.left_buy_date" class="date-tag warning">{{ row.left_buy_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="右侧买点" width="105">
                <template #default="{ row }">
                  <span v-if="row.right_buy_date" class="date-tag success">{{ row.right_buy_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="buy_date" label="实际买入" width="105" />
              <el-table-column prop="sell_date" label="卖出日期" width="105" />
              <el-table-column label="止损卖点" width="105">
                <template #default="{ row }">
                  <span v-if="row.stop_loss_date" class="date-tag danger">{{ row.stop_loss_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="时间止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.time_stop_date" class="date-tag warning">{{ row.time_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="高位止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.high_stop_date" class="date-tag success">{{ row.high_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="5日线止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.ma5_stop_date" class="date-tag success">{{ row.ma5_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="buy_price" label="买入价" width="80">
                <template #default="{ row }">{{ row.buy_price.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="sell_price" label="卖出价" width="80">
                <template #default="{ row }">{{ row.sell_price.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="return_pct" label="收益率" width="100" sortable>
                <template #default="{ row }">
                  <span :class="['pct', row.return_pct >= 0 ? 'up' : 'down']">
                    {{ row.return_pct >= 0 ? '+' : '' }}{{ row.return_pct.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="signal_type" label="信号类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getSignalTypeTag(row.signal_type)" size="small">{{ row.signal_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sell_reason" label="卖出原因" width="110">
                <template #default="{ row }">
                  <el-tag :type="getSellReasonTag(row.sell_reason)" size="small">{{ row.sell_reason }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 亏损最多交易 -->
          <el-card shadow="never" style="margin-top: 16px;">
            <template #header>
              <div class="card-header">
                <span>亏损最多交易</span>
              </div>
            </template>
            <el-table :data="backtestResult.worst_trades" stripe style="width: 100%">
              <el-table-column prop="code" label="代码" width="80" />
              <el-table-column prop="name" label="名称" width="100" />
              <el-table-column prop="limit_up_date" label="涨停日" width="105" />
              <el-table-column label="左侧买点" width="105">
                <template #default="{ row }">
                  <span v-if="row.left_buy_date" class="date-tag warning">{{ row.left_buy_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="右侧买点" width="105">
                <template #default="{ row }">
                  <span v-if="row.right_buy_date" class="date-tag success">{{ row.right_buy_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="buy_date" label="实际买入" width="105" />
              <el-table-column prop="sell_date" label="卖出日期" width="105" />
              <el-table-column label="止损卖点" width="105">
                <template #default="{ row }">
                  <span v-if="row.stop_loss_date" class="date-tag danger">{{ row.stop_loss_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="时间止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.time_stop_date" class="date-tag warning">{{ row.time_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="高位止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.high_stop_date" class="date-tag success">{{ row.high_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column label="5日线止盈" width="105">
                <template #default="{ row }">
                  <span v-if="row.ma5_stop_date" class="date-tag success">{{ row.ma5_stop_date }}</span>
                  <span v-else class="empty-tag">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="buy_price" label="买入价" width="80">
                <template #default="{ row }">{{ row.buy_price.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="sell_price" label="卖出价" width="80">
                <template #default="{ row }">{{ row.sell_price.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="return_pct" label="收益率" width="100" sortable>
                <template #default="{ row }">
                  <span :class="['pct', row.return_pct >= 0 ? 'up' : 'down']">
                    {{ row.return_pct >= 0 ? '+' : '' }}{{ row.return_pct.toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="signal_type" label="信号类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getSignalTypeTag(row.signal_type)" size="small">{{ row.signal_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sell_reason" label="卖出原因" width="110">
                <template #default="{ row }">
                  <el-tag :type="getSellReasonTag(row.sell_reason)" size="small">{{ row.sell_reason }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  InfoFilled,
  Setting,
  Refresh,
  Search,
  List,
  DataLine,
  QuestionFilled,
  ArrowRight
} from '@element-plus/icons-vue'
import {
  screeningApi,
  type LimitUpPullbackItem,
  type LimitUpPullbackScanReq,
  type LimitUpPullbackBacktestReq,
  type LimitUpPullbackBacktestResp
} from '@/api/screening'
import { favoritesApi } from '@/api/favorites'

const router = useRouter()

const activeTab = ref<'scan' | 'backtest'>('scan')

const loading = ref(false)
const results = ref<LimitUpPullbackItem[]>([])
const tookMs = ref(0)
const hasSearched = ref(false)

// 回测相关状态
const backtestLoading = ref(false)
const backtestResult = ref<LimitUpPullbackBacktestResp | null>(null)

const defaultBacktestParams = {
  start_date: '',
  end_date: '',
  hold_days: 15,
  top_n: 10
}

const backtestParams = reactive<LimitUpPullbackBacktestReq>({ ...defaultBacktestParams })

// 信号类型统计列表
const signalStatsList = computed(() => {
  if (!backtestResult.value) return []
  return Object.entries(backtestResult.value.signal_stats).map(([signal_type, v]) => ({
    signal_type,
    count: v.count,
    win_rate: v.win_rate,
    avg_return: v.avg_return
  }))
})

// 卖出原因统计列表
const sellReasonStatsList = computed(() => {
  if (!backtestResult.value) return []
  return Object.entries(backtestResult.value.sell_reason_stats).map(([sell_reason, v]) => ({
    sell_reason,
    count: v.count,
    win_rate: v.win_rate,
    avg_return: v.avg_return
  }))
})

const defaultParams = {
  max_lookback_days: 15,
  min_pullback_days: 2,
  max_pullback_days: 8,
  shrink_volume_ratio: 0.5,
  min_shrink_days: 2,
  above_ma10: true,
  ground_volume_ratio: 0.35,
  lower_shadow_ratio: 0.015,
  breakout_ma5: true,
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

const goToAnalysis = (code: string) => {
  router.push({ path: '/analysis/single', query: { stock: code } })
}

const addToFavorites = async (row: LimitUpPullbackItem) => {
  try {
    await favoritesApi.add({
      stock_code: row.code,
      stock_name: row.name || '',
      market: 'A股'
    })
    ElMessage.success(`已添加 ${row.name}(${row.code}) 到自选`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '添加自选失败')
  }
}

const doBacktest = async () => {
  if (!backtestParams.start_date || !backtestParams.end_date) {
    ElMessage.warning('请选择回测开始和结束日期')
    return
  }

  backtestLoading.value = true
  backtestResult.value = null
  activeTab.value = 'backtest'

  try {
    // 合并扫描参数到回测请求
    const payload: LimitUpPullbackBacktestReq = {
      ...backtestParams,
      min_score: params.min_score,
      max_lookback_days: params.max_lookback_days,
      min_pullback_days: params.min_pullback_days,
      max_pullback_days: params.max_pullback_days,
      shrink_volume_ratio: params.shrink_volume_ratio,
      min_shrink_days: params.min_shrink_days,
      above_ma10: params.above_ma10,
      ground_volume_ratio: params.ground_volume_ratio,
      lower_shadow_ratio: params.lower_shadow_ratio,
      breakout_ma5: params.breakout_ma5,
      breakout_volume_ratio: params.breakout_volume_ratio
    }

    const resp = await screeningApi.backtestLimitUpPullback(payload, { timeout: 600000 })
    backtestResult.value = resp

    if (resp.total_trades > 0) {
      ElMessage.success(`回测完成，共 ${resp.total_trades} 笔交易，胜率 ${resp.win_rate.toFixed(2)}%`)
    } else {
      ElMessage.warning('回测完成，但未产生交易，请调整参数或日期范围')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '回测失败，请稍后重试')
  } finally {
    backtestLoading.value = false
  }
}

const getSignalTypeTag = (type: string) => {
  const map: Record<string, string> = {
    '右侧确认': 'success',
    '左侧潜伏': 'warning',
    '底部观察': 'info',
    '缩量回调中': 'primary',
    '观察': ''
  }
  return map[type] || ''
}

const getSellReasonTag = (reason: string) => {
  const map: Record<string, string> = {
    'ATR止损': 'danger',
    '10日止损': 'danger',
    '8日时间止盈': 'warning',
    '高位止盈': 'success',
    '5日线止盈': 'success',
    'ATR止盈': 'success',
    '到期卖出': 'info'
  }
  return map[reason] || ''
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

.param-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 2px;
}

.strategy-detail {
  .strategy-overview {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    margin-bottom: 0;
  }
}

.signal-types {
  .signal-desc {
    font-size: 11px;
    color: #909399;
    line-height: 1.4;
    margin-top: 4px;
  }

  .signal-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;

    .signal-buy-point,
    .signal-watch {
      min-width: 140px;
      text-align: center;
      padding: 12px 16px;
    }
  }

  .flow-arrow {
    font-size: 20px;
    color: #c0c4cc;
    flex-shrink: 0;
  }

  .signal-buy-point {
    padding: 8px 10px;
    border: 1px dashed #e6a23c;
    border-radius: 6px;
    background: #fdf6ec;

    .signal-desc {
      color: #b88230;
    }
  }

  .signal-sell-point {
    padding: 8px 10px;
    border: 1px dashed #f56c6c;
    border-radius: 6px;
    background: #fef0f0;

    .signal-desc {
      color: #c45656;
    }
  }

  .signal-watch {
    padding: 8px 10px;
    border: 1px solid #ebeef5;
    border-radius: 6px;
    background: #fafafa;
  }

  .signal-tip {
    margin-top: 12px;
    padding: 8px 12px;
    background: #ecf5ff;
    border-radius: 4px;
    font-size: 12px;
    color: #409eff;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.table-link {
  color: #409eff;
  text-decoration: none;
  cursor: pointer;

  &:hover {
    color: #66b1ff;
    text-decoration: underline;
  }
}

.date-range {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.date-item {
  white-space: nowrap;
}

.date-arrow {
  color: #909399;
  flex-shrink: 0;
}

.date-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  line-height: 1.4;

  &.warning {
    background: #fdf6ec;
    color: #e6a23c;
    border: 1px solid #f5dab1;
  }

  &.success {
    background: #f0f9eb;
    color: #67c23a;
    border: 1px solid #c2e7b0;
  }

  &.danger {
    background: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fbc4c4;
  }

  &.info {
    background: #f4f4f5;
    color: #909399;
    border: 1px solid #d3d4d6;
  }
}

.empty-tag {
  color: #c0c4cc;
  font-size: 12px;
}

.tooltip-detail {
  font-size: 13px;
  line-height: 1.5;
  max-width: 300px;
}

.help-icon {
  margin-left: 4px;
  font-size: 14px;
  color: #909399;
  cursor: help;
  vertical-align: middle;
  
  &:hover {
    color: #409eff;
  }
}

.metric-card {
  text-align: center;

  .metric-label {
    font-size: 13px;
    color: #909399;
    margin-bottom: 8px;
  }

  .metric-value {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    line-height: 1.2;

    &.up {
      color: #f56c6c;
    }

    &.down {
      color: #67c23a;
    }
  }
}
</style>
