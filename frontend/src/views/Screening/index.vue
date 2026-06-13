<template>
  <div class="stock-screening">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
            <el-icon><Search /></el-icon>
            选股
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

    <!-- 三买三卖策略模板 -->
    <el-card class="templates-panel" shadow="never" style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-icon><TrendCharts /></el-icon>
            <span>三买三卖策略</span>
            <el-tag type="success" size="small" effect="plain">基于均线与BIAS的技术信号</el-tag>
          </div>
        </div>
      </template>

      <!-- 买点 B1 / B2 / B3 -->
      <div class="signal-section-title buy-title">📈 买点信号</div>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'B1' }" @click="applySignalTemplate('B1')">
            <div class="signal-card-inner">
              <div class="strategy-icon buy b1">B1</div>
              <div class="strategy-info">
                <h3>左侧买点</h3>
                <p>BIAS60 超卖区间，赌反弹</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="warning">BIAS60:{{ signalParams.b1_bias_min }}%~{{ signalParams.b1_bias_max }}%</el-tag>
                  <el-tooltip :content="signalHelp.B1" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'B2' }" @click="applySignalTemplate('B2')">
            <div class="signal-card-inner">
              <div class="strategy-icon buy b2">B2</div>
              <div class="strategy-info">
                <h3>突破买点</h3>
                <p>放量突破MA55/MA60 + 阳线</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="primary">量比≥{{ signalParams.b2_volume_ratio }}</el-tag>
                  <el-tooltip :content="signalHelp.B2" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'B3' }" @click="applySignalTemplate('B3')">
            <div class="signal-card-inner">
              <div class="strategy-icon buy b3">B3</div>
              <div class="strategy-info">
                <h3>回踩买点</h3>
                <p>MA13支撑 + 回踩确认</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="success">BIAS60:{{ signalParams.b3_bias_min }}%~{{ signalParams.b3_bias_max }}%</el-tag>
                  <el-tooltip :content="signalHelp.B3" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 卖点 S1 / S2 / S3 -->
      <div class="signal-section-title sell-title">📉 卖点信号</div>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'S1' }" @click="applySignalTemplate('S1')">
            <div class="signal-card-inner">
              <div class="strategy-icon sell s1">S1</div>
              <div class="strategy-info">
                <h3>加速卖点</h3>
                <p>BIAS60 超买，减仓止盈</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="danger">BIAS60≥{{ signalParams.s1_bias_min }}%</el-tag>
                  <el-tooltip :content="signalHelp.S1" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'S2' }" @click="applySignalTemplate('S2')">
            <div class="signal-card-inner">
              <div class="strategy-icon sell s2">S2</div>
              <div class="strategy-info">
                <h3>跌破卖点</h3>
                <p>跌破短期均线(MA5/8/13)</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="warning">连破短期均线</el-tag>
                  <el-tooltip :content="signalHelp.S2" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="strategy-card signal-card" :class="{ active: activeSignalTemplate === 'S3' }" @click="applySignalTemplate('S3')">
            <div class="signal-card-inner">
              <div class="strategy-icon sell s3">S3</div>
              <div class="strategy-info">
                <h3>清仓卖点</h3>
                <p>跌破MA55/60 + 趋势向下</p>
                <div class="strategy-tags">
                  <el-tag size="small" type="info">中期下降趋势</el-tag>
                  <el-tooltip :content="signalHelp.S3" placement="top" effect="dark">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
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
            <span>选股条件</span>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    市场类型
                    <el-tooltip :content="indicatorHelp.market" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-select v-model="filters.market" placeholder="选择市场" disabled>
                  <el-option label="A股" value="A股" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    板块
                    <el-tooltip :content="indicatorHelp.board" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    市值范围
                    <el-tooltip :content="indicatorHelp.market_cap" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    涨跌幅 (%)
                    <el-tooltip :content="indicatorHelp.change_percent" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    换手率 (%)
                    <el-tooltip :content="indicatorHelp.turnover_rate" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    量比
                    <el-tooltip :content="indicatorHelp.volume_ratio" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    成交量
                    <el-tooltip :content="indicatorHelp.volume" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    MACD金叉
                    <el-tooltip :content="indicatorHelp.macd" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-select v-model="filters.macdGoldenFork" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    KDJ金叉
                    <el-tooltip :content="indicatorHelp.kdj" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-select v-model="filters.kdjGoldenFork" placeholder="选择">
                  <el-option label="全部" value="" />
                  <el-option label="是" value="Y" />
                  <el-option label="否" value="N" />
                </el-select>
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    站上20日均线
                    <el-tooltip :content="indicatorHelp.ma20" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    站上5日均线
                    <el-tooltip :content="indicatorHelp.ma5" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    市盈率 PE
                    <el-tooltip :content="indicatorHelp.pe" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    市净率 PB
                    <el-tooltip :content="indicatorHelp.pb" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    收盘价 (元)
                    <el-tooltip :content="indicatorHelp.price" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
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

        <!-- 三买三卖信号参数调整（选中信号模板时显示） -->
        <div v-if="currentSignalType" class="filter-section">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            <span>{{ currentSignalType }} 信号参数调整</span>
            <el-tag type="success" size="small" style="margin-left: 8px;">实时生效，点击筛选查看结果</el-tag>
          </div>

          <!-- B1 信号参数 -->
          <el-row v-if="currentSignalType === 'B1'" :gutter="24">
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    BIAS60 下限
                    <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.b1_bias_min"
                  :step="1"
                  :precision="0"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    BIAS60 上限
                    <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.b1_bias_max"
                  :step="1"
                  :precision="0"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- B2 信号参数 -->
          <el-row v-if="currentSignalType === 'B2'" :gutter="24">
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    放量倍数
                    <el-tooltip :content="indicatorHelp.volume_ratio" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.b2_volume_ratio"
                  :min="1.0"
                  :step="0.1"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    阳线涨幅
                    <el-tooltip :content="indicatorHelp.price_change" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.b2_price_change"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    突破参考均线
                    <el-tooltip :content="indicatorHelp.ma_cross" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-checkbox v-model="signalParams.b2_use_ma55">
                  <el-tooltip :content="indicatorHelp.ma55_signal" placement="top" effect="dark">
                    <span>MA55</span>
                  </el-tooltip>
                </el-checkbox>
                <el-checkbox v-model="signalParams.b2_use_ma60" style="margin-left: 12px;">
                  <el-tooltip :content="indicatorHelp.ma60_signal" placement="top" effect="dark">
                    <span>MA60</span>
                  </el-tooltip>
                </el-checkbox>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- B3 信号参数 -->
          <el-row v-if="currentSignalType === 'B3'" :gutter="24">
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    BIAS60 下限
                    <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number v-model="signalParams.b3_bias_min" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    BIAS60 上限
                    <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number v-model="signalParams.b3_bias_max" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    MA13与MA55比值
                    <el-tooltip :content="indicatorHelp.ma55_signal" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.b3_ma13_threshold"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- S1 信号参数 -->
          <el-row v-if="currentSignalType === 'S1'" :gutter="24">
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    BIAS60 下限
                    <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number v-model="signalParams.s1_bias_min" :step="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- S2 信号参数 -->
          <el-row v-if="currentSignalType === 'S2'" :gutter="24">
            <el-col :span="8">
              <el-form-item label="跌破参考均线">
                <el-checkbox v-model="signalParams.s2_use_ma5">
                  <el-tooltip :content="indicatorHelp.ma5" placement="top" effect="dark">
                    <span>MA5</span>
                  </el-tooltip>
                </el-checkbox>
                <el-checkbox v-model="signalParams.s2_use_ma8" style="margin-left: 8px;">
                  <el-tooltip :content="indicatorHelp.ma8" placement="top" effect="dark">
                    <span>MA8</span>
                  </el-tooltip>
                </el-checkbox>
                <el-checkbox v-model="signalParams.s2_use_ma13" style="margin-left: 8px;">
                  <el-tooltip :content="indicatorHelp.ma13" placement="top" effect="dark">
                    <span>MA13</span>
                  </el-tooltip>
                </el-checkbox>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- S3 信号参数 -->
          <el-row v-if="currentSignalType === 'S3'" :gutter="24">
            <el-col :span="8">
              <el-form-item label="跌破参考均线">
                <el-checkbox v-model="signalParams.s3_use_ma55">
                  <el-tooltip :content="indicatorHelp.ma55" placement="top" effect="dark">
                    <span>MA55</span>
                  </el-tooltip>
                </el-checkbox>
                <el-checkbox v-model="signalParams.s3_use_ma60" style="margin-left: 8px;">
                  <el-tooltip :content="indicatorHelp.ma60" placement="top" effect="dark">
                    <span>MA60</span>
                  </el-tooltip>
                </el-checkbox>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <template #label>
                  <span style="display: flex; align-items: center; gap: 4px;">
                    趋势判断天数
                    <el-tooltip :content="indicatorHelp.ma_trend" placement="top" effect="dark">
                      <el-icon class="help-icon"><QuestionFilled /></el-icon>
                    </el-tooltip>
                  </span>
                </template>
                <el-input-number
                  v-model="signalParams.s3_trend_days"
                  :min="3"
                  :max="20"
                  :step="1"
                  style="width: 100%"
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

        <!-- 信号指标列（仅信号筛选时显示） -->
        <el-table-column 
          v-if="currentSignalType" 
          prop="ma5" 
          width="90" 
          align="right"
        >
          <template #header>
            <el-tooltip :content="indicatorHelp.ma5" placement="top" effect="dark">
              <span style="display: inline-flex; align-items: center; gap: 4px;">
                MA5 <el-icon><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span v-if="row.ma5" class="price-text">{{ row.ma5?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          v-if="currentSignalType" 
          prop="ma13" 
          width="90" 
          align="right"
        >
          <template #header>
            <el-tooltip :content="indicatorHelp.ma13" placement="top" effect="dark">
              <span style="display: inline-flex; align-items: center; gap: 4px;">
                MA13 <el-icon><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span v-if="row.ma13" class="price-text">{{ row.ma13?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          v-if="currentSignalType" 
          prop="ma55" 
          width="90" 
          align="right"
        >
          <template #header>
            <el-tooltip :content="indicatorHelp.ma55" placement="top" effect="dark">
              <span style="display: inline-flex; align-items: center; gap: 4px;">
                MA55 <el-icon><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span v-if="row.ma55" class="price-text">{{ row.ma55?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          v-if="currentSignalType" 
          prop="ma60" 
          width="90" 
          align="right"
        >
          <template #header>
            <el-tooltip :content="indicatorHelp.ma60" placement="top" effect="dark">
              <span style="display: inline-flex; align-items: center; gap: 4px;">
                MA60 <el-icon><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span v-if="row.ma60" class="price-text">{{ row.ma60?.toFixed(2) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column 
          v-if="currentSignalType" 
          prop="bias_60" 
          width="100" 
          align="right"
          sortable
        >
          <template #header>
            <el-tooltip :content="indicatorHelp.bias60" placement="top" effect="dark">
              <span style="display: inline-flex; align-items: center; gap: 4px;">
                BIAS60 <el-icon><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          <template #default="{ row }">
            <span 
              v-if="row.bias_60 !== null && row.bias_60 !== undefined"
              :class="{
                'text-green-600': row.bias_60 <= -10,
                'text-red-600': row.bias_60 >= 25,
                'text-gray-700': row.bias_60 > -10 && row.bias_60 < 25
              }"
            >
              {{ row.bias_60 > 0 ? '+' : '' }}{{ row.bias_60?.toFixed(2) }}%
            </span>
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
import { Search, Refresh, TrendCharts, Download, Star, Connection, Warning, MagicStick, Wallet, Histogram, Lightning, DataAnalysis, Crop, Money, ShoppingCart, QuestionFilled } from '@element-plus/icons-vue'
import type { StockInfo } from '@/types/analysis'
import { screeningApi, type FieldConfigResponse } from '@/api/screening'
import { ApiClient } from '@/api/request'
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

// 三买三卖信号筛选
const activeSignalTemplate = ref<string>('')
const currentSignalType = ref<string>('')

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

// 三买三卖信号参数（可调）
const signalParams = reactive({
  // B1: 左侧买点 - BIAS60区间
  b1_bias_min: -40,
  b1_bias_max: -10,
  // B2: 突破买点 - 放量突破
  b2_volume_ratio: 1.2,
  b2_price_change: 0.03,
  b2_use_ma55: true,
  b2_use_ma60: true,
  // B3: 回踩买点
  b3_bias_min: -10,
  b3_bias_max: 10,
  b3_ma13_threshold: 0.95,
  b3_price_vs_ma60: 0.98,
  // S1: 加速卖点 - BIAS60上限
  s1_bias_min: 25,
  // S2: 跌破卖点 - 跌破短期均线
  s2_use_ma5: true,
  s2_use_ma8: true,
  s2_use_ma13: true,
  // S3: 清仓卖点 - 跌破长期均线+趋势向下
  s3_use_ma55: true,
  s3_use_ma60: true,
  s3_trend_days: 5,
})

// 技术指标 tooltip 解释（鼠标悬停显示详细信息）
const indicatorHelp = {
  market: '市场类型（Market）\n\n目前仅支持A股市场（沪深交易所上市的股票）。\nA股包含：主板、创业板（300xxx）、科创板（688xxx）、北交所（8/4开头）。\n\n后续可扩展至港股、美股等其它市场。',
  board: '板块（Board）\n\n• 主板：600xxx/000xxx/001xxx开头，市值较大，市场稳定\n• 创业板：300xxx开头，新兴成长型企业，涨跌幅±20%\n• 科创板：688xxx开头，科技创新企业，涨跌幅±20%\n• 北交所：8/4开头，中小企业为主，涨跌幅±30%\n\n不同板块的交易规则和风险特征不同。',
  market_cap: '市值范围（Market Capitalization）\n\n计算公式：市值 = 最新收盘价 × 总股本\n\n• 小盘股：< 100亿，波动大，弹性强\n• 中盘股：100亿 ~ 500亿，平衡型\n• 大盘股：> 500亿，稳定型，抗风险能力强\n\n市值大小会影响股价的流动性和波动性。',
  change_percent: '涨跌幅（Price Change %）\n\n计算公式：(当前价 - 昨收价) / 昨收价 × 100%\n\n• 正数：上涨，代表当日强势\n• 负数：下跌，代表当日弱势\n• ±3% 以内：正常波动\n• > 5%：大幅波动，需警惕\n\n筛选时可根据策略偏好设定范围：\n• 突破型：> 3%（放量上涨）\n• 低波动型：-3% ~ 3%',
  turnover_rate: '换手率（Turnover Rate）\n\n计算公式：(当日成交量 / 流通股本) × 100%\n\n换手率反映股票的活跃度和市场热度：\n• < 1%：冷清，缺乏关注\n• 1% ~ 3%：正常活跃\n• 3% ~ 5%：高度活跃，资金关注\n• > 5%：异常活跃，需警惕回调\n\n高换手率常出现在题材炒作和突破行情中。',
  volume_ratio: '量比（Volume Ratio）\n\n计算公式：当日成交量 / 过去N日平均成交量\n\n量比是衡量相对成交量的指标：\n• < 0.8：缩量，市场冷淡\n• 0.8 ~ 1.2：正常成交量\n• 1.2 ~ 2.0：温和放量，资金关注度上升\n• > 2.0：明显放量，资金活跃度高\n• > 3.0：巨量，极端活跃\n\n量比 > 1.2 + 股价上涨 = 突破概率较高（B2信号逻辑）。',
  volume: '成交量（Volume）\n\n成交量是当日成交的股票数量（股数或手数）。\n\n• 高成交量：资金活跃，市场关注度高\n• 中等成交量：正常交易状态\n• 低成交量：市场冷淡，缺乏资金关注\n\n成交量是判断股票活跃度的基础指标，常配合价格走势使用。\n价涨量增 = 上涨趋势可靠\n价跌量增 = 下跌趋势确认',
  macd: 'MACD金叉（Moving Average Convergence Divergence）\n\nMACD由两条线组成：DIF（差离值）和DEA（讯号线）。\n\n金叉：DIF 自下往上穿越 DEA，且两条线同时在0轴上方最佳。\n\n金叉是经典的买入信号，表示短期动能已超过中期动能。\n\n注意：MACD对震荡市行情信号噪音较多，需配合其他指标使用。',
  kdj: 'KDJ金叉（Stochastic Oscillator）\n\nKDJ是衡量股价在近期价格波动中所处位置的指标。\n\n金叉：K线 自下往上穿越 D线。\n\n金叉代表短期动能转强，是常用的买入信号。\n\n• KDJ < 20 且金叉：超卖区域买入，信号更可靠\n• KDJ > 80 且死叉：超买区域卖出，信号更可靠',
  ma20: '站上20日均线（MA20 Cross）\n\nMA20 = 最近20个交易日收盘价的算术平均\n\n站上20日均线：当前收盘价 > MA20\n\n意义：价格站在短期均线之上，短期趋势向好。\n• 跌破MA20且MA20下行：短期趋势转弱\n• 站稳MA20且MA20上行：短期强势确立',
  ma5: '站上5日均线（MA5 Cross）\n\nMA5 = 最近5个交易日收盘价的算术平均\n\n站上5日均线：当前收盘价 > MA5\n\n意义：价格在最近5个交易日平均价之上，代表极短期强势。\nMA5是最敏感的均线，常用于：\n• 短线止损参考（跌破MA5即离场）\n• 判断当日趋势强度',
  pe: '市盈率 PE（Price-to-Earnings Ratio）\n\n计算公式：PE = 股价 / 每股收益（EPS）\n\n意义：表示投资者为每1元盈利愿意支付的价格，反映市场对公司未来盈利的预期。\n\n参考值：\n• PE < 15：低估，价值投资首选\n• PE 在 15 ~ 40：正常区间\n• PE > 40：高估，需警惕泡沫\n• PE < 0：亏损，高风险\n\n低PE策略是经典的价值投资方法，但需结合行业特性和公司成长性综合判断。',
  pb: '市净率 PB（Price-to-Book Ratio）\n\n计算公式：PB = 股价 / 每股净资产\n\n意义：表示投资者为每1元公司净资产愿意支付的价格。\n\n参考值：\n• PB < 1：破净股，市场极度悲观（可能是机会也可能是价值陷阱）\n• PB 在 1 ~ 3：正常区间\n• PB > 5：高估，需结合行业判断\n\nPB < 1是寻找"烟蒂股"的常用指标，类似巴菲特早期的投资风格。',
  price: '收盘价（Close Price）\n\n当日交易结束时股票最后一笔成交的价格。\n\n意义：收盘价是技术分析中最重要的价格数据，反映了市场参与者对当日价格的最终共识。\n\n• 高股价股票（> 100元）通常流动性稍差，但可能是基本面优秀的公司\n• 低股价股票（< 5元）可能是问题股或小盘股，波动风险较大\n• 中等价格股票（10 ~ 50元）通常交易活跃，适合大多数策略',
  bias60: 'BIAS60（60日乖离率）\n定义与计算公式：\nBIAS60衡量当前收盘价与MA60之间的偏离程度。\n公式：BIAS60 = [(收盘价 - MA60) / MA60] × 100%\n\n意义：反映股价偏离中期均线的程度，常用于判断超买超卖。\n\n典型区间：\n• BIAS60 > 25%：超买，存在回调风险（S1信号区域）\n• BIAS60 在 [-10%, 10%]：正常波动，与均线贴合（B3信号区域）\n• BIAS60 在 [-40%, -10%]：超卖，可能出现反弹机会（B1信号区域）\n• BIAS60 < -40%：严重超卖，极端恐慌状态',
  ma_cross: '均线突破（Moving Average Breakout）\n定义：\n价格穿越某条均线称为"突破"。\n\n向上突破：\n• 前一日收盘价在均线下方\n• 当日收盘价在均线上方\n→ 意味着短期趋势反转向上（B2信号的突破条件）\n\n向下跌破：\n• 前一日收盘价在均线上方\n• 当日收盘价在均线下方\n→ 意味着短期趋势反转向下（S2/S3信号）\n\n常用突破均线：MA55、MA60（中期趋势突破）',
  volume_ratio_signal: '量比（Volume Ratio）\n定义与计算公式：\n量比是衡量相对成交量的指标，反映当日成交量与过去一段时间平均成交量的比值。\n公式：量比 = 当日成交量 / 过去N日平均成交量\n\n意义：衡量成交量的放大或缩小程度，判断市场热度和资金活跃程度。\n\n典型用法：\n• 量比 > 1.5：成交量放大，资金活跃，配合上涨更可靠（B2信号）\n• 量比 > 2.0：明显放量，突破信号更可靠\n• 量比 < 0.8：成交量萎缩，关注方向选择',
  ma5_signal: 'MA5（5日移动平均线）\n定义与计算公式：\nMA5是将股票最近5个交易日的收盘价进行算术平均得到的线。\n公式：MA5 = (C1 + C2 + C3 + C4 + C5) / 5\n其中C1到C5表示连续五个交易日的收盘价。\n\n意义：反映股票短期走势，是最敏感的均线之一。\n常用于：判断超短期趋势、短线支撑/压力位。\n• S2信号中：跌破MA5是短期走弱的第一信号',
  ma8_signal: 'MA8（8日移动平均线）\n定义与计算公式：\nMA8是将股票最近8个交易日的收盘价进行算术平均得到的线。\n公式：MA8 = (C1 + C2 + ... + C8) / 8\n\n意义：短期与中期趋势之间的过渡均线。\n常用于：捕捉小趋势变化、辅助判断买入/卖出时机。\n• S2信号中：跌破MA8强化短期走弱信号',
  ma13_signal: 'MA13（13日移动平均线）\n定义与计算公式：\nMA13是将股票最近13个交易日的收盘价进行算术平均得到的线。\n公式：MA13 = (C1 + C2 + ... + C13) / 13\n\n意义：短期均线的代表，是短线交易重要参考。\n常用于：判断短期趋势方向、作为短线止损/止盈参考。\n• S2信号中：跌破MA13且同时跌破MA5/MA8 = 短期趋势完全走弱',
  ma55_signal: 'MA55（55日移动平均线）\n定义与计算公式：\nMA55是将股票最近55个交易日的收盘价进行算术平均得到的线。\n公式：MA55 = (C1 + C2 + ... + C55) / 55\n\n意义：中短期趋势的分水岭，接近季度线。\n常用于：判断中期趋势方向、作为中长线的重要支撑/压力位。\n• B2信号中：价格突破MA55是中期趋势反转的重要信号\n• S3信号中：价格跌破MA55且MA60下行 = 中期趋势确认走弱',
  ma60_signal: 'MA60（60日移动平均线）\n定义与计算公式：\nMA60是将股票最近60个交易日的收盘价进行算术平均得到的线。\n公式：MA60 = (C1 + C2 + ... + C60) / 60\n\n意义：俗称"季线"，是判断中期趋势的核心均线。\n常用于：判断股票中期强弱、作为中长线操作的重要参考。\n价格在MA60上方表示中期强势，反之表示中期弱势。\n• B2信号中：价格同时突破MA55和MA60是最强的中期反转信号\n• S3信号中：MA60趋势向下 + 价格在MA60下方 = 强烈清仓信号',
  ma_trend: '均线趋势（Moving Average Trend）\n定义与计算公式：\n通过计算均线近期数日的斜率，判断均线本身的趋势方向。\n方法：取最近N日的均线值，用线性回归计算斜率。\n\n斜率 > 0：均线向上，趋势向好\n斜率 < 0：均线向下，趋势向弱\n\n意义：均线本身的趋势比单根价格K线更可靠。\n\n典型用法（S3信号）：\n• MA60斜率 < 0：中期均线持续下降\n• 同时价格在MA55/MA60下方\n→ 确认中期下降趋势，清仓信号',
  price_change_signal: '价格涨跌幅（Price Change）\n定义与计算公式：\n表示当日价格相对于开盘价的变化幅度。\n公式：涨跌幅 = (收盘价 - 开盘价) / 开盘价 × 100%\n\n意义：判断当日K线形态的强度。\n\n典型用法：\n• > 3%：中阳线，当日强势（B2信号的阳线条件）\n• > 5%：大阳线，强势突破信号\n• < -3%：中阴线，当日弱势',
}

// 信号卡片的 tooltip 解释
const signalHelp = {
  B1: 'B1 - 左侧买点\n条件：BIAS60 在 [-40%, -10%] 区间\n\n解读：\n价格已经大幅低于60日均线，进入超卖区域。\n这是左侧交易思路——"别人恐慌我贪婪"，赌股价反弹。\n\n风险：趋势可能继续下跌，需要严格控制仓位，建议1/3仓位。',
  B2: 'B2 - 突破买点\n条件：放量（量比≥1.2）+ 突破MA55/MA60 + 阳线（涨幅≥3%）\n\n解读：\n放量突破中期均线，且有阳线确认，是典型的趋势反转信号。\n资金入场意愿明显，技术形态突破，可以标准建仓（2/3仓位）。',
  B3: 'B3 - 回踩买点\n条件：MA13接近MA55 + BIAS60在[-10%, 10%] + 近期有过强势表现\n\n解读：\n股价回踩均线获得支撑，同时前期有过强势信号，蓄力后可能再次向上。\n这是确认后的加仓信号，可以加仓至满仓。',
  S1: 'S1 - 加速卖点\n条件：BIAS60 ≥ 25%\n\n解读：\n价格严重偏离60日均线，进入超买区间。\n"加速上涨"之后往往伴随回调，建议减仓止盈，保留1/3仓位即可。',
  S2: 'S2 - 跌破卖点\n条件：连续跌破MA5、MA8、MA13（短期均线全部失守）\n\n解读：\n短期趋势已经完全转向，均线支撑全部失效。\n这是明确的离场信号，应加大止盈力度，仅保留少量底仓。',
  S3: 'S3 - 清仓卖点\n条件：跌破MA55 + 跌破MA60 + MA60趋势向下\n\n解读：\n中期趋势已经确认向下，长期均线还在持续下降。\n这是最强烈的卖出信号——清仓离场，保护本金。\n不要抱有幻想，趋势的力量会让左侧交易者付出代价。',
}

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
    // 如果当前是信号筛选模式，调用专用的信号筛选 API
    if (currentSignalType.value) {
      console.log(`🔍 [信号筛选] 调用 ${currentSignalType.value} 信号筛选 API，参数:`, signalParams)
      
      const res = await ApiClient.post(
        '/api/three-buy-three-sell/screen/signal',
        { signal_type: currentSignalType.value, params: signalParams },
        { timeout: 120000 }
      )
      
      console.log(`🔍 [信号筛选] API原始响应:`, res)
      
      // ApiClient 返回响应体本身（response.data），结构为 { success, data, total, message }
      // data 字段就是股票数组
      let items: any[] = []
      if (Array.isArray(res)) {
        items = res
      } else if (res && typeof res === 'object') {
        if (Array.isArray((res as any).data)) {
          items = (res as any).data
        } else if (Array.isArray((res as any).items)) {
          items = (res as any).items
        } else if ((res as any).data && Array.isArray((res as any).data?.data)) {
          items = (res as any).data.data
        }
      }
      
      console.log(`🔍 [信号筛选] 返回 ${items.length} 只股票`)
      if (items.length > 0) {
        console.log(`🔍 [信号筛选] 首条数据示例:`, items[0])
      }
      
      screeningResults.value = items.map((it: any) => ({
        symbol: it.code || it.symbol || '',
        code: it.code || it.symbol || '',
        name: it.name || it.code || '',
        close: it.close,
        ma5: it.ma_5,
        ma13: it.ma_13,
        ma55: it.ma_55,
        ma60: it.ma_60,
        bias_60: it.bias_60,
        pct_chg: it.pct_chg || null,
        total_mv: it.total_mv || null,
      }))
      
      ElMessage.success(`筛选完成，找到 ${screeningResults.value.length} 只 ${currentSignalType.value} 信号股票`)
      return
    }

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
  // 清除信号筛选状态
  activeSignalTemplate.value = ''
  currentSignalType.value = ''

  Object.assign(filters, {
    market: 'A股',
    ...template.conditions
  })

  ElMessage.info(`已应用【${template.name}】策略模板，请点击"开始筛选"查看结果`)
}

const applySignalTemplate = (signalType: string) => {
  activeSignalTemplate.value = signalType
  currentSignalType.value = signalType
  // 清除通用模板状态
  activeTemplate.value = ''

  ElMessage.info(`已应用【${signalType}】信号模板，请点击"开始筛选"查看结果（可调整上方参数）`)
}

const resetFilters = () => {
  activeTemplate.value = ''
  activeSignalTemplate.value = ''
  currentSignalType.value = ''
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

  /* 通用卡片头部样式 */
  .templates-panel {
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(
        135deg,
        var(--el-color-primary-light-9) 0%,
        var(--el-color-primary-light-8) 100%
      );
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

    /* 信号区域标题 */
    .signal-section-title {
      font-size: 13px;
      font-weight: 600;

      &.buy-title {
        margin-bottom: 12px;
        color: var(--el-color-success);
      }
      &.sell-title {
        margin: 16px 0 12px 0;
        color: var(--el-color-danger);
      }
    }

    /* 信号卡片内部布局 */
    .signal-card-inner {
      display: flex;
      align-items: start;
      gap: 12px;
    }

    /* 通用策略卡片 */
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
        background: linear-gradient(
          135deg,
          var(--el-color-primary-light-9) 0%,
          var(--el-color-primary-light-8) 100%
        );
      }

      /* 策略图标 */
      .strategy-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        color: var(--el-color-white);
        flex-shrink: 0;

        /* 第一行：常规策略模板 */
        &.breakout {
          background: linear-gradient(
            135deg,
            var(--el-color-warning) 0%,
            var(--el-color-warning-dark-2) 100%
          );
        }
        &.value {
          background: linear-gradient(
            135deg,
            var(--el-color-success) 0%,
            var(--el-color-success-dark-2) 100%
          );
        }
        &.growth {
          background: linear-gradient(
            135deg,
            var(--el-color-primary) 0%,
            var(--el-color-primary-dark-2) 100%
          );
        }
        &.momentum {
          background: linear-gradient(
            135deg,
            var(--el-color-danger) 0%,
            var(--el-color-danger-dark-2) 100%
          );
        }
        &.lowvolatility {
          background: linear-gradient(
            135deg,
            var(--el-color-info) 0%,
            var(--el-color-info-dark-2) 100%
          );
        }
        &.smallcap {
          background: linear-gradient(
            135deg,
            var(--el-color-warning) 0%,
            var(--el-color-warning-dark-2) 100%
          );
        }
        &.bluechip {
          background: linear-gradient(
            135deg,
            var(--el-color-primary) 0%,
            var(--el-color-primary-dark-2) 100%
          );
        }
        &.superlowpb {
          background: linear-gradient(
            135deg,
            var(--el-color-success) 0%,
            var(--el-color-success-dark-2) 100%
          );
        }
        &.lowprice {
          background: linear-gradient(
            135deg,
            var(--el-text-color-regular) 0%,
            var(--el-text-color-secondary) 100%
          );
        }

        /* 第二行：三买三卖信号 */
        &.buy, &.sell {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          font-size: 22px;
          font-weight: 700;
        }

        &.b1, &.b2, &.b3 {
          background: linear-gradient(
            135deg,
            var(--el-color-success) 0%,
            var(--el-color-success-dark-2) 100%
          );
        }

        &.s1, &.s2, &.s3 {
          background: linear-gradient(
            135deg,
            var(--el-color-danger) 0%,
            var(--el-color-danger-dark-2) 100%
          );
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

      /* 信号卡片的 buy/sell 激活样式 */
      &.signal-card {
        align-items: start;

        &:has(.strategy-icon.buy) {
          border-color: transparent;
        }
        &:has(.strategy-icon.buy):hover {
          border-color: var(--el-color-success);
        }
        &:has(.strategy-icon.buy).active {
          background: linear-gradient(
            135deg,
            var(--el-color-success-light-9) 0%,
            var(--el-color-success-light-8) 100%
          );
          border-color: var(--el-color-success);
        }

        &:has(.strategy-icon.sell) {
          border-color: transparent;
        }
        &:has(.strategy-icon.sell):hover {
          border-color: var(--el-color-danger);
        }
        &:has(.strategy-icon.sell).active {
          background: linear-gradient(
            135deg,
            var(--el-color-danger-light-9) 0%,
            var(--el-color-danger-light-8) 100%
          );
          border-color: var(--el-color-danger);
        }
      }
    }

    /* 帮助图标样式 */
    .help-icon {
      color: var(--el-text-color-placeholder);
      font-size: 14px;
      margin-left: 6px;
      cursor: help;
      vertical-align: middle;
    }
  }

  /* 筛选条件面板 */
  .filter-panel {
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(
        135deg,
        var(--el-color-primary-light-9) 0%,
        var(--el-color-primary-light-8) 100%
      );
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

      .help-icon {
        font-size: 14px;
        color: var(--el-color-info);
        cursor: help;
        margin-left: 2px;
        vertical-align: middle;

        &:hover {
          color: var(--el-color-primary);
        }
      }

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

  /* 结果面板 */
  .results-panel {
    border-radius: 12px;
    overflow: hidden;

    :deep(.el-card__header) {
      background: linear-gradient(
        135deg,
        var(--el-color-success-light-9) 0%,
        var(--el-color-success-light-8) 100%
      );
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
    color: var(--el-color-danger);
    font-weight: 600;
  }

  .text-green {
    color: var(--el-color-success);
    font-weight: 600;
  }

  .price-text {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

/* ============================================
   深色 / 夜间模式样式覆盖（灰阶体系）
   ============================================ */
html.dark {
  .stock-screening {
    /* 卡片头部：深色灰阶 */
    .templates-panel,
    .filter-panel,
    .results-panel {
      :deep(.el-card__header) {
        background: linear-gradient(
          135deg,
          var(--el-bg-color-overlay) 0%,
          var(--el-fill-color-darker) 100%
        );
        border-bottom-color: var(--el-border-color-darker);
      }
    }

    /* 卡片主体背景 */
    .templates-panel :deep(.el-card__body) {
      background: var(--el-bg-color);
    }

    /* 信号区域标题颜色：深色下保持可读 */
    .templates-panel {
      .signal-section-title {
        &.buy-title {
          color: var(--el-color-success-light-5);
        }
        &.sell-title {
          color: var(--el-color-danger-light-5);
        }
      }
    }

    /* 策略卡片：深色下统一灰阶 */
    .strategy-card {
      background: var(--el-fill-color-darker);
      border-color: transparent;

      &:hover {
        background: var(--el-fill-color-dark);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
      }

      &.active {
        background: linear-gradient(
          135deg,
          var(--el-fill-color-dark) 0%,
          var(--el-fill-color) 100%
        );
        border-color: var(--el-text-color-secondary);
      }

      /* 策略图标：深色下改为灰阶三色 */
      .strategy-icon {
        color: var(--el-color-white);
        background: linear-gradient(
          135deg,
          var(--el-text-color-secondary) 0%,
          var(--el-text-color-placeholder) 100%
        ) !important;
      }

      .strategy-info {
        h3 {
          color: var(--el-text-color-primary);
        }
        p {
          color: var(--el-text-color-regular);
        }
      }

      /* 信号卡片 hover/active 深色下保持灰阶语义 */
      &.signal-card {
        &:has(.strategy-icon.buy):hover {
          border-color: var(--el-text-color-secondary);
        }
        &:has(.strategy-icon.buy).active {
          background: linear-gradient(
            135deg,
            var(--el-fill-color-dark) 0%,
            var(--el-fill-color) 100%
          );
          border-color: var(--el-text-color-secondary);
        }
        &:has(.strategy-icon.sell):hover {
          border-color: var(--el-text-color-secondary);
        }
        &:has(.strategy-icon.sell).active {
          background: linear-gradient(
            135deg,
            var(--el-fill-color-dark) 0%,
            var(--el-fill-color) 100%
          );
          border-color: var(--el-text-color-secondary);
        }
      }
    }

    /* 筛选条件分区：深色下改为更深灰阶 */
    .filter-panel {
      .filter-form {
        .filter-section {
          background: var(--el-fill-color-darker);

          &:hover {
            background: var(--el-fill-color-dark);
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
          }

          .section-title {
            border-bottom-color: var(--el-border-color-darker);
            color: var(--el-text-color-primary);

            .el-icon {
              color: var(--el-text-color-regular);
            }
          }
        }

        .help-icon {
          color: var(--el-text-color-placeholder);
          &:hover {
            color: var(--el-text-color-primary);
          }
        }
      }
    }

    /* 结果面板 */
    .results-panel {
      :deep(.el-table) {
        th {
          background-color: var(--el-fill-color-darker) !important;
          color: var(--el-text-color-primary);
        }

        .el-table__row:hover {
          background-color: var(--el-fill-color-dark);
        }
      }
    }

    /* 页面标题 */
    .page-header {
      border-bottom-color: var(--el-border-color-darker);

      .page-title {
        .el-icon {
          color: var(--el-text-color-regular);
        }
      }

      .page-description {
        color: var(--el-text-color-regular);
      }
    }

    .price-text {
      color: var(--el-text-color-primary);
    }
  }
}
</style>
