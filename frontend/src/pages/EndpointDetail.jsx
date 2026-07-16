import { useEffect, useState, useCallback } from 'react'
import { format, parseISO } from 'date-fns'
import StatusBadge from '../components/StatusBadge'
import LatencyChart from '../components/LatencyChart'
import IncidentTimeline from '../components/IncidentTimeline'
import RCAPanel from '../components/RCAPanel'
import DriftPanel from '../components/DriftPanel'
import DeployPanel from '../components/DeployPanel'
import { useWebSocket } from '../hooks/useWebSocket'
import { api } from '../services/api'

function StatCard({ label, value, sub, mono = true }) {
  return (
    <div className="stat-card">
      <p className="font-mono text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-xl font-semibold text-gray-900 ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</p>
      {sub && <p className="font-mono text-[11px] text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function EndpointDetail({ endpoint }) {
  const [stats, setStats] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [liveReadings, setLiveReadings] = useState([])
  const [currentStatus, setCurrentStatus] = useState(endpoint.current_status)
  const [currentLatency, setCurrentLatency] = useState(endpoint.current_latency)
  const [lastChecked, setLastChecked] = useState(endpoint.last_checked)
  const [latestRca, setLatestRca] = useState(null)
  const [drift, setDrift] = useState(null)
  const [deploys, setDeploys] = useState([])
  const [liveDeployEvent, setLiveDeployEvent] = useState(null)

  useEffect(() => {
    setCurrentStatus(endpoint.current_status)
    setCurrentLatency(endpoint.current_latency)
    setLastChecked(endpoint.last_checked)
    setLiveReadings([])
    setLatestRca(null)
    setDrift(null)
    setLiveDeployEvent(null)

    Promise.all([
      api.getStats(endpoint.id),
      api.getIncidents(endpoint.id),
      api.getAnomalies(endpoint.id),
      fetch(`/api/endpoints/${endpoint.id}/drift`).then(r => r.ok ? r.json() : null).catch(() => null),
      api.getDeploys(endpoint.id),
    ]).then(([s, i, a, d, dep]) => {
      setStats(s)
      setIncidents(i)
      setAnomalies(a)
      if (d && d.status !== 'stable' && d.status !== 'insufficient_data') setDrift(d)
      setDeploys(dep || [])
    }).catch(() => {})
  }, [endpoint.id])

  const handleWsMessage = useCallback((msg) => {
    const { data } = msg

    if (msg.type === 'deploy_started') {
      setLiveDeployEvent({ ...data, analysis_complete: false })
      return
    }

    if (msg.type === 'deploy_analysis') {
      setLiveDeployEvent(data)
      setDeploys(prev => {
        const filtered = prev.filter(d => d.id !== data.deploy_id)
        return [{ ...data, id: data.deploy_id }, ...filtered]
      })
      return
    }

    if (msg.type !== 'reading') return

    setLiveReadings((prev) => [...prev.slice(-299), {
      timestamp: data.timestamp,
      latency_ms: data.latency_ms,
      status_code: data.status_code,
      success: data.success,
    }])
    if (data.latency_ms != null) setCurrentLatency(data.latency_ms)
    setLastChecked(data.timestamp)
    if (!data.success) setCurrentStatus('down')
    else if (data.latency_ms != null && data.latency_ms > endpoint.alert_threshold) setCurrentStatus('degraded')
    else setCurrentStatus('healthy')

    if (data.anomaly) {
      setAnomalies((prev) => [{
        id: Date.now(),
        timestamp: data.timestamp,
        confidence: data.anomaly.confidence,
        predicted_latency: data.anomaly.predicted_latency,
        actual_latency: data.latency_ms,
      }, ...prev])
    }
    if (data.rca) setLatestRca(data.rca)
    if (data.drift) setDrift(data.drift)
  }, [endpoint.alert_threshold])

  useWebSocket(`/ws/${endpoint.id}`, handleWsMessage)

  const fmtTs = (ts) => {
    if (!ts) return '—'
    try { return format(parseISO(ts), 'MMM d, HH:mm:ss') } catch { return ts }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-medium text-gray-900 break-all">{endpoint.url}</span>
            <StatusBadge status={currentStatus} />
          </div>
          <p className="text-xs text-gray-400 mt-1 font-mono">
            last checked: {fmtTs(lastChecked)}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className={`text-2xl font-mono font-semibold ${
            currentStatus === 'down' ? 'text-status-down' :
            currentStatus === 'degraded' ? 'text-status-degraded' :
            'text-gray-900'
          }`}>
            {currentLatency != null ? `${Math.round(currentLatency)}ms` : '—'}
          </p>
          <p className="font-mono text-xs text-gray-400">current latency</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="current latency"
          value={currentLatency != null ? `${Math.round(currentLatency)}ms` : '—'}
        />
        <StatCard
          label="uptime 7d"
          value={stats ? `${stats.uptime_7d}%` : '—'}
        />
        <StatCard
          label="uptime 30d"
          value={stats ? `${stats.uptime_30d}%` : '—'}
        />
        <StatCard
          label="incidents 30d"
          value={stats?.incidents_month ?? '—'}
          mono={false}
          sub={stats?.model_ready ? 'lstm active' : 'building model…'}
        />
      </div>

      {/* Drift + RCA alerts */}
      {(drift || latestRca) && (
        <div className="space-y-3">
          <DriftPanel drift={drift} />
          <RCAPanel rca={latestRca} />
        </div>
      )}

      {/* Latency chart */}
      <div className="card p-5">
        <h2 className="text-sm font-medium text-gray-900 mb-4">Latency</h2>
        <LatencyChart
          endpointId={endpoint.id}
          alertThreshold={endpoint.alert_threshold}
          anomalies={anomalies}
          liveReadings={liveReadings}
        />
      </div>

      {/* Incidents + Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="px-5 py-3.5 border-b border-border">
            <h2 className="text-sm font-medium text-gray-900">Incident Log</h2>
          </div>
          <IncidentTimeline incidents={incidents} />
        </div>

        <div className="card">
          <div className="px-5 py-3.5 border-b border-border">
            <h2 className="text-sm font-medium text-gray-900">Anomaly Events</h2>
          </div>
          {anomalies.length === 0 ? (
            <div className="text-sm text-gray-400 py-6 text-center">No anomalies detected.</div>
          ) : (
            <div className="divide-y divide-border">
              <div className="grid grid-cols-3 gap-2 px-4 py-2 font-mono text-[11px] text-gray-400">
                <span>time</span>
                <span>actual</span>
                <span>confidence</span>
              </div>
              {anomalies.slice(0, 12).map((a) => (
                <div key={a.id} className="grid grid-cols-3 gap-2 px-4 py-2.5 hover:bg-gray-50 transition-colors">
                  <span className="font-mono text-xs text-gray-600">
                    {fmtTs(a.timestamp)}
                  </span>
                  <span className="font-mono text-xs font-medium text-status-degraded">
                    {Math.round(a.actual_latency)}ms
                  </span>
                  <span>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono bg-amber-50 text-status-degraded border border-amber-200">
                      {Math.round(a.confidence * 100)}%
                    </span>
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Deploy tracking */}
      <div className="card">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-900">Deploy Tracking</h2>
          {liveDeployEvent && !liveDeployEvent.analysis_complete && (
            <span className="flex items-center gap-1.5 text-xs text-msu-green font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-msu-green animate-pulse" />
              Monitoring post-deploy window
            </span>
          )}
        </div>
        <DeployPanel deploys={deploys} liveEvent={liveDeployEvent} />
      </div>
    </div>
  )
}
