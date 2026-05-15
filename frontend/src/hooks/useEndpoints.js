import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

export function useEndpoints() {
  const [endpoints, setEndpoints] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    try {
      const data = await api.getEndpoints()
      setEndpoints(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, 15000)
    return () => clearInterval(id)
  }, [fetch])

  const updateEndpoint = useCallback((id, patch) => {
    setEndpoints((prev) => prev.map((ep) => (ep.id === id ? { ...ep, ...patch } : ep)))
  }, [])

  const addEndpoint = useCallback((ep) => {
    setEndpoints((prev) => [ep, ...prev])
  }, [])

  const removeEndpoint = useCallback((id) => {
    setEndpoints((prev) => prev.filter((ep) => ep.id !== id))
  }, [])

  return { endpoints, loading, error, refetch: fetch, updateEndpoint, addEndpoint, removeEndpoint }
}
