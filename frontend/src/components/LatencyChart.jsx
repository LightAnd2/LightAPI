import { useState, useEffect } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ReferenceArea, Legend,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { api } from '../services/api'

const RANGES = ['1h', '24h', '7d', '30d', '90d']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-md shadow-card-hover p-2.5 text-xs">
      <p className="text-gray-500 mb-1.5">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-600">{p.name}:</span>
          <span className="font-mono font-medium text-gray-900">
            {p.value != null ? `${Math.round(p.value)}ms` : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

function formatTick(ts, range) {
  try {
    const d = parseISO(ts)
    if (range === '1h' || range === '24h') return format(d, 'HH:mm')
    return format(d, 'MMM d')
  } catch {
    return ts
  }
}

export default function LatencyChart({ endpointId, alertThreshold, anomalies = [], liveReadings = [] }) {
  const [range, setRange] = useState('24h')
  const [readings, setReadings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getReadings(endpointId, range)
      .then((data) => setReadings(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [endpointId, range])

  useEffect(() => {
    if (liveReadings.length === 0) return
    setReadings((prev) => {
      const combined = [...prev, ...liveReadings]
      const seen = new Set()
      return combined.filter((r) => {
        if (seen.has(r.timestamp)) return false
        seen.add(r.timestamp)
        return true
      })
    })
  }, [liveReadings])

  const anomalySet = new Set(anomalies.map((a) => a.timestamp.slice(0, 16)))

  const data = readings.map((r) => ({
    timestamp: r.timestamp,
    label: formatTick(r.timestamp, range),
    latency: r.success && r.latency_ms != null ? Math.round(r.latency_ms) : null,
    anomaly: anomalySet.has(r.timestamp.slice(0, 16)) ? Math.round(r.latency_ms ?? 0) : null,
  }))

  const anomalyRegions = []
  anomalies.forEach((a) => {
    const ts = a.timestamp
    anomalyRegions.push({ x1: ts, x2: ts })
  })

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center text-sm text-gray-400">Loading chart...</div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-sm text-gray-400">
        No data yet — readings will appear here as monitoring collects them.
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors font-mono ${
                range === r
                  ? 'bg-msu-green text-white'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-status-healthy inline-block" />
            Latency
          </span>
          {anomalies.length > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-amber-100 border border-amber-300 inline-block" />
              Anomaly
            </span>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v}ms`}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} />
          {alertThreshold && (
            <ReferenceLine
              y={alertThreshold}
              stroke="#D97706"
              strokeDasharray="4 3"
              strokeWidth={1}
              label={{ value: `${alertThreshold}ms`, position: 'right', fontSize: 10, fill: '#D97706', fontFamily: 'JetBrains Mono, monospace' }}
            />
          )}
          {anomalyRegions.map((region, i) => (
            <ReferenceArea
              key={i}
              x1={region.x1}
              x2={region.x2}
              fill="#FEF3C7"
              fillOpacity={0.6}
            />
          ))}
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#2DA44E"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, fill: '#2DA44E' }}
            connectNulls={false}
            name="Latency"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
