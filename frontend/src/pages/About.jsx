import { Link } from 'react-router-dom'
import PageShell from '../components/PageShell'

function Section({ label, title, children }) {
  return (
    <section className="mb-10">
      <p className="font-mono text-[11px] text-gray-400 mb-1">{label}</p>
      <h2 className="text-sm font-medium text-gray-900 mb-3 pb-2 border-b border-border">{title}</h2>
      <div className="space-y-3 text-sm text-gray-600 leading-relaxed">{children}</div>
    </section>
  )
}

function Step({ n, children }) {
  return (
    <li className="flex gap-3">
      <span className="shrink-0 font-mono text-[11px] text-gray-400 pt-0.5">{String(n).padStart(2, '0')}</span>
      <span>{children}</span>
    </li>
  )
}

export default function About() {
  return (
    <PageShell crumb="about">
      <h1 className="text-2xl font-semibold tracking-tight leading-tight">
        What this is <span className="text-gray-400">and how to use it.</span>
      </h1>
      <p className="mt-3 mb-12 text-sm text-gray-600 leading-relaxed">
        LightAPI is a directory of 1,500+ free public APIs where every entry is
        <em> monitorable</em>: one click puts any API on a live dashboard that tracks
        its uptime and latency, and a small neural network learns what &ldquo;normal&rdquo;
        looks like for that endpoint so it can flag trouble early.
      </p>

      <Section label="directions" title="Getting started">
        <ol className="space-y-3">
          <Step n={1}>
            <strong className="font-medium text-gray-900">Find an API.</strong> Browse by category or press{' '}
            <kbd className="font-mono text-[11px] border border-border rounded px-1 py-0.5">/</kbd> and type to search.
            The <span className="font-mono text-xs">no key</span> filter shows APIs you can call without signing up anywhere.
          </Step>
          <Step n={2}>
            <strong className="font-medium text-gray-900">Click monitor.</strong> The API is added to your own
            workspace and you land on its dashboard. The first latency reading arrives within ~30 seconds.
          </Step>
          <Step n={3}>
            <strong className="font-medium text-gray-900">Read the dashboard.</strong> Live latency chart
            (updates over WebSocket), uptime over 7/30 days, an incident log, and anomaly events as the
            model flags them.
          </Step>
          <Step n={4}>
            <strong className="font-medium text-gray-900">Add your own endpoints.</strong> <em>Add Endpoint</em> monitors
            any URL — your side project, your company&rsquo;s status page — with a custom check interval, alert
            threshold, and an optional webhook that gets POSTed when something breaks.
          </Step>
          <Step n={5}>
            <strong className="font-medium text-gray-900">Share your workspace.</strong> The code in the dashboard&rsquo;s
            top-right corner copies a link to your workspace. It&rsquo;s the only key to it — anyone with the link can
            view and edit, so treat it like a password.
          </Step>
        </ol>
      </Section>

      <Section label="info" title="What the models do">
        <p>
          Each endpoint gets its own anomaly detector. It starts as a simple statistical
          baseline (readings more than 2.5σ from the rolling mean are flagged), and once
          100 readings exist, a per-endpoint <strong className="font-medium text-gray-900">LSTM</strong> takes
          over — it learns the endpoint&rsquo;s daily rhythm, so a spike at 3 a.m. registers as more
          unusual than the same spike at noon. The dashboard shows which mode is active.
        </p>
        <p>
          When something does break, incidents are logged and correlated: if only one of your
          endpoints failed, it&rsquo;s reported as an isolated failure; if several failed in the same
          window, that points to something shared — network, provider, or your own infrastructure.
        </p>
      </Section>

      <Section label="info" title="Good to know">
        <ul className="space-y-2">
          <li>— No accounts, no login. A workspace is created for you on first visit and lives in your browser + its shareable link.</li>
          <li>— The backend runs on a free tier: after ~15 quiet minutes it sleeps, and the first visit afterwards takes up to a minute to wake it.</li>
          <li>— The demo workspace is read-only; your own workspace is fully editable.</li>
          <li>— The directory is sourced from the community <a href="https://github.com/public-apis/public-apis" target="_blank" rel="noreferrer" className="text-msu-green hover:underline">public-apis</a> project and refreshes daily.</li>
          <li>— Everything is open source: <a href="https://github.com/LightAnd2/LightAPI" target="_blank" rel="noreferrer" className="text-msu-green hover:underline">github.com/LightAnd2/LightAPI</a> — the README documents the full REST API and how to self-host.</li>
        </ul>
      </Section>

      <p className="text-sm text-gray-500">
        Questions about data? See the <Link to="/privacy" className="text-msu-green hover:underline">privacy policy</Link>.
      </p>
    </PageShell>
  )
}
