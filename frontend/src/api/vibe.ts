import { ApiClient } from './request'

// ---------------------------------------------------------------------------
// 类型定义
// ---------------------------------------------------------------------------

export interface IndexQuote {
  name: string
  price: number
  change_pct: number
  change_amt: number
}

export interface GlobalIndex {
  key: string
  name: string
  region: string
  price: number | null
  change_pct: number | null
}

export interface MarketSentiment {
  up: number
  down: number
  flat: number
  zt: number
  zt_real: number
  dt: number
  dt_real: number
  active: string
  breadth: string
  speculation: string
  date: string
}

export interface SectorFlow {
  name: string
  pct: number
  net: number
  inflow: number
  outflow: number
  firms: number
}

export interface MarketOverview {
  sentiment: MarketSentiment
  sectors: SectorFlow[]
  updated: string
}

export interface LianbanStock {
  code: string
  name: string
  boards: number
  price: number
  pct: number
  amount: number | null
  float_cap: number | null
  industry: string
}

export interface ShortTermEmotion {
  date: string
  zt_count: number
  dt_count: number
  zb_count: number
  max_boards: number
  lianban_count: number
  ladder: { boards: number; count: number; plus: boolean }[]
  lianban_stocks: LianbanStock[]
  seal_rate: number | null
  break_rate: number | null
  promotion_rate: number | null
  yzt_count: number
}

export interface TurnoverStock {
  code: string
  name: string
  price: number | null
  pct: number | null
  amount: number
  mcap: number
  industry: string
}

export interface TurnoverTop {
  stocks: TurnoverStock[]
  updated: string
}

export interface StockQuote {
  code: string
  name: string
  price: number | null
  change_pct: number | null
  change_amt: number | null
  pe_ttm: number | null
  pb: number | null
  mcap_yi: number | null
  float_mcap_yi: number | null
  amount_wan: number | null
  turnover_pct: number | null
}

export interface RadarItem {
  title: string
  url: string
  time: string
  source: string
  summary?: string
  zh?: string
  ts?: number
}

export interface Industry {
  key: string
  name: string
  accent: string
  total: number
  items: RadarItem[]
}

export interface RadarData {
  generated_at: string | null
  recent_days: number
  industries: Industry[]
  stats: {
    industries: number
    total_sources: number
    failed_sources?: number
  }
}

export interface SectorNode {
  key: string
  label: string
  tagline: string
  hot: boolean
  verified: boolean
  nodes: string[]
}

export interface SectorsData {
  sectors: SectorNode[]
}

export interface Note {
  id: string
  kind: string
  title: string
  content: string
  ts: number
}

export interface Announcement {
  date: string
  title: string
  type: string
  url: string
}

export interface NewsItem {
  新闻标题: string
  新闻链接: string
  发布时间: string
  新闻来源: string
}

// ---------------------------------------------------------------------------
// 本地存储（研究记录）
// ---------------------------------------------------------------------------

const NOTES_KEY = 'vibe_research_notes'
const MAX_NOTES = 200

const WATCHLIST_KEY = 'vibe_watchlist'
const MAX_WATCHLIST = 20

// ---------------------------------------------------------------------------
// API 接口
// ---------------------------------------------------------------------------

export const vibeApi = {
  // 复盘模块
  async getIndices() {
    return ApiClient.get<IndexQuote[]>('/api/vibe/indices')
  },

  async getGlobalIndices() {
    return ApiClient.get<GlobalIndex[]>('/api/vibe/global-indices')
  },

  async getMarketOverview() {
    return ApiClient.get<MarketOverview>('/api/vibe/market/overview')
  },

  async getEmotion() {
    return ApiClient.get<ShortTermEmotion>('/api/vibe/market/emotion')
  },

  async getTurnoverTop() {
    return ApiClient.get<TurnoverTop>('/api/vibe/market/turnover-top')
  },

  // 资讯模块
  async getRadar() {
    return ApiClient.get<RadarData>('/api/vibe/radar')
  },

  async refreshRadar() {
    return ApiClient.post<RadarData>('/api/vibe/radar/refresh')
  },

  async getAnnouncements(code: string, limit = 15) {
    return ApiClient.get<Announcement[]>(`/api/vibe/announcements?code=${code}&limit=${limit}`)
  },

  async getNews(code: string, limit = 20) {
    return ApiClient.get<NewsItem[]>(`/api/vibe/news?code=${code}&limit=${limit}`)
  },

  // 板块模块
  async getSectors() {
    return ApiClient.get<SectorsData>('/api/vibe/sectors')
  },

  // 批量行情
  async getQuotes(codes: string[]) {
    if (codes.length === 0) return { success: true, data: [] as StockQuote[], message: '' }
    return ApiClient.get<StockQuote[]>(`/api/vibe/quotes?codes=${codes.join(',')}`)
  },

  // AI 对话（流式 NDJSON）
  async chatStream(
    messages: { role: string; content: string }[],
    context: string,
    onDelta: (text: string) => void,
    onError?: (msg: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem('token') || ''
    const resp = await fetch('/api/vibe/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ messages, context }),
      signal,
    })

    if (!resp.ok) {
      throw new Error(`请求失败: ${resp.status}`)
    }

    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue
        try {
          const ev = JSON.parse(trimmed)
          if (ev.type === 'delta') onDelta(ev.text)
          else if (ev.type === 'error' && onError) onError(ev.message)
        } catch {
          // ignore parse errors
        }
      }
    }
  },

  // 研究记录（localStorage）
  loadNotes(): Note[] {
    try {
      const data = localStorage.getItem(NOTES_KEY)
      return data ? JSON.parse(data) : []
    } catch {
      return []
    }
  },

  saveNote(kind: string, title: string, content: string): Note[] {
    const notes = this.loadNotes()
    const newNote: Note = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      kind,
      title,
      content,
      ts: Date.now(),
    }
    const next = [newNote, ...notes].slice(0, MAX_NOTES)
    localStorage.setItem(NOTES_KEY, JSON.stringify(next))
    return next
  },

  deleteNote(id: string): Note[] {
    const notes = this.loadNotes().filter(n => n.id !== id)
    localStorage.setItem(NOTES_KEY, JSON.stringify(notes))
    return notes
  },

  clearNotes(): Note[] {
    localStorage.removeItem(NOTES_KEY)
    return []
  },

  // 关注股票（localStorage）
  loadWatchlist(): string[] {
    try {
      const data = localStorage.getItem(WATCHLIST_KEY)
      return data ? JSON.parse(data) : []
    } catch {
      return []
    }
  },

  addWatchlist(code: string): string[] {
    const list = this.loadWatchlist()
    const c = code.trim()
    if (!c || list.includes(c)) return list
    const next = [c, ...list].slice(0, MAX_WATCHLIST)
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next))
    return next
  },

  removeWatchlist(code: string): string[] {
    const list = this.loadWatchlist().filter(c => c !== code)
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list))
    return list
  },
}
