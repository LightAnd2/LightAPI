import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { Plus, Activity, CloudOff, RefreshCw, Link2, Check } from 'lucide-react'
import SettingsDropdown from '../components/SettingsDropdown'
import { useEndpoints } from '../hooks/useEndpoints'
import { useWebSocket } from '../hooks/useWebSocket'
import EndpointCard from '../components/EndpointCard'
import EndpointDetail from './EndpointDetail'
import AddEndpointModal from '../components/AddEndpointModal'
import { api } from '../services/api'

function GlobalStats({ stats }) {
  if (!stats) return null
  return (
    <div className="hidden sm:flex items-center gap-4 font-mono text-xs text-gray-400">
      <span><span className="text-gray-900">{stats.total_endpoints}</span> endpoints</span>
      <span className="text-gray-200">·</span>
      <span><span className="text-status-healthy">{stats.global_uptime}%</span> uptime</span>
      <span className="text-gray-200">·</span>
      <span>
        <span className={stats.active_incidents > 0 ? 'text-status-down' : 'text-gray-900'}>{stats.active_incidents}</span> incidents
      </span>
    </div>
  )
}

function WorkspaceChip({ wsId }) {
  const [copied, setCopied] = useState(false)
  if (!wsId) return null

  const copy = () => {
    navigator.clipboard.writeText(`${window.location.origin}/dashboard?ws=${wsId}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <button
      onClick={copy}
      title="Copy this workspace's link. Treat it like a password — anyone who has it can view and edit this workspace."
      className="flex items-center gap-1.5 px-2 py-1 rounded border border-border text-xs font-mono text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-colors"
    >
      {copied ? <Check size={12} className="text-status-healthy" /> : <Link2 size={12} />}
      {copied ? 'copied' : wsId}
    </button>
  )
}

function EmptyState({ onAdd }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-sm">
        <Activity size={22} className="text-msu-green mx-auto mb-4" />
        <h2 className="text-sm font-medium text-gray-900 mb-2">No endpoints yet</h2>
        <p className="text-sm text-gray-500 mb-5">
          Add your first endpoint to start monitoring uptime, latency, and anomalies.
        </p>
        <button onClick={onAdd} className="btn-primary">
          Add Endpoint
        </button>
      </div>
    </div>
  )
}

function BackendOffline({ onRetry }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-sm">
        <CloudOff size={22} className="text-status-down mx-auto mb-4" />
        <h2 className="text-sm font-medium text-gray-900 mb-2">Can&apos;t reach the backend</h2>
        <p className="text-sm text-gray-500 mb-5">
          The monitoring API is currently unreachable. Live data and updates are paused until it&apos;s back online.
        </p>
        <button onClick={onRetry} className="btn-secondary inline-flex items-center gap-2">
          <RefreshCw size={14} />
          Retry
        </button>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { endpointId } = useParams()
  const navigate = useNavigate()
  const { endpoints, loading, error, refetch, updateEndpoint, addEndpoint, removeEndpoint } = useEndpoints()
  const [globalStats, setGlobalStats] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [wsId, setWsId] = useState(null)

  useEffect(() => {
    api.getWorkspace().then(setWsId).catch(() => {})
    api.getGlobalStats().then(setGlobalStats).catch(() => {})
    const id = setInterval(() => api.getGlobalStats().then(setGlobalStats).catch(() => {}), 15000)
    return () => clearInterval(id)
  }, [])

  const activeEndpoint = endpoints.find((e) => e.id === endpointId) || endpoints[0] || null
  const offline = !!error && endpoints.length === 0

  useEffect(() => {
    if (!endpointId && activeEndpoint) {
      navigate(`/dashboard/${activeEndpoint.id}`, { replace: true })
    }
  }, [endpointId, activeEndpoint, navigate])

  const handleWsMessage = useCallback((msg) => {
    if (msg.type !== 'reading') return
    const { endpoint_id, data } = msg
    const patch = { last_checked: data.timestamp }
    if (data.latency_ms != null) patch.current_latency = data.latency_ms
    if (!data.success) patch.current_status = 'down'
    else if (data.latency_ms != null) {
      const ep = endpoints.find((e) => e.id === endpoint_id)
      patch.current_status = ep && data.latency_ms > ep.alert_threshold ? 'degraded' : 'healthy'
    }
    updateEndpoint(endpoint_id, patch)
  }, [endpoints, updateEndpoint])

  useWebSocket(wsId ? `/ws?workspace=${encodeURIComponent(wsId)}` : null, handleWsMessage)

  const handleAdded = (ep) => {
    addEndpoint(ep)
    navigate(`/dashboard/${ep.id}`)
    api.getGlobalStats().then(setGlobalStats).catch(() => {})
  }

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      {/* Top bar */}
      <header className="bg-white border-b border-border shrink-0">
        <div className="h-12 px-5 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-msu-green">
              <polyline points="2,14 5,14 7,6 9,20 11,11 13,9 15,15 17,14 22,14" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-sm font-bold tracking-tight">LightAPI</span>
            <span className="hidden sm:inline text-xs text-gray-400 font-mono ml-1">/ dashboard</span>
          </Link>
          <GlobalStats stats={globalStats} />
          <div className="flex items-center gap-3">
            <Link to="/" className="hidden sm:inline text-xs font-mono text-gray-500 hover:text-gray-900 transition-colors">
              directory →
            </Link>
            <WorkspaceChip wsId={wsId} />
            <SettingsDropdown
              activeEndpoint={activeEndpoint}
              onDeleted={(id) => { removeEndpoint(id); navigate('/dashboard') }}
            />
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-border flex flex-col shrink-0">
          <div className="px-3 py-3 border-b border-border">
            <button
              onClick={() => setModalOpen(true)}
              className="w-full flex items-center justify-center gap-2 btn-primary py-2"
            >
              <Plus size={14} />
              Add Endpoint
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 rounded bg-gray-100 animate-pulse" />
                ))}
              </div>
            ) : offline ? (
              <p className="text-xs text-status-down text-center mt-8 px-4">Backend unreachable.</p>
            ) : endpoints.length === 0 ? (
              <p className="text-xs text-gray-400 text-center mt-8 px-4">No endpoints. Add one to get started.</p>
            ) : (
              endpoints.map((ep) => (
                <EndpointCard
                  key={ep.id}
                  endpoint={ep}
                  isActive={ep.id === (endpointId || activeEndpoint?.id)}
                  onClick={() => navigate(`/dashboard/${ep.id}`)}
                />
              ))
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 rounded-sm bg-white border border-border animate-pulse" />
              ))}
            </div>
          ) : offline ? (
            <BackendOffline onRetry={refetch} />
          ) : activeEndpoint ? (
            <EndpointDetail key={activeEndpoint.id} endpoint={activeEndpoint} />
          ) : (
            <EmptyState onAdd={() => setModalOpen(true)} />
          )}
        </main>
      </div>

      <AddEndpointModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onAdded={handleAdded}
      />
    </div>
  )
}
