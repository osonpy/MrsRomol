// components/BottomNav.jsx
import { useLocation, useNavigate } from 'react-router-dom'
import { useCartStore } from '../store/useCartStore'
import { t } from '../i18n'

const TABS = [
  { path: '/',        icon: '🛍️', labelKey: 'nav_catalog' },
  { path: '/cart',    icon: '🛒', labelKey: 'nav_cart',   showBadge: true },
  { path: '/orders',  icon: '📦', labelKey: 'nav_orders' },
  { path: '/profile', icon: '👤', labelKey: 'nav_profile' },
]

export function BottomNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const items = useCartStore((s) => s.items)
  const cartCount = items.reduce((sum, i) => sum + i.quantity, 0)

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 flex border-t"
      style={{
        background: 'var(--tg-theme-bg-color)',
        borderColor: 'var(--tg-theme-secondary-bg-color)',
        paddingBottom: 'env(safe-area-inset-bottom, 8px)',
      }}
    >
      {TABS.map((tab) => {
        const isActive =
          tab.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(tab.path)

        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className="flex-1 flex flex-col items-center py-2 gap-0.5 relative active:opacity-60 transition-opacity"
          >
            {/* Badge for cart */}
            {tab.showBadge && cartCount > 0 && (
              <span
                className="absolute top-1 right-1/4 min-w-[18px] h-[18px] rounded-full flex items-center justify-center text-xs font-bold px-1"
                style={{
                  background: 'var(--tg-theme-button-color)',
                  color: 'var(--tg-theme-button-text-color)',
                  fontSize: '10px',
                }}
              >
                {cartCount > 99 ? '99+' : cartCount}
              </span>
            )}

            <span
              className="text-xl leading-none transition-transform duration-150"
              style={{
                transform: isActive ? 'scale(1.1)' : 'scale(1)',
                filter: isActive ? 'none' : 'grayscale(0.3)',
              }}
            >
              {tab.icon}
            </span>
            <span
              className="text-xs font-medium transition-colors duration-150"
              style={{
                color: isActive
                  ? 'var(--tg-theme-button-color)'
                  : 'var(--tg-theme-hint-color)',
              }}
            >
              {t(tab.labelKey)}
            </span>
          </button>
        )
      })}
    </nav>
  )
}
