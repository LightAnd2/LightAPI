import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Explore from './pages/Explore'

// Code-split the heavy routes (charts, dashboard) so they don't load on the
// discovery home. Explore stays eager since it's the entry point.
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Privacy = lazy(() => import('./pages/Privacy'))

export default function App() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-base" />}>
      <Routes>
        <Route path="/" element={<Explore />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/:endpointId" element={<Dashboard />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </Suspense>
  )
}
