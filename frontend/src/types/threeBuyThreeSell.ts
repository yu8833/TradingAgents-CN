// 三买三卖交易系统类型定义

export interface TradingPoolEntry {
  stock_code: string
  stock_name: string
  pool_type: 'buy_candidate' | 'holding' | 'watching'
  entry_date: string
  entry_price?: number
  entry_signal: string
  quantity: number
  target_position: string
  status: string
  notes: string
  created_at: string
}

export interface Position {
  stock_code: string
  stock_name: string
  quantity: number
  avg_cost: number
  current_price: number
  unrealized_pnl: number
  position_ratio: string
  entry_date: string
  signals_triggered: string[]
  status: string
  created_at: string
}

export interface SignalHistory {
  stock_code: string
  signal_type: string
  signal_name: string
  trigger_date: string
  trigger_price: number
  trigger_conditions: Record<string, any>
  action_taken: string
  notification_sent: boolean
  is_active: boolean
  created_at: string
}

export interface SignalDetectionResult {
  stock_code: string
  stock_name: string
  current_price: number
  indicators: Record<string, any>
  signals: string[]
  recommendations: string[]
  position_advice: 'hold' | 'add' | 'reduce' | 'exit'
}

export interface SignalAlert {
  stock_code: string
  stock_name: string
  new_signals: string[]
  signal_strength: 'mild' | 'strong' | 'critical'
  message: string
  action: string
  timestamp: string
}

export interface PoolStatistics {
  total_stocks: number
  buy_candidate_count: number
  holding_count: number
  watching_count: number
  active_signals: number
}