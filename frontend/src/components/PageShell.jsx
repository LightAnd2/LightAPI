import { Link } from 'react-router-dom'

function Logo({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="text-msu-green">
      <polyline points="2,14 5,14 7,6 9,20 11,11 13,9 15,15 17,14 22,14"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// Directory-style chrome for static pages (about, privacy).
export default function PageShell({ crumb, children }) {
  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-12 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <Logo />
            <span className="text-sm font-bold tracking-tight">LightAPI</span>
            <span className="hidden sm:inline text-xs text-gray-400 font-mono ml-1">/ {crumb}</span>
          </Link>
          <Link to="/dashboard" className="text-xs font-mono text-gray-500 hover:text-gray-900 transition-colors">
            dashboard →
          </Link>
        </div>
      </header>

      <main className="max-w-2xl w-full mx-auto px-6 py-12 flex-1">
        {children}
      </main>

      <footer className="border-t border-border mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between font-mono text-[11px] text-gray-400">
          <span>© {new Date().getFullYear()} LightAPI</span>
          <span className="hidden sm:inline">data · public-apis</span>
          <span className="flex items-center gap-3">
            <Link to="/about" className="hover:text-gray-700 transition-colors">about</Link>
            <Link to="/privacy" className="hover:text-gray-700 transition-colors">privacy</Link>
          </span>
        </div>
      </footer>
    </div>
  )
}
