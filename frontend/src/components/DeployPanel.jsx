import { GitCommit, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import { format, parseISO } from 'date-fns'

function fmtTs(ts) {
  try { return format(parseISO(ts), 'MMM d, HH:mm') } catch { return ts }
}

export default function DeployPanel({ deploys = [], liveEvent = null }) {
  const all = liveEvent ? [liveEvent, ...deploys.filter(d => d.id !== liveEvent.id)] : deploys

  if (all.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-6 text-center">
        No deploys detected yet. Add a GitHub webhook to start tracking.
      </div>
    )
  }

  return (
    <div className="divide-y divide-border">
      <div className="grid grid-cols-4 gap-2 px-4 py-2 text-xs font-medium text-gray-400 uppercase tracking-wide">
        <span>Commit</span>
        <span>Branch</span>
        <span className="font-mono">Pre → Post</span>
        <span>Result</span>
      </div>
      {all.map((d) => (
        <div key={d.id} className="grid grid-cols-4 gap-2 px-4 py-3 hover:bg-gray-50 transition-colors">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <GitCommit size={12} className="text-gray-400 shrink-0" />
              <span className="font-mono text-xs font-medium text-gray-900">{d.commit_sha}</span>
            </div>
            <p className="text-xs text-gray-400 truncate mt-0.5">{fmtTs(d.deployed_at)}</p>
          </div>
          <div className="min-w-0">
            <p className="text-xs text-gray-600 truncate">{d.branch}</p>
            <p className="text-xs text-gray-400 truncate">{d.pusher}</p>
          </div>
          <div>
            {d.pre_deploy_baseline_ms != null && d.post_deploy_baseline_ms != null ? (
              <span className="font-mono text-xs text-gray-600">
                {Math.round(d.pre_deploy_baseline_ms)}ms → {Math.round(d.post_deploy_baseline_ms)}ms
              </span>
            ) : d.analysis_complete === false ? (
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <Clock size={11} />
                Analyzing…
              </span>
            ) : (
              <span className="text-xs text-gray-400">—</span>
            )}
          </div>
          <div>
            {!d.analysis_complete ? (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-gray-50 text-gray-400 border border-gray-200">
                <Clock size={10} /> Pending
              </span>
            ) : d.regression_detected ? (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-red-50 text-status-down border border-red-200 font-medium">
                <AlertTriangle size={10} /> +{d.regression_percent}%
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-green-50 text-status-healthy border border-green-200">
                <CheckCircle size={10} /> Clean
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
