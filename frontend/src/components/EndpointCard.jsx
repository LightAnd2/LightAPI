import StatusIndicator from './StatusIndicator'

export default function EndpointCard({ endpoint, isActive, onClick }) {
  const latency = endpoint.current_latency
  const latencyStr = latency != null ? `${Math.round(latency)}ms` : '—'

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-3 flex items-center gap-3 transition-colors border-l-2 hover:bg-gray-50/80 ${
        isActive
          ? 'border-l-msu-green bg-green-50/40'
          : 'border-l-transparent'
      }`}
    >
      <StatusIndicator status={endpoint.current_status} size="sm" pulse={endpoint.current_status === 'healthy'} />
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-medium truncate ${isActive ? 'text-msu-green' : 'text-gray-900'}`}>
          {endpoint.name}
        </p>
        <p className="text-xs text-gray-400 truncate font-mono mt-0.5">{endpoint.url.replace(/^https?:\/\//, '')}</p>
      </div>
      <div className="text-right shrink-0">
        <p className={`text-xs font-mono font-medium ${
          endpoint.current_status === 'down' ? 'text-status-down' :
          endpoint.current_status === 'degraded' ? 'text-status-degraded' :
          'text-gray-600'
        }`}>{latencyStr}</p>
        <p className="text-xs text-gray-400 mt-0.5">{endpoint.uptime_24h}%</p>
      </div>
    </button>
  )
}
