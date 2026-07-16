import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { usePageMeta } from '../hooks/usePageMeta'

function Logo({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="text-msu-green">
      <polyline points="2,14 5,14 7,6 9,20 11,11 13,9 15,15 17,14 22,14"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function useDebounced(value, ms = 200) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function MonitorButton({ item, state, onMonitor }) {
  const label = state === 'loading' ? 'adding' : state === 'done' ? 'tracking →'
    : state === 'error' ? 'retry' : 'monitor'
  return (
    <button
      onClick={(e) => { e.preventDefault(); onMonitor(item) }}
      disabled={state === 'loading'}
      className={`shrink-0 font-mono text-xs px-2 py-1 rounded-sm border transition-colors
        ${state === 'done'
          ? 'border-msu-green/40 text-msu-green'
          : state === 'error'
          ? 'border-status-down/40 text-status-down'
          : 'border-transparent text-gray-400 group-hover:border-border group-hover:text-gray-700 hover:!border-msu-green hover:!text-msu-green'}`}
    >
      {label}
    </button>
  )
}

function Row({ item, state, onMonitor }) {
  return (
    <div className="group flex items-baseline gap-4 px-3 py-2.5 -mx-3 rounded-sm hover:bg-gray-50/80 transition-colors">
      <a
        href={item.url}
        target="_blank"
        rel="noreferrer"
        className="shrink-0 w-44 sm:w-52 text-sm font-medium text-gray-900 hover:text-msu-green transition-colors truncate"
        title={item.name}
      >
        {item.name}
      </a>
      <p className="flex-1 min-w-0 text-sm text-gray-500 truncate hidden sm:block" title={item.description}>
        {item.description || '—'}
      </p>
      <span className="shrink-0 font-mono text-[11px] text-gray-400 w-16 text-right">
        {item.auth === 'None' ? 'open' : 'key'}
      </span>
      <span className="shrink-0 font-mono text-[11px] text-gray-300 w-8 text-right hidden md:inline">
        {item.https ? 'tls' : ''}
      </span>
      <MonitorButton item={item} state={state} onMonitor={onMonitor} />
    </div>
  )
}

export default function Explore() {
  usePageMeta(
    'LightAPI — Discover and monitor every free API',
    'Search 1,500+ free public APIs by category, then monitor any of them live — uptime, latency, and ML-powered anomaly detection — in one click.'
  )
  const navigate = useNavigate()
  const searchRef = useRef(null)
  const [categories, setCategories] = useState([])
  const [totalApis, setTotalApis] = useState(null)
  const [activeCat, setActiveCat] = useState(null)
  const [authFilter, setAuthFilter] = useState(null)
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounced(searchInput, 200)

  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [monitorState, setMonitorState] = useState({})

  // `/` focuses search — a small pro touch.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === '/' && document.activeElement !== searchRef.current) {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    api.getDirectoryCategories()
      .then((d) => { setCategories(d.categories); setTotalApis(d.total) })
      .catch(() => setOffline(true))
  }, [])

  useEffect(() => {
    setLoading(true)
    api.getDirectory({ category: activeCat, search, auth: authFilter, limit: 80 })
      .then((d) => { setResults(d.results); setTotal(d.total); setOffline(false) })
      .catch(() => setOffline(true))
      .finally(() => setLoading(false))
  }, [activeCat, search, authFilter])

  const onMonitor = useCallback(async (item) => {
    setMonitorState((s) => ({ ...s, [item.id]: 'loading' }))
    try {
      const ep = await api.createEndpoint({ url: item.url, name: item.name })
      setMonitorState((s) => ({ ...s, [item.id]: 'done' }))
      setTimeout(() => navigate(`/dashboard/${ep.id}`), 450)
    } catch {
      setMonitorState((s) => ({ ...s, [item.id]: 'error' }))
    }
  }, [navigate])

  const heading = useMemo(() => {
    if (search) return `“${search}”`
    if (activeCat) return activeCat
    return 'All APIs'
  }, [search, activeCat])

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <Logo size={18} />
            <span className="text-sm font-bold tracking-tight">LightAPI</span>
            <span className="hidden sm:inline text-xs text-gray-400 font-mono ml-1">/ directory</span>
          </Link>
          <Link to="/dashboard" className="text-xs font-mono text-gray-500 hover:text-gray-900 transition-colors">
            dashboard →
          </Link>
        </div>
      </header>

      {/* Masthead */}
      <div className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-10">
          <h1 className="text-2xl sm:text-[28px] font-semibold tracking-tight leading-tight max-w-2xl">
            Every free API on the internet, in one place —
            <span className="text-gray-400"> and monitorable in a click.</span>
          </h1>
          <div className="mt-4 flex items-center gap-4 font-mono text-xs text-gray-400">
            <span><span className="text-gray-900">{totalApis?.toLocaleString() ?? '—'}</span> apis</span>
            <span className="text-gray-200">·</span>
            <span><span className="text-gray-900">{categories.length || '—'}</span> categories</span>
            <span className="text-gray-200">·</span>
            <span>updated daily</span>
          </div>

          {/* Search */}
          <div className="mt-6 relative max-w-xl">
            <input
              ref={searchRef}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by name or description…"
              className="w-full pl-3 pr-12 py-2.5 text-sm border border-border rounded-sm bg-white
                focus:outline-none focus:border-gray-400 transition-colors placeholder:text-gray-400"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[11px] text-gray-400 border border-border rounded px-1.5 py-0.5">
              /
            </kbd>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="max-w-6xl mx-auto px-6 w-full flex gap-10 flex-1">
        {/* Category rail */}
        <aside className="hidden md:block w-44 shrink-0 border-r border-border">
          <nav className="sticky top-0 py-6 pr-4 space-y-0.5 max-h-screen overflow-y-auto">
            <button
              onClick={() => setActiveCat(null)}
              className={`w-full flex items-baseline justify-between text-left text-[13px] py-1 transition-colors
                ${!activeCat ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-900'}`}
            >
              <span>All</span>
              <span className="font-mono text-[11px] text-gray-400">{totalApis ?? ''}</span>
            </button>
            {categories.map((c) => (
              <button
                key={c.category}
                onClick={() => setActiveCat(c.category)}
                className={`w-full flex items-baseline justify-between gap-2 text-left text-[13px] py-1 transition-colors
                  ${activeCat === c.category ? 'text-gray-900 font-medium' : 'text-gray-500 hover:text-gray-900'}`}
              >
                <span className="truncate">{c.category}</span>
                <span className="font-mono text-[11px] text-gray-400 shrink-0">{c.count}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Results */}
        <main className="flex-1 min-w-0 py-6">
          <div className="flex items-baseline justify-between mb-1 pb-2 border-b border-border">
            <h2 className="text-sm font-medium text-gray-900">
              {heading} <span className="font-mono text-xs text-gray-400 ml-1">{loading ? '' : total.toLocaleString()}</span>
            </h2>
            <button
              onClick={() => setAuthFilter(authFilter === 'none' ? null : 'none')}
              className={`font-mono text-xs transition-colors ${authFilter === 'none' ? 'text-msu-green' : 'text-gray-400 hover:text-gray-700'}`}
            >
              {authFilter === 'none' ? '✓ ' : ''}no key
            </button>
          </div>

          {offline ? (
            <p className="text-sm text-gray-500 py-16 text-center font-mono">directory unreachable — backend offline</p>
          ) : loading ? (
            <div className="divide-y divide-border/60">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="h-11 flex items-center"><div className="h-3 bg-gray-100 rounded w-1/3 animate-pulse" /></div>
              ))}
            </div>
          ) : results.length === 0 ? (
            <p className="text-sm text-gray-500 py-16 text-center font-mono">no matches</p>
          ) : (
            <div className="divide-y divide-border/60">
              {results.map((item) => (
                <Row key={item.id} item={item} state={monitorState[item.id]} onMonitor={onMonitor} />
              ))}
            </div>
          )}

          {!loading && total > results.length && (
            <p className="text-center font-mono text-[11px] text-gray-400 mt-6">
              {results.length} / {total.toLocaleString()} — narrow with search or a category
            </p>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-border mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between font-mono text-[11px] text-gray-400">
          <span>© {new Date().getFullYear()} LightAPI</span>
          <span className="hidden sm:inline">data · public-apis</span>
          <span className="flex items-center gap-3">
            <Link to="/about" className="hover:text-gray-700 transition-colors">about</Link>
            <Link to="/privacy" className="hover:text-gray-700 transition-colors">privacy</Link>
          </span>
        </div>
      </footer>
    </div>
  )
}
