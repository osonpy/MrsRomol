import { Link } from 'react-router-dom'
import { ChevronRightIcon, ClockIcon, PackageIcon, TruckIcon } from '../../components/icons'
import { ErrorState, Skeleton } from '../../components/ui'
import { useDashboard } from '../../hooks/admin'
import { money } from './uz'
import { AdminHeader } from './AdminLayout'

function ActionCard({ to, icon: Icon, count, label, tone }) {
  const tones = {
    urgent: 'bg-rose-600 text-white',
    calm: 'bg-white text-ink',
  }
  const active = count > 0
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 rounded-2xl p-4 shadow-card active:scale-[0.99] ${active ? tones[tone] : tones.calm}`}
    >
      <Icon className={`h-7 w-7 shrink-0 ${active && tone === 'urgent' ? '' : 'text-rose-500'}`} />
      <span className="flex-1 text-[15px] font-medium">{label}</span>
      <span className="text-2xl font-bold tabular-nums">{count}</span>
      <ChevronRightIcon className="h-4 w-4 opacity-60" />
    </Link>
  )
}

export default function DashboardPage() {
  const { data, isPending, isError, error, refetch } = useDashboard()

  return (
    <div>
      <AdminHeader title="Panel" />
      {isPending ? (
        <div className="space-y-3 px-4">
          <Skeleton className="h-24 w-full rounded-2xl" />
          <Skeleton className="h-16 w-full rounded-2xl" />
          <Skeleton className="h-16 w-full rounded-2xl" />
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <div className="space-y-3 px-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="card p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Bugun buyurtma</p>
              <p className="mt-1 text-3xl font-bold tabular-nums">{data.today.orders}</p>
            </div>
            <div className="card p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Bugungi tushum</p>
              <p className="mt-1 text-xl font-bold tabular-nums text-rose-700">{money(data.today.revenue)}</p>
            </div>
          </div>

          <ActionCard to="/admin/orders?status=payment_review" icon={PackageIcon} count={data.to_review} label="Chekni tekshirish kerak" tone="urgent" />
          <ActionCard to="/admin/orders?status=confirmed" icon={TruckIcon} count={data.to_ship} label="Yuborish kerak" tone="urgent" />
          <ActionCard to="/admin/orders?status=awaiting_payment" icon={ClockIcon} count={data.awaiting_payment} label="Toʻlov kutilmoqda" tone="calm" />

          <section className="card p-4">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-ink-soft">Tugayotgan mahsulotlar</h2>
            {data.low_stock.length === 0 ? (
              <p className="text-sm text-ink-soft">Hammasi yetarli 👍</p>
            ) : (
              <ul className="divide-y divide-rose-100">
                {data.low_stock.map((v) => (
                  <li key={v.id}>
                    <Link to={`/admin/products/${v.product.id}`} className="flex items-center justify-between py-2.5 text-sm">
                      <span className="min-w-0 flex-1 truncate">
                        {v.product.name_uz}
                        <span className="text-ink-soft"> {[v.color_uz, v.size].filter(Boolean).join(' · ')}</span>
                      </span>
                      <span className={`ml-3 rounded-full px-2.5 py-0.5 text-xs font-bold ${v.stock === 0 ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                        {v.stock === 0 ? 'Tugadi' : `${v.stock} dona`}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
