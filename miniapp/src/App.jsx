import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './i18n'
import { useTelegram } from './hooks/useTelegram'
import { useUserStore } from './store/userStore'
import { customersApi } from './api/customers'
import { BottomNav } from './components/layout/BottomNav'
import { Spinner } from './components/ui/Spinner'

const CatalogPage = lazy(() => import('./pages/CatalogPage'))
const ProductPage  = lazy(() => import('./pages/ProductPage'))
const CartPage     = lazy(() => import('./pages/CartPage'))
const OrdersPage   = lazy(() => import('./pages/OrdersPage'))
const ProfilePage  = lazy(() => import('./pages/ProfilePage'))

if (import.meta.env.DEV && !window.Telegram?.WebApp) {
  window.Telegram = {
    WebApp: {
      initData: 'mock_init_data_for_dev',
      initDataUnsafe: {
        user: {
          id: 123456789,
          first_name: 'Test',
          last_name: 'User',
          username: 'testuser',
          language_code: 'uz',
        },
      },
      colorScheme: 'light',
      themeParams: {},
      ready: () => {},
      expand: () => {},
      setHeaderColor: () => {},
      MainButton: { show: () => {}, hide: () => {}, setText: () => {}, onClick: () => {}, offClick: () => {} },
      BackButton:  { show: () => {}, hide: () => {}, onClick: () => {}, offClick: () => {} },
    },
  }
}

function PageFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen" style={{ color: 'var(--tg-theme-hint-color)' }}>
      <Spinner size="lg" />
    </div>
  )
}

export default function App() {
  const { tg, user } = useTelegram()
  const { setTelegramUser, setCustomer, setLoading } = useUserStore()

  useEffect(() => {
    const themeParams = tg?.themeParams
    if (!themeParams || Object.keys(themeParams).length === 0) return
    const root = document.documentElement
    const map = {
      bg_color:           '--tg-theme-bg-color',
      text_color:         '--tg-theme-text-color',
      hint_color:         '--tg-theme-hint-color',
      link_color:         '--tg-theme-link-color',
      button_color:       '--tg-theme-button-color',
      button_text_color:  '--tg-theme-button-text-color',
      secondary_bg_color: '--tg-theme-secondary-bg-color',
    }
    Object.entries(map).forEach(([tgKey, cssVar]) => {
      if (themeParams[tgKey]) root.style.setProperty(cssVar, themeParams[tgKey])
    })
  }, [tg])

  useEffect(() => {
    if (!user) return
    setTelegramUser(user)
    setLoading(true)

    const lang = ['uz', 'ru', 'en'].includes(user.language_code) ? user.language_code : 'uz'

    customersApi
      .register({
        telegram_id: String(user.id),
        full_name: [user.first_name, user.last_name].filter(Boolean).join(' ') || 'User',
        phone: '',
        language: lang,
      })
      .then((customer) => {
        setCustomer(customer)
        import('./i18n').then(({ default: i18n }) => i18n.changeLanguage(customer.language))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user?.id])

  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-dvh" style={{ background: 'var(--tg-theme-bg-color)' }}>
        <main className="flex-1 overflow-hidden">
          <Suspense fallback={<PageFallback />}>
            <Routes>
              <Route path="/"            element={<CatalogPage />} />
              <Route path="/product/:id" element={<ProductPage />} />
              <Route path="/cart"        element={<CartPage />} />
              <Route path="/orders"      element={<OrdersPage />} />
              <Route path="/profile"     element={<ProfilePage />} />
            </Routes>
          </Suspense>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
