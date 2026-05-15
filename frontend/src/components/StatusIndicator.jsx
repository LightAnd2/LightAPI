export default function StatusIndicator({ status, size = 'sm', pulse = false }) {
  const colors = {
    healthy: 'bg-status-healthy',
    degraded: 'bg-status-degraded',
    down: 'bg-status-down',
    unknown: 'bg-gray-300',
  }

  const sizes = {
    xs: 'w-1.5 h-1.5',
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  }

  const color = colors[status] || colors.unknown
  const sz = sizes[size] || sizes.sm

  return (
    <span className="relative inline-flex items-center justify-center">
      {pulse && status === 'healthy' && (
        <span className={`absolute inline-flex rounded-full ${sz} ${color} opacity-75 animate-ping`} />
      )}
      <span className={`relative inline-flex rounded-full ${sz} ${color}`} />
    </span>
  )
}
