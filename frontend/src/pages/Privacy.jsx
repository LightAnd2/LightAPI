import { Link } from 'react-router-dom'

function Logo({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="text-msu-green">
      <polyline
        points="2,14 5,14 7,6 9,20 11,11 13,9 15,15 17,14 22,14"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function Privacy() {
  return (
    <div className="min-h-screen bg-base">
      <header className="bg-white border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <Logo size={22} />
            <span className="text-base font-bold text-gray-900 tracking-tight">LightAPI</span>
          </Link>
          <Link to="/dashboard" className="btn-primary text-xs px-3 py-1.5">
            Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-14">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-xs text-gray-400 mb-10">Last updated July 2026</p>

        <div className="space-y-8 text-sm text-gray-600 leading-relaxed">

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Overview</h2>
            <p>LightAPI is an open-source public API directory and monitoring tool. This policy explains what data is collected when you use LightAPI, how it is stored, and how it is used. LightAPI does not sell, share, or monetize any data.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">What we collect</h2>
            <ul className="list-disc list-inside space-y-1">
              <li>URLs you add to the dashboard for monitoring</li>
              <li>Latency readings, HTTP status codes, and uptime records for those URLs</li>
              <li>Webhook URLs you optionally provide for alerts</li>
              <li>GitHub repository names if you configure deploy tracking</li>
            </ul>
            <p className="mt-3">We do not collect names, email addresses, passwords, payment information, or any other personally identifiable information.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">How data is used</h2>
            <p>Collected data is used solely to power the monitoring dashboard — displaying latency charts, anomaly detection, incident logs, and deploy tracking. No data is used for advertising, analytics, or any purpose outside of the monitoring functionality you configured.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Data storage</h2>
            <p>All monitoring data is stored in a SQLite database on the backend server (hosted on Render). Trained LSTM model weights are stored on the same server. No data is sent to third-party analytics or data platforms.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Third-party requests</h2>
            <p>LightAPI makes outbound HTTP requests to the URLs you add in order to measure their latency and availability. These requests originate from the backend server and include a standard HTTP User-Agent header. No personal data is included in these requests.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Webhooks</h2>
            <p>If you configure a webhook URL for alerts, LightAPI will send POST requests to that URL containing endpoint name, latency values, and alert type. You are responsible for the security of any webhook endpoint you provide.</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Open source</h2>
            <p>LightAPI is fully open source. You can inspect the complete codebase, including all data handling logic, at <a href="https://github.com/LightAnd2/LightAPI" target="_blank" rel="noreferrer" className="text-msu-green hover:underline">github.com/LightAnd2/LightAPI</a>. You are free to self-host the backend for full control over your data.</p>
          </section>

        </div>
      </main>

      <footer className="border-t border-border bg-white mt-2">
        <div className="max-w-5xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Logo size={14} />
              <span className="text-xs font-bold text-gray-700">LightAPI</span>
            </div>
            <p className="text-xs text-gray-400">&copy; {new Date().getFullYear()} Andrew Koja. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
