import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Github, Linkedin } from 'lucide-react'
import StatusIndicator from '../components/StatusIndicator'
import { api } from '../services/api'

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

function LiveStatusStrip({ endpoints }) {
  if (!endpoints || endpoints.length === 0) return null
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-8">
      {endpoints.slice(0, 4).map((ep) => (
        <div key={ep.id} className="flex items-center gap-2">
          <StatusIndicator status={ep.current_status} size="xs" />
          <span className="text-xs text-gray-600">{ep.name}</span>
          <span className="font-mono text-xs text-gray-400">
            {ep.current_latency != null ? `${Math.round(ep.current_latency)}ms` : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

const CODE_SNIPPET = `from lightai import monitor

@monitor(name="get_users", threshold_ms=200)
def get_users(org_id: str):
    return db.query(User).filter_by(org_id=org_id).all()`

export default function Landing() {
  const [endpoints, setEndpoints] = useState([])

  useEffect(() => {
    api.getEndpoints('demo').then(setEndpoints).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-base">
      <header className="bg-white border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <Logo size={22} />
            <span className="text-base font-bold text-gray-900 tracking-tight">LightAI</span>
          </Link>
          <Link to="/dashboard" className="btn-primary text-xs px-3 py-1.5">
            Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6">
        <section className="pt-14 pb-10">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            <h1 className="text-4xl font-bold text-gray-900 tracking-tight mb-3 leading-tight">
              Latency and uptime monitoring for your APIs
            </h1>
            <p className="text-base text-gray-500 max-w-xl leading-relaxed mb-7">
              LightAI pings your endpoints, then trains a small model on each one&apos;s history to flag anomalies and predict slowdowns before they turn into outages.
            </p>

            <div className="flex items-center gap-3">
              <Link to="/dashboard" className="btn-primary px-5 py-2 text-sm">
                Open Dashboard
              </Link>
              <Link to="/dashboard?ws=demo" className="btn-secondary px-5 py-2 text-sm">
                View Demo
              </Link>
            </div>

          </motion.div>
        </section>

        <div className="border-t border-border" />

        <section className="py-10">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-6">Three ways to use it</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              label: 'Paste a URL',
              description: 'Add any endpoint from the dashboard. LightAI starts pinging every 30 seconds with no code changes required.',
              code: '# No code needed\n# Add a URL in the dashboard',
            },
            {
              label: 'Decorate a function',
              description: 'Wrap any Python function with @monitor. Execution time is reported on every call without touching your logic.',
              code: 'from lightai import monitor\n\n@monitor(name="checkout")\ndef checkout(cart_id): ...',
            },
            {
              label: 'Connect GitHub',
              description: 'Add one webhook to your repo. LightAI snapshots latency before each push and flags regressions by commit SHA.',
              code: '# Payload URL:\n/api/webhooks/github',
            },
          ].map(({ label, description, code }) => (
            <div key={label} className="border border-border rounded-lg p-5 space-y-3">
              <p className="text-sm font-semibold text-gray-900">{label}</p>
              <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
              <pre className="bg-gray-950 rounded px-3 py-2.5 text-xs font-mono text-gray-300 leading-relaxed overflow-x-auto whitespace-pre">
                <code>{code}</code>
              </pre>
            </div>
          ))}
          </div>
        </section>

        <div className="border-t border-border" />

        <section className="py-12">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-8">What it does</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
          <div className="space-y-6">
            {[
              {
                title: 'Endpoint monitoring',
                body: 'Pings any URL every 30 seconds. Records latency, status code, and uptime. Dashboard updates over WebSocket within 100ms of each reading.',
              },
              {
                title: 'Per-service LSTM',
                body: 'After 100 readings, trains a dedicated LSTM on that endpoint\'s own latency history. Understands time-of-day and weekly patterns rather than comparing to a global average.',
              },
              {
                title: 'Predictive alerts',
                body: 'If latency is trending up, the model projects where it\'s going and fires a webhook before the threshold is crossed. Works with Slack, Discord, PagerDuty, or any URL.',
              },
              {
                title: 'Function-level tracing',
                body: 'The @monitor decorator instruments any Python function and reports execution time directly to LightAI. Works with Flask, FastAPI, background jobs, or plain scripts.',
              },
              {
                title: 'Deploy regression tracking',
                body: 'Add a GitHub webhook and LightAI compares pre/post-deploy latency baselines. Links regressions directly to the commit SHA that caused them.',
              },
            ].map(({ title, body }) => (
              <div key={title} className="border-l-2 border-border pl-4">
                <p className="text-sm font-semibold text-gray-900 mb-1">{title}</p>
                <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          <div className="sticky top-8 space-y-4">
            <div className="bg-gray-950 rounded-lg overflow-hidden border border-gray-800">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800">
                <span className="text-xs text-gray-500 font-mono">users.py</span>
                <span className="text-xs text-gray-600">Python</span>
              </div>
              <pre className="px-5 py-4 text-xs font-mono text-gray-300 leading-relaxed overflow-x-auto whitespace-pre">
                <code>{CODE_SNIPPET}</code>
              </pre>
            </div>

            <div className="bg-white border border-border rounded-lg p-4 space-y-3">
              <p className="text-xs font-semibold text-gray-700">Install</p>
              <div className="bg-gray-50 rounded px-3 py-2 font-mono text-xs text-gray-600">
                pip install lightai
              </div>
              <div className="bg-gray-50 rounded px-3 py-2 font-mono text-xs text-gray-600">
                LIGHTAI_URL=https://your-backend.railway.app
              </div>
            </div>
          </div>
          </div>
        </section>

        <div className="border-t border-border" />

        <section className="py-12">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-8">Quick start</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              step: '1 — Backend',
              lines: ['cd backend', 'pip install -r requirements.txt', 'uvicorn app.main:app --port 8000'],
            },
            {
              step: '2 — Frontend',
              lines: ['cd frontend', 'npm install', 'npm run dev'],
            },
            {
              step: '3 — SDK',
              lines: ['pip install lightai', '# then in your code:', 'from lightai import monitor'],
            },
          ].map(({ step, lines }) => (
            <div key={step}>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">{step}</p>
              <div className="bg-gray-950 rounded-md px-4 py-3 space-y-1">
                {lines.map((l) => (
                  <p key={l} className={`font-mono text-xs ${l.startsWith('#') ? 'text-gray-600' : 'text-gray-300'}`}>{l}</p>
                ))}
              </div>
            </div>
          ))}
          </div>
        </section>

        <div className="border-t border-border" />

        <section className="py-8 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
          {[
            { value: '28,800+', label: 'readings / day per endpoint' },
            { value: '100ms', label: 'WebSocket update latency' },
            { value: '$0', label: 'infrastructure cost' },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-lg font-bold text-gray-900 font-mono">{s.value}</p>
              <p className="text-xs text-gray-400 mt-1">{s.label}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-border bg-white mt-2">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Logo size={14} />
            <span className="text-xs font-bold text-gray-700">LightAI</span>
          </div>
          <p className="text-xs text-gray-400">&copy; {new Date().getFullYear()} Andrew Koja. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link to="/privacy" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">Privacy Policy</Link>
            <a href="https://github.com/LightAnd2" target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-600 transition-colors">
              <Github size={14} />
            </a>
            <a href="https://www.linkedin.com/in/andrewkoja" target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-600 transition-colors">
              <Linkedin size={14} />
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
