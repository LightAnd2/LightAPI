import { format, parseISO } from 'date-fns'

function formatDuration(seconds) {
  if (seconds == null) return 'ongoing'
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
}

function formatTs(ts) {
  try { return format(parseISO(ts), 'MMM d, HH:mm') } catch { return ts }
}

export default function IncidentTimeline({ incidents }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-6 text-center">No incidents recorded.</div>
    )
  }

  return (
    <div className="divide-y divide-border">
      <div className="grid grid-cols-4 gap-2 px-3 py-2 text-xs font-medium text-gray-400 uppercase tracking-wide">
        <span>Started</span>
        <span>Duration</span>
        <span className="font-mono">Peak</span>
        <span>Severity</span>
      </div>
      {incidents.map((inc) => (
        <div key={inc.id} className="grid grid-cols-4 gap-2 px-3 py-2.5 text-sm hover:bg-gray-50 transition-colors">
          <span className="font-mono text-xs text-gray-600">{formatTs(inc.started_at)}</span>
          <span className="font-mono text-xs text-gray-600">{formatDuration(inc.duration_seconds)}</span>
          <span className={`font-mono text-xs font-medium ${inc.peak_latency > 1000 ? 'text-status-down' : 'text-status-degraded'}`}>
            {inc.peak_latency != null ? `${Math.round(inc.peak_latency)}ms` : '—'}
          </span>
          <span>
            {inc.severity === 'critical' ? (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-50 text-status-down border border-red-200">
                Critical
              </span>
            ) : (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-50 text-status-degraded border border-amber-200">
                Warning
              </span>
            )}
          </span>
        </div>
      ))}
    </div>
  )
}
