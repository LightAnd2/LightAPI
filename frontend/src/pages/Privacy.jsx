import PageShell from '../components/PageShell'

function Section({ title, children }) {
  return (
    <section className="mb-8">
      <h2 className="text-sm font-medium text-gray-900 mb-2">{title}</h2>
      <div className="space-y-3 text-sm text-gray-600 leading-relaxed">{children}</div>
    </section>
  )
}

export default function Privacy() {
  return (
    <PageShell crumb="privacy">
      <h1 className="text-2xl font-semibold tracking-tight">Privacy Policy</h1>
      <p className="font-mono text-[11px] text-gray-400 mt-2 mb-10">last updated july 2026</p>

      <Section title="Overview">
        <p>LightAPI is an open-source public API directory and monitoring tool. This policy explains what data is collected when you use LightAPI, how it is stored, and how it is used. LightAPI does not sell, share, or monetize any data.</p>
      </Section>

      <Section title="What we collect">
        <ul className="list-disc list-inside space-y-1">
          <li>URLs you add to the dashboard for monitoring</li>
          <li>Latency readings, HTTP status codes, and uptime records for those URLs</li>
          <li>Webhook URLs you optionally provide for alerts</li>
          <li>GitHub repository names if you configure deploy tracking</li>
        </ul>
        <p>We do not collect names, email addresses, passwords, payment information, or any other personally identifiable information.</p>
      </Section>

      <Section title="How data is used">
        <p>Collected data is used solely to power the monitoring dashboard — displaying latency charts, anomaly detection, incident logs, and deploy tracking. No data is used for advertising, analytics, or any purpose outside of the monitoring functionality you configured.</p>
      </Section>

      <Section title="Data storage">
        <p>All monitoring data is stored in a SQLite database on the backend server (hosted on Render). Trained LSTM model weights are stored on the same server. No data is sent to third-party analytics or data platforms.</p>
        <p>The backend runs on a free hosting tier without a persistent disk, so monitoring data may be cleared when the service restarts or redeploys. Don&rsquo;t rely on it as your only record of an endpoint&rsquo;s history.</p>
      </Section>

      <Section title="Third-party requests">
        <p>LightAPI makes outbound HTTP requests to the URLs you add in order to measure their latency and availability. These requests originate from the backend server and include a standard HTTP User-Agent header. No personal data is included in these requests.</p>
      </Section>

      <Section title="Webhooks">
        <p>If you configure a webhook URL for alerts, LightAPI will send POST requests to that URL containing endpoint name, latency values, and alert type. You are responsible for the security of any webhook endpoint you provide.</p>
      </Section>

      <Section title="Workspace links">
        <p>Workspaces have no accounts — access is the shareable link itself. Anyone who has your workspace link can view and edit that workspace, so only share it with people you trust.</p>
      </Section>

      <Section title="Open source">
        <p>LightAPI is fully open source. You can inspect the complete codebase, including all data handling logic, at <a href="https://github.com/LightAnd2/LightAPI" target="_blank" rel="noreferrer" className="text-msu-green hover:underline">github.com/LightAnd2/LightAPI</a>. You are free to self-host the backend for full control over your data.</p>
      </Section>
    </PageShell>
  )
}
