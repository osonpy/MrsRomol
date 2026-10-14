// Admin section shell: role guard, header with a way back to the shop, and
// its own bottom navigation. Admin screens are in Uzbek only for now.
import { Link, Navigate, NavLink, Outlet, useLocation } from 'react-router-dom'
import { BagIcon, GridIcon, PackageIcon, SlidersIcon } from '../../components/icons'
import { useMeta } from '../../hooks/queries'

const TABS = [
  { to: '/admin', label: 'Panel', icon: GridIcon, end: true },
  { to: '/admin/orders', label: 'Buyurtmalar', icon: PackageIcon },
  { to: '/admin/products', label: 'Mahsulotlar', icon: BagIcon },
  { to: '/admin/more', label: 'Boshqa', icon: SlidersIcon },
]

const ADMIN_TAB_PATHS = TABS.map((t) => t.to)

export function AdminHeader({ title, right }) {
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-3 bg-cream/95 px-4 pb-3 pt-4 backdrop-blur">
      <h1 className="font-serif text-[28px] font-semibold leading-none text-ink">{title}</h1>
      {right}
    </header>
  )
}

export default function AdminLayout() {
  const { data: meta } = useMeta()
  const { pathname } = useLocation()
  if (!['admin', 'super_admin'].includes(meta?.me?.role)) return <Navigate to="/" replace />
  // Detail pages have their own action bar at the bottom (and Telegram's Back).
  const showNav = ADMIN_TAB_PATHS.includes(pathname)

  return (
    <div className={`min-h-dvh ${showNav ? 'pb-[calc(4.5rem+env(safe-area-inset-bottom))]' : ''}`}>
      <div className="flex items-center justify-between bg-ink px-4 py-2 text-xs text-cream">
        <span className="font-semibold uppercase tracking-widest">Admin</span>
        <Link to="/" className="font-semibold underline-offset-2 active:underline">
          ← Doʻkonga qaytish
        </Link>
      </div>
      <Outlet />
      {showNav && (
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-rose-100 bg-cream/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
        <div className="grid h-16 grid-cols-4">
          {TABS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium ${isActive ? 'text-rose-700' : 'text-ink-faint'}`
              }
            >
              <Icon className="h-6 w-6" />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
      )}
    </div>
  )
}
