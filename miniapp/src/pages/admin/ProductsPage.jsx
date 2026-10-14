import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BagIcon, ChevronRightIcon, PlusIcon, SearchIcon } from '../../components/icons'
import { ProductImage } from '../../components/product'
import { Button, EmptyState, ErrorState, Skeleton } from '../../components/ui'
import { useAdminProducts } from '../../hooks/admin'
import { money } from './uz'
import { AdminHeader } from './AdminLayout'

export default function AdminProductsPage() {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [q, setQ] = useState('')
  useEffect(() => {
    const id = setTimeout(() => setQ(text.trim()), 350)
    return () => clearTimeout(id)
  }, [text])
  const { data, isPending, isError, error, refetch } = useAdminProducts({ q })

  return (
    <div>
      <AdminHeader
        title="Mahsulotlar"
        right={
          <Button className="h-10 px-4 text-sm" onClick={() => navigate('/admin/products/new')}>
            <PlusIcon className="h-5 w-5" /> Qoʻshish
          </Button>
        }
      />
      <label className="relative mx-4 mb-3 block">
        <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
        <input
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Nomi boʻyicha qidirish"
          className="h-11 w-full rounded-full border border-rose-200 bg-white pl-11 pr-4 text-[15px] outline-none focus:border-rose-400"
        />
      </label>

      {isPending ? (
        <div className="space-y-2 px-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.products.length === 0 ? (
        <EmptyState
          icon={BagIcon}
          title={q ? 'Topilmadi' : 'Hali mahsulot yoʻq'}
          text={q ? undefined : 'Birinchi mahsulotingizni qoʻshing'}
          action={!q && <Button onClick={() => navigate('/admin/products/new')}>Mahsulot qoʻshish</Button>}
        />
      ) : (
        <ul className="space-y-2 px-4">
          {data.products.map((p) => {
            const noPhotos = p.images.length === 0
            const noVariants = p.variants.length === 0
            return (
              <li key={p.id}>
                <Link to={`/admin/products/${p.id}`} className="card flex items-center gap-3 p-2.5 active:bg-rose-50/50">
                  <ProductImage image={p.images[0] ?? null} alt="" className="h-16 w-12 shrink-0 rounded-lg" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[15px] font-medium">{p.name_uz}</p>
                    <p className="text-sm text-rose-700">{money(p.price)}</p>
                    <div className="mt-0.5 flex flex-wrap gap-1.5 text-[11px] font-semibold">
                      {!p.is_active && <span className="rounded bg-stone-200 px-1.5 py-0.5 text-stone-700">Yashirin</span>}
                      {noPhotos && <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-800">Rasm yoʻq</span>}
                      {noVariants ? (
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-800">Variant yoʻq</span>
                      ) : (
                        <span className={`rounded px-1.5 py-0.5 ${p.total_stock === 0 ? 'bg-red-100 text-red-800' : 'bg-rose-50 text-ink-soft'}`}>
                          {p.total_stock} dona
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRightIcon className="h-4 w-4 shrink-0 text-ink-faint" />
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
