import { useTranslation } from 'react-i18next'
import { NavLink, Outlet } from 'react-router-dom'
import { useCartCount } from '../store/cart'
import { BagIcon, GridIcon, HeartIcon, PackageIcon, UserIcon } from './icons'

const TABS = [
  { to: '/', icon: GridIcon, label: 'nav.catalog', end: true },
  { to: '/favorites', icon: HeartIcon, label: 'nav.favorites' },
  { to: '/cart', icon: BagIcon, label: 'nav.cart', badge: true },
  { to: '/orders', icon: PackageIcon, label: 'nav.orders' },
  { to: '/profile', icon: UserIcon, label: 'nav.profile' },
]

function BottomNav() {
  const { t } = useTranslation()
  const count = useCartCount()
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-rose-100 bg-cream/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      <div className="grid h-16 grid-cols-5">
        {TABS.map(({ to, icon: Icon, label, end, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition ${
                isActive ? 'text-rose-700' : 'text-ink-faint'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className="relative">
                  <Icon className={`h-6 w-6 ${isActive ? 'stroke-[2.1]' : ''}`} />
                  {badge && count > 0 && (
                    <span className="absolute -right-2.5 -top-1.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white">
                      {count > 99 ? '99+' : count}
                    </span>
                  )}
                </span>
                {t(label)}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}

// Tab pages: content + bottom navigation.
export function TabLayout() {
  return (
    <div className="min-h-dvh pb-[calc(4.5rem+env(safe-area-inset-bottom))]">
      <Outlet />
      <BottomNav />
    </div>
  )
}
