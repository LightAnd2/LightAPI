import { useEffect } from 'react'

// Per-route <title>, meta description, and canonical URL. Google renders
// SPAs, so updating these client-side is enough for distinct search results.
export function usePageMeta(title, description) {
  useEffect(() => {
    document.title = title

    if (description) {
      const meta = document.querySelector('meta[name="description"]')
      if (meta) meta.setAttribute('content', description)
    }

    let canonical = document.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.rel = 'canonical'
      document.head.appendChild(canonical)
    }
    canonical.href = `https://lightapi.dev${window.location.pathname}`
  }, [title, description])
}
