import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ChevronRightIcon, PackageIcon, SearchIcon } from '../../components/icons'
import { StatusBadge } from '../../components/order'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui'
import { useAdminOrders } from '../../hooks/admin'
import { phone } from '../../lib/format'
import { dateTime, money } from './uz'
import { AdminHeader } from './AdminLayout'

const FILTERS = [
  ['', 'Hammasi'],
  ['payment_review', 'Chek keldi'],
  ['confirmed', 'Yuborish kerak'],
  ['awaiting_payment', 'Toʻlov kutilmoqda'],
  ['shipped', 'Yoʻlda'],
  ['delivered', 'Yetkazildi'],
  ['cancelled', 'Bekor'],
]

export default function AdminOrdersPage() {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') || ''
  const [text, setText] = useState(params.get('q') || '')
  const q = params.get('q') || ''

  // Search 400 ms after typing stops.
  useEffect(() => {
    if (text === q) return
    const id = setTimeout(() => setParams((p) => (text ? p.set('q', text) : p.delete('q'), p), { replace: true }), 400)
    return () => clearTimeout(id)
  }, [text, q, setParams])

  const { data, isPending, isError, error, refetch, isFetching } = useAdminOrders({ status, q })

  return (
    <div>
      <AdminHeader title="Buyurtmalar" />
      <div className="sticky top-[60px] z-10 space-y-3 bg-cream/95 pb-3 backdrop-blur">
        <label className="relative mx-4 block">
          <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
          <input
            type="search"
            inputMode="search"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Raqam (#1024) yoki telefon"
            className="h-11 w-full rounded-full border border-rose-200 bg-white pl-11 pr-4 text-[15px] outline-none focus:border-rose-400"
          />
        </label>
        <div className="no-scrollbar flex gap-2 overflow-x-auto px-4">
          {FILTERS.map(([value, label]) => (
            <button
              key={value || 'all'}
              type="button"
              onClick={() => setParams((p) => (value ? p.set('status', value) : p.delete('status'), p), { replace: true })}
              className={`chip ${status === value ? 'border-ink bg-ink text-cream' : 'border-rose-200 bg-white text-ink'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {isPending ? (
        <div className="space-y-3 px-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.orders.length === 0 ? (
        <EmptyState icon={PackageIcon} title="Buyurtma yoʻq" text={q ? 'Qidiruv boʻyicha topilmadi' : 'Bu boʻlimda hozircha boʻsh'} />
      ) : (
        <ul className={`space-y-3 px-4 transition-opacity ${isFetching ? 'opacity-60' : ''}`}>
          {data.orders.map((o) => (
            <li key={o.id}>
              <Link to={`/admin/orders/${o.id}`} className="card block p-4 active:bg-rose-50/50">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-lg font-bold leading-none">#{o.number}</p>
                    <p className="mt-1 truncate text-sm text-ink">
                      {o.contact_name} · <span className="text-ink-soft">{phone(o.contact_phone)}</span>
                    </p>
                  </div>
                  <StatusBadge status={o.status} lng="uz" />
                </div>
                <div className="mt-2 flex items-center justify-between text-sm">
                  <span className="text-ink-soft">
                    {dateTime(o.created_at)} · {o.items_count} dona
                  </span>
                  <span className="flex items-center gap-1 font-semibold text-rose-700">
                    {money(o.total)}
                    <ChevronRightIcon className="h-4 w-4 text-ink-faint" />
                  </span>
                </div>
              </Link>
            </li>
          ))}
          {data.total > data.orders.length && (
            <p className="py-2 text-center text-xs text-ink-soft">
              Oxirgi {data.orders.length} ta koʻrsatildi (jami {data.total}). Aniqroq qidiring.
            </p>
          )}
        </ul>
      )}
    </div>
  )
}
