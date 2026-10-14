import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronRightIcon, ClockIcon, PackageIcon } from '../components/icons'
import { StatusBadge } from '../components/order'
import { Button, EmptyState, ErrorState, PageTitle, Skeleton } from '../components/ui'
import { useOrders } from '../hooks/queries'
import { dateTime, money, pick } from '../lib/format'

export default function OrdersPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data, isPending, isError, error, refetch } = useOrders()

  return (
    <div>
      <PageTitle>{t('orders.title')}</PageTitle>
      {isPending ? (
        <div className="space-y-3 px-4">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.orders.length === 0 ? (
        <EmptyState
          icon={PackageIcon}
          title={t('orders.empty_title')}
          text={t('orders.empty_text')}
          action={<Button onClick={() => navigate('/')}>{t('cart.to_catalog')}</Button>}
        />
      ) : (
        <ul className="space-y-3 px-4">
          {data.orders.map((o) => {
            const count = o.items.reduce((n, i) => n + i.quantity, 0)
            return (
              <li key={o.id}>
                <Link to={`/orders/${o.id}`} className="card block p-4 active:bg-rose-50/50">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-bold leading-none tracking-tight">#{o.number}</p>
                      <p className="mt-1 text-xs text-ink-soft">{dateTime(o.created_at)}</p>
                    </div>
                    <StatusBadge status={o.status} />
                  </div>
                  <p className="mt-3 line-clamp-1 text-sm text-ink-soft">
                    {o.items.map((i) => pick({ name_uz: i.product_name_uz, name_ru: i.product_name_ru }, 'name')).join(', ')}
                  </p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm text-ink-soft">{t('orders.items_count', { count })}</span>
                    <span className="flex items-center gap-1 font-semibold text-rose-700">
                      {money(o.total)}
                      <ChevronRightIcon className="h-4 w-4 text-ink-faint" />
                    </span>
                  </div>
                  {o.status === 'awaiting_payment' && (
                    <p className="mt-3 flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
                      <ClockIcon className="h-4 w-4" />
                      {t('order.pay_step2')}
                    </p>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
