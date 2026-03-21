import { Link, useLocation } from 'react-router-dom'
import { Landmark, Search, Upload, BarChart3, MessageSquare } from 'lucide-react'
import clsx from 'clsx'

const links = [
  { to: '/', label: 'Feed', icon: Landmark },
  { to: '/ask', label: 'Ask', icon: MessageSquare },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center
                           group-hover:bg-brand-700 transition-colors">
              <Landmark className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900 tracking-tight">
              Civic<span className="text-brand-600">Lens</span>
            </span>
          </Link>

          {/* Nav links */}
          <nav className="hidden sm:flex items-center gap-1">
            {links.map(({ to, label, icon: Icon }) => {
              const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
              return (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors',
                    active
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              )
            })}
          </nav>

          {/* Mobile nav */}
          <nav className="flex sm:hidden items-center gap-1">
            {links.map(({ to, label, icon: Icon }) => {
              const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
              return (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'p-2 rounded-lg transition-colors',
                    active ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:bg-gray-100'
                  )}
                  title={label}
                >
                  <Icon className="w-5 h-5" />
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </header>
  )
}
