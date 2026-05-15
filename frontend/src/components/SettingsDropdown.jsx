import { useState, useRef, useEffect } from 'react'
import { Settings, Trash2, ExternalLink } from 'lucide-react'
import { api } from '../services/api'

export default function SettingsDropdown({ activeEndpoint, onDeleted }) {
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
        setConfirming(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const handleDelete = async () => {
    if (!confirming) { setConfirming(true); return }
    setDeleting(true)
    try {
      await api.deleteEndpoint(activeEndpoint.id)
      onDeleted(activeEndpoint.id)
      setOpen(false)
      setConfirming(false)
    } catch {}
    setDeleting(false)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => { setOpen(o => !o); setConfirming(false) }}
        className={`p-1.5 rounded transition-colors ${open ? 'bg-gray-100 text-gray-700' : 'text-gray-400 hover:text-gray-600'}`}
      >
        <Settings size={16} />
      </button>

      {open && (
        <div className="absolute right-0 top-8 w-52 bg-white border border-border rounded-lg shadow-card-hover z-50 py-1">
          {activeEndpoint ? (
            <>
              <div className="px-3 py-2 border-b border-border">
                <p className="text-xs font-medium text-gray-900 truncate">{activeEndpoint.name}</p>
                <p className="text-xs text-gray-400 font-mono truncate">{activeEndpoint.url}</p>
              </div>
              <a
                href={activeEndpoint.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
                onClick={() => setOpen(false)}
              >
                <ExternalLink size={13} />
                Open URL
              </a>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className={`w-full flex items-center gap-2 px-3 py-2 text-xs transition-colors ${
                  confirming
                    ? 'text-status-down bg-red-50 hover:bg-red-100'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Trash2 size={13} />
                {deleting ? 'Removing…' : confirming ? 'Click again to confirm' : 'Remove endpoint'}
              </button>
            </>
          ) : (
            <p className="px-3 py-2 text-xs text-gray-400">No endpoint selected</p>
          )}
        </div>
      )}
    </div>
  )
}
