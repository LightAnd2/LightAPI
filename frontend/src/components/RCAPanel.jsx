import { AlertTriangle, CheckCircle, GitBranch } from 'lucide-react'

const VERDICT_CONFIG = {
  isolated: {
    icon: CheckCircle,
    label: 'Isolated Failure',
    color: 'text-status-down',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
  upstream_dependency: {
    icon: GitBranch,
    label: 'Upstream Dependency',
    color: 'text-status-degraded',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
  },
  shared_infrastructure: {
    icon: AlertTriangle,
    label: 'Shared Infrastructure',
    color: 'text-status-degraded',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
  },
  cascading_failure: {
    icon: AlertTriangle,
    label: 'Cascading Failure',
    color: 'text-status-down',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
}

export default function RCAPanel({ rca }) {
  if (!rca) return null

  const config = VERDICT_CONFIG[rca.verdict] || VERDICT_CONFIG.isolated
  const Icon = config.icon

  return (
    <div className={`rounded-lg border ${config.border} ${config.bg} p-4`}>
      <div className="flex items-start gap-3">
        <Icon size={16} className={`${config.color} mt-0.5 shrink-0`} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold ${config.color}`}>{config.label}</span>
            <span className="text-xs text-gray-400 font-mono">{Math.round(rca.confidence * 100)}% confidence</span>
          </div>
          <p className="text-xs text-gray-700 leading-relaxed">{rca.summary}</p>

          {rca.correlated_endpoints?.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="text-xs font-medium text-gray-500 mb-1.5">Correlated endpoints</p>
              {rca.correlated_endpoints.map((ep) => (
                <div key={ep.endpoint_id} className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-700">{ep.endpoint_name}</span>
                  <span className="font-mono text-gray-400">
                    {ep.offset_seconds > 0 ? `+${ep.offset_seconds}s after` : ep.offset_seconds < 0 ? `${Math.abs(ep.offset_seconds)}s before` : 'simultaneous'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
