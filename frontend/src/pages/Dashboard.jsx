import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { Plus, Activity } from 'lucide-react'
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
    <div className="flex items-center gap-5">
      <div className="text-center">
        <span className="text-xs text-gray-400">Endpoints</span>
        <p className="text-sm font-mono font-semibold text-gray-900">{stats.total_endpoints}</p>
      </div>
      <div className="w-px h-8 bg-border" />
      <div className="text-center">
        <span className="text-xs text-gray-400">Global Uptime</span>
        <p className="text-sm font-mono font-semibold text-status-healthy">{stats.global_uptime}%</p>
      </div>
      <div className="w-px h-8 bg-border" />
      <div className="text-center">
        <span className="text-xs text-gray-400">Active Incidents</span>
        <p className={`text-sm font-mono font-semibold ${stats.active_incidents > 0 ? 'text-status-down' : 'text-gray-900'}`}>
          {stats.active_incidents}
        </p>
      </div>
    </div>
  )
}

function EmptyState({ onAdd }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center max-w-sm">
        <div className="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center mx-auto mb-4">
          <Activity size={22} className="text-msu-green" />
        </div>
        <h2 className="text-sm font-semibold text-gray-900 mb-2">No endpoints yet</h2>
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

export default function Dashboard() {
  const { endpointId } = useParams()
  const navigate = useNavigate()
  const { endpoints, loading, updateEndpoint, addEndpoint, removeEndpoint } = useEndpoints()
  const [globalStats, setGlobalStats] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    api.getGlobalStats().then(setGlobalStats).catch(() => {})
    const id = setInterval(() => api.getGlobalStats().then(setGlobalStats).catch(() => {}), 15000)
    return () => clearInterval(id)
  }, [])

  const activeEndpoint = endpoints.find((e) => e.id === endpointId) || endpoints[0] || null

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

  useWebSocket('/ws', handleWsMessage)

  const handleAdded = (ep) => {
    addEndpoint(ep)
    navigate(`/dashboard/${ep.id}`)
    api.getGlobalStats().then(setGlobalStats).catch(() => {})
  }

  return (
    <div className="h-screen flex flex-col bg-base overflow-hidden">
      {/* Top bar */}
      <header className="bg-white border-b border-border shrink-0">
        <div className="h-14 px-5 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-msu-green">
              <polyline points="2,14 5,14 7,6 9,20 11,11 13,9 15,15 17,14 22,14" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-base font-bold text-gray-900 tracking-tight">LightAI</span>
          </Link>
          <GlobalStats stats={globalStats} />
          <SettingsDropdown
            activeEndpoint={activeEndpoint}
            onDeleted={(id) => { removeEndpoint(id); navigate('/dashboard') }}
          />
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
                <div key={i} className="h-24 rounded-lg bg-white border border-border animate-pulse" />
              ))}
            </div>
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
