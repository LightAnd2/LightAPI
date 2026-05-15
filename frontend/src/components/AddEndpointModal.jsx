import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { api } from '../services/api'

export default function AddEndpointModal({ open, onClose, onAdded }) {
  const [form, setForm] = useState({
    url: '',
    name: '',
    check_interval: 30,
    alert_threshold: 500,
    webhook_url: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const ep = await api.createEndpoint({
        ...form,
        webhook_url: form.webhook_url || null,
        check_interval: Number(form.check_interval),
        alert_threshold: Number(form.alert_threshold),
      })
      onAdded(ep)
      onClose()
      setForm({ url: '', name: '', check_interval: 30, alert_threshold: 500, webhook_url: '' })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/20"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.15 }}
            className="relative bg-white rounded-xl border border-border shadow-card-hover w-full max-w-md"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h2 className="text-sm font-semibold text-gray-900">Start Monitoring</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={submit} className="px-5 py-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://api.example.com/health"
                  value={form.url}
                  onChange={(e) => set('url', e.target.value)}
                  className="w-full border border-border rounded-md px-3 py-2 text-sm font-mono placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-msu-green focus:border-msu-green"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="My API"
                  value={form.name}
                  onChange={(e) => set('name', e.target.value)}
                  className="w-full border border-border rounded-md px-3 py-2 text-sm placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-msu-green focus:border-msu-green"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Check Interval</label>
                  <div className="relative">
                    <input
                      type="number"
                      min={10}
                      max={300}
                      value={form.check_interval}
                      onChange={(e) => set('check_interval', e.target.value)}
                      className="w-full border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-msu-green focus:border-msu-green pr-8"
                    />
                    <span className="absolute right-2.5 top-2 text-xs text-gray-400">s</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Alert Threshold</label>
                  <div className="relative">
                    <input
                      type="number"
                      min={50}
                      value={form.alert_threshold}
                      onChange={(e) => set('alert_threshold', e.target.value)}
                      className="w-full border border-border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-msu-green focus:border-msu-green pr-10"
                    />
                    <span className="absolute right-2.5 top-2 text-xs text-gray-400">ms</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Webhook URL <span className="text-gray-400 font-normal">(optional)</span></label>
                <input
                  type="url"
                  placeholder="https://hooks.slack.com/..."
                  value={form.webhook_url}
                  onChange={(e) => set('webhook_url', e.target.value)}
                  className="w-full border border-border rounded-md px-3 py-2 text-sm font-mono placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-msu-green focus:border-msu-green"
                />
              </div>

              {error && <p className="text-xs text-status-down">{error}</p>}

              <div className="flex gap-2 pt-1">
                <button type="button" onClick={onClose} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-1 disabled:opacity-60">
                  {loading ? 'Starting…' : 'Start Monitoring'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
