const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  if (res.status === 204) return null
  return res.json()
}

// ---- Workspace resolution ----------------------------------------------
// Every visitor gets their own workspace (the shareable-link model):
//   1. ?ws=<id> in the URL wins — opening a shared link views that workspace
//      for the rest of the session without overwriting your own.
//   2. Otherwise the id saved in localStorage is used.
//   3. First-time visitors get a fresh id minted by the backend.

let sessionWs = null

function urlWorkspace() {
  const param = new URLSearchParams(window.location.search).get('ws')
  if (param) sessionWs = param
  return sessionWs
}

let mintPromise = null

async function currentWorkspace() {
  const fromUrl = urlWorkspace()
  if (fromUrl) return fromUrl
  const stored = localStorage.getItem('lightai_ws')
  if (stored) return stored
  if (!mintPromise) {
    mintPromise = request('/api/workspaces', { method: 'POST' })
      .then((d) => {
        localStorage.setItem('lightai_ws', d.id)
        return d.id
      })
      .catch((e) => {
        mintPromise = null // retry on next call once the backend is reachable
        throw e
      })
  }
  return mintPromise
}

async function scoped(path, options) {
  const ws = await currentWorkspace()
  const sep = path.includes('?') ? '&' : '?'
  return request(`${path}${sep}workspace=${encodeURIComponent(ws)}`, options)
}

export const api = {
  // Workspace-scoped
  getEndpoints: (workspace) =>
    workspace
      ? request(`/api/endpoints?workspace=${encodeURIComponent(workspace)}`)
      : scoped('/api/endpoints'),
  createEndpoint: (body) => scoped('/api/endpoints', { method: 'POST', body: JSON.stringify(body) }),
  getGlobalStats: () => scoped('/api/stats'),
  getWorkspace: () => currentWorkspace(),

  // Addressed by unguessable endpoint id — no workspace needed
  getEndpoint: (id) => request(`/api/endpoints/${id}`),
  deleteEndpoint: (id) => request(`/api/endpoints/${id}`, { method: 'DELETE' }),
  getReadings: (id, range = '24h') => request(`/api/endpoints/${id}/readings?range=${range}`),
  getIncidents: (id) => request(`/api/endpoints/${id}/incidents`),
  getAnomalies: (id) => request(`/api/endpoints/${id}/anomalies`),
  getStats: (id) => request(`/api/endpoints/${id}/stats`),
  getPredictions: (id, steps = 30) => request(`/api/endpoints/${id}/predictions?steps=${steps}`),
  getDeploys: (id) => request(`/api/endpoints/${id}/deploys`),
}
