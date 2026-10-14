import { lazy, Suspense, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouterProvider,
  ScrollRestoration,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import { TabLayout } from './components/layout'
import { Button, ErrorState, Spinner, Toaster } from './components/ui'
import { useMeta } from './hooks/queries'
import { backButton, startParam } from './lib/telegram'
import CatalogPage from './pages/CatalogPage'

const ProductPage = lazy(() => import('./pages/ProductPage'))
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'))
const CartPage = lazy(() => import('./pages/CartPage'))
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'))
const OrdersPage = lazy(() => import('./pages/OrdersPage'))
const OrderPage = lazy(() => import('./pages/OrderPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const AdminSoonPage = lazy(() => import('./pages/AdminSoonPage'))

const TAB_PATHS = ['/', '/favorites', '/cart', '/orders', '/profile']

// Telegram's native Back button on every page that is not a main tab.
function BackButtonController() {
  const { pathname, key } = useLocation()
  const navigate = useNavigate()
  useEffect(() => {
    if (TAB_PATHS.includes(pathname)) return
    // Opened straight on a deep link (from a notification): there is no
    // history to go back to, so go to the catalogue instead.
    const canGoBack = key !== 'default'
    return backButton.show(() => (canGoBack ? navigate(-1) : navigate('/', { replace: true })))
  }, [pathname, key, navigate])
  return null
}

// Notification buttons open the app with ?startapp=order_<id>.
function startRoute() {
  const m = /^(admin_)?order_([0-9a-f-]{36})$/.exec(startParam)
  if (!m) return null
  return m[1] ? `/admin/orders/${m[2]}` : `/orders/${m[2]}`
}

function PageFallback() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center text-rose-400">
      <Spinner />
    </div>
  )
}

function Splash() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 px-10">
      <img src="/logo.webp" alt="Mrs Romol" className="w-64 animate-fade-in" />
      <Spinner className="h-6 w-6 text-rose-400" />
    </div>
  )
}

function Root() {
  const meta = useMeta()

  if (meta.isPending) return <Splash />
  if (meta.isError) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center">
        <img src="/logo.webp" alt="Mrs Romol" className="w-56" />
        <ErrorState error={meta.error} onRetry={() => meta.refetch()} />
      </div>
    )
  }
  return (
    <>
      <BackButtonController />
      <ScrollRestoration />
      <Toaster />
      <Suspense fallback={<PageFallback />}>
        <Outlet />
      </Suspense>
    </>
  )
}

function NotFound() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-8 text-center">
      <p className="font-serif text-2xl">{t('not_found')}</p>
      <Button variant="outline" onClick={() => navigate('/', { replace: true })}>
        {t('common.back_home')}
      </Button>
    </div>
  )
}

const router = createBrowserRouter([
  {
    element: <Root />,
    children: [
      {
        element: <TabLayout />,
        children: [
          { index: true, element: startRoute() ? <Navigate to={startRoute()} replace /> : <CatalogPage /> },
          { path: 'favorites', element: <FavoritesPage /> },
          { path: 'cart', element: <CartPage /> },
          { path: 'orders', element: <OrdersPage /> },
          { path: 'profile', element: <ProfilePage /> },
        ],
      },
      { path: 'product/:id', element: <ProductPage /> },
      { path: 'checkout', element: <CheckoutPage /> },
      { path: 'orders/:id', element: <OrderPage /> },
      { path: 'admin/*', element: <AdminSoonPage /> },
      { path: '*', element: <NotFound /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
