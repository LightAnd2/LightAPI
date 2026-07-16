import { TrendingUp, TrendingDown } from 'lucide-react'

export default function DriftPanel({ drift }) {
  if (!drift || drift.status === 'stable' || drift.status === 'insufficient_data') return null

  const isDegraded = drift.status === 'degraded'
  const isCritical = drift.severity === 'critical'

  const borderColor = isCritical ? 'border-red-200' : 'border-amber-200'
  const bgColor = isCritical ? 'bg-red-50' : 'bg-amber-50'
  const textColor = isCritical ? 'text-status-down' : 'text-status-degraded'
  const Icon = isDegraded ? TrendingUp : TrendingDown

  return (
    <div className={`rounded-sm border ${borderColor} ${bgColor} p-4`}>
      <div className="flex items-start gap-3">
        <Icon size={16} className={`${textColor} mt-0.5 shrink-0`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold ${textColor}`}>
              Baseline Drift {isDegraded ? 'Detected' : 'Improved'}
            </span>
            <span className={`text-xs font-mono font-medium ${textColor}`}>
              {drift.drift_percent > 0 ? '+' : ''}{drift.drift_percent}%
            </span>
          </div>
          <p className="text-xs text-gray-700 leading-relaxed">{drift.message}</p>

          <div className="mt-3 grid grid-cols-3 gap-3">
            {[
              { label: '30d baseline', value: drift.baseline_30d_ms },
              { label: '7d baseline', value: drift.baseline_7d_ms },
              { label: 'Last 24h', value: drift.baseline_24h_ms },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-gray-400">{label}</p>
                <p className={`text-sm font-mono font-semibold ${label === 'Last 24h' ? textColor : 'text-gray-700'}`}>
                  {value != null ? `${value}ms` : '—'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
