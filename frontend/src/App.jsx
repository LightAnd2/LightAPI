import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Landing from './pages/Landing'

// Code-split the heavy routes (charts, dashboard) so they don't load on the
// landing page. Landing stays eager since it's the entry point.
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Privacy = lazy(() => import('./pages/Privacy'))

export default function App() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-base" />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/:endpointId" element={<Dashboard />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </Suspense>
  )
}
