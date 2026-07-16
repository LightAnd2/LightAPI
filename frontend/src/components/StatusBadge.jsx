export default function StatusBadge({ status }) {
  const config = {
    healthy: { label: 'healthy', cls: 'bg-green-50 text-status-healthy border-green-200' },
    degraded: { label: 'degraded', cls: 'bg-amber-50 text-status-degraded border-amber-200' },
    down: { label: 'down', cls: 'bg-red-50 text-status-down border-red-200' },
    unknown: { label: 'unknown', cls: 'bg-gray-50 text-gray-500 border-gray-200' },
  }
  const { label, cls } = config[status] || config.unknown
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium border font-mono ${cls}`}>
      {label}
    </span>
  )
}
