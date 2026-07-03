import { ApiClient } from './request'

export interface ScreeningOrderBy { field: string; direction: 'asc' | 'desc' }
export interface ScreeningRunReq {
  market?: 'CN'
  date?: string | null
  adj?: 'qfq' | 'hfq' | 'none'
  conditions: any
  order_by?: ScreeningOrderBy[]
  limit?: number
  offset?: number
}

export interface ScreeningRunItem {
  code: string
  close?: number
  pct_chg?: number
  amount?: number
  ma20?: number
  rsi14?: number
  kdj_k?: number
  kdj_d?: number
  kdj_j?: number
  dif?: number
  dea?: number
  macd_hist?: number
}

export interface ScreeningRunResp { total: number; items: ScreeningRunItem[] }

// 筛选字段配置
export interface FieldInfo {
  name: string
  display_name: string
  field_type: string
  data_type: string
  description: string
  supported_operators: string[]
}

export interface FieldConfigResponse {
  fields: Record<string, FieldInfo>
  categories: Record<string, string[]>
}

// 行业列表响应
export interface IndustryOption {
  value: string
  label: string
  count: number
}

export interface IndustriesResponse {
  industries: IndustryOption[]
  total: number
}

export interface LimitUpPullbackScanReq {
  max_lookback_days?: number
  min_pullback_days?: number
  max_pullback_days?: number
  shrink_volume_ratio?: number
  min_shrink_days?: number
  above_ma10?: boolean
  ground_volume_ratio?: number
  lower_shadow_ratio?: number
  breakout_ma5?: boolean
  breakout_volume_ratio?: number
  min_score?: number
  limit?: number
}

export interface LimitUpPullbackItem {
  code: string
  name: string
  close: number
  pct_chg: number
  limit_up_date: string
  days_since_limit_up: number
  limit_up_close: number
  pullback_depth: number
  volume_shrink_ratio: number
  ground_volume_ratio: number
  lower_shadow_pct: number
  signal_type: string
  score: number
  score_details: string[]
  upside_space: number
  ma5?: number
  ma10?: number
  ma20?: number
  small_body_ratio: number
  ground_day_offset: number
  industry: string
  shadow_to_body_ratio?: number
  space_position_ok?: boolean
  is_20day_ground?: boolean
  fake_breakout?: boolean
  days_since_ground_day?: number
  rebound_from_ground?: number
  // 各阶段日期
  pullback_start_date?: string
  pullback_end_date?: string
  bottom_watch_start_date?: string
  left_buy_date?: string
  right_buy_date?: string
  ground_day_date?: string
}

export interface LimitUpPullbackScanResp {
  total: number
  items: LimitUpPullbackItem[]
  took_ms?: number
  scanned_count?: number
  params?: Record<string, any>
}

export interface LimitUpPullbackBacktestReq {
  start_date?: string
  end_date?: string
  hold_days?: number
  top_n?: number
  min_score?: number
  max_lookback_days?: number
  min_pullback_days?: number
  max_pullback_days?: number
  shrink_volume_ratio?: number
  min_shrink_days?: number
  above_ma10?: boolean
  ground_volume_ratio?: number
  lower_shadow_ratio?: number
  breakout_ma5?: boolean
  breakout_volume_ratio?: number
}

export interface BacktestTrade {
  code: string
  name: string
  buy_date: string
  sell_date: string
  buy_price: number
  sell_price: number
  return_pct: number
  score: number
  signal_type: string
  sell_reason: string
  // 各阶段日期
  limit_up_date?: string
  pullback_start_date?: string
  pullback_end_date?: string
  bottom_watch_start_date?: string
  left_buy_date?: string
  right_buy_date?: string
  ground_day_date?: string
  // 卖点日期
  stop_loss_date?: string
  time_stop_date?: string
  high_stop_date?: string
  ma5_stop_date?: string
}

export interface LimitUpPullbackBacktestResp {
  total_trades: number
  win_rate: number
  avg_return: number
  avg_win: number
  avg_loss: number
  max_drawdown: number
  total_return: number
  backtest_days: number
  signal_stats: Record<string, { count: number; win_rate: number; avg_return: number }>
  sell_reason_stats: Record<string, { count: number; win_rate: number; avg_return: number }>
  daily_results: Array<{
    date: string
    selected_count: number
    valid_count: number
    avg_return: number
    stocks: BacktestTrade[]
  }>
  top_trades: BacktestTrade[]
  worst_trades: BacktestTrade[]
  params?: Record<string, any>
  took_ms?: number
}

export const screeningApi = {
  run: (payload: ScreeningRunReq, options?: { timeout?: number }) =>
    ApiClient.post<ScreeningRunResp>('/api/screening/run', payload, { timeout: options?.timeout ?? 120000 }),
  getFields: () => ApiClient.get<FieldConfigResponse>('/api/screening/fields'),
  getIndustries: () => ApiClient.get<IndustriesResponse>('/api/screening/industries'),
  scanLimitUpPullback: (payload: LimitUpPullbackScanReq, options?: { timeout?: number }) =>
    ApiClient.post<LimitUpPullbackScanResp>('/api/screening/limit-up-pullback/scan', payload, { timeout: options?.timeout ?? 180000 }),
  backtestLimitUpPullback: (payload: LimitUpPullbackBacktestReq, options?: { timeout?: number }) =>
    ApiClient.post<LimitUpPullbackBacktestResp>('/api/screening/limit-up-pullback/backtest', payload, { timeout: options?.timeout ?? 300000 })
}

