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

export const api = {
  getEndpoints: () => request('/api/endpoints'),
  getEndpoint: (id) => request(`/api/endpoints/${id}`),
  createEndpoint: (body) => request('/api/endpoints', { method: 'POST', body: JSON.stringify(body) }),
  deleteEndpoint: (id) => request(`/api/endpoints/${id}`, { method: 'DELETE' }),
  getReadings: (id, range = '24h') => request(`/api/endpoints/${id}/readings?range=${range}`),
  getIncidents: (id) => request(`/api/endpoints/${id}/incidents`),
  getAnomalies: (id) => request(`/api/endpoints/${id}/anomalies`),
  getStats: (id) => request(`/api/endpoints/${id}/stats`),
  getPredictions: (id, steps = 30) => request(`/api/endpoints/${id}/predictions?steps=${steps}`),
  getGlobalStats: () => request('/api/stats'),
  getDeploys: (id) => request(`/api/endpoints/${id}/deploys`),
}
