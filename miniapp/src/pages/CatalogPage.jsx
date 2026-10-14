import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import { SearchIcon, SlidersIcon, XIcon } from '../components/icons'
import { ProductGrid, ProductGridSkeleton } from '../components/product'
import { Button, EmptyState, ErrorState, Sheet } from '../components/ui'
import { useMeta, useProducts } from '../hooks/queries'
import { pick } from '../lib/format'
import { haptic } from '../lib/telegram'
import { BagIcon } from '../components/icons'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL']
const SORTS = ['new', 'price_asc', 'price_desc']

// Filters live in the URL so Back from a product returns to the same list.
function useFilters() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(
    () => ({
      q: params.get('q') || '',
      category_id: params.get('category_id') || '',
      sort: params.get('sort') || 'new',
      size: params.get('size') || '',
      min_price: params.get('min_price') || '',
      max_price: params.get('max_price') || '',
    }),
    [params],
  )
  const update = useCallback(
    (patch) => {
      const next = { ...filters, ...patch }
      setParams(Object.fromEntries(Object.entries(next).filter(([k, v]) => v && !(k === 'sort' && v === 'new'))), {
        replace: true,
      })
    },
    [filters, setParams],
  )
  return [filters, update]
}

function SearchBox({ value, onChange }) {
  const { t } = useTranslation()
  const [text, setText] = useState(value)
  useEffect(() => {
    setText(value)
  }, [value])
  // Search 350 ms after the user stops typing.
  useEffect(() => {
    if (text === value) return
    const id = setTimeout(() => onChange(text.trim()), 350)
    return () => clearTimeout(id)
  }, [text, value, onChange])

  return (
    <label className="relative block flex-1">
      <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
      <input
        type="search"
        enterKeyHint="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
        placeholder={t('catalog.search')}
        className="h-11 w-full rounded-full border border-rose-200 bg-white pl-11 pr-10 text-[15px] outline-none placeholder:text-ink-faint focus:border-rose-400"
      />
      {text && (
        <button
          type="button"
          aria-label="clear"
          onClick={() => setText('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1.5 text-ink-faint"
        >
          <XIcon className="h-4 w-4" />
        </button>
      )}
    </label>
  )
}

function FilterSheet({ open, onClose, filters, onApply }) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState(filters)
  useEffect(() => {
    if (open) setDraft(filters)
  }, [open, filters])
  const set = (patch) => setDraft((d) => ({ ...d, ...patch }))

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={t('catalog.filters')}
      footer={
        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={() => set({ sort: 'new', size: '', min_price: '', max_price: '' })}>
            {t('catalog.reset')}
          </Button>
          <Button className="flex-[2]" onClick={() => (onApply(draft), onClose())}>
            {t('catalog.apply')}
          </Button>
        </div>
      }
    >
      <h3 className="label">{t('catalog.sort')}</h3>
      <div className="mb-6 flex flex-wrap gap-2">
        {SORTS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => set({ sort: s })}
            className={`chip ${draft.sort === s ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
          >
            {t(`catalog.sort_${s}`)}
          </button>
        ))}
      </div>

      <h3 className="label">{t('catalog.size')}</h3>
      <div className="mb-6 flex flex-wrap gap-2">
        {SIZES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => set({ size: draft.size === s ? '' : s })}
            className={`chip min-w-[3rem] justify-center ${
              draft.size === s ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <h3 className="label">
        {t('catalog.price')}, {t('common.currency')}
      </h3>
      <div className="flex items-center gap-3">
        <input
          inputMode="numeric"
          className="field"
          placeholder={t('catalog.price_from')}
          value={draft.min_price}
          onChange={(e) => set({ min_price: e.target.value.replace(/\D/g, '') })}
        />
        <span className="text-ink-faint">—</span>
        <input
          inputMode="numeric"
          className="field"
          placeholder={t('catalog.price_to')}
          value={draft.max_price}
          onChange={(e) => set({ max_price: e.target.value.replace(/\D/g, '') })}
        />
      </div>
    </Sheet>
  )
}

export default function CatalogPage() {
  const { t } = useTranslation()
  const { data: meta } = useMeta()
  const [filters, update] = useFilters()
  const [filterOpen, setFilterOpen] = useState(false)
  const products = useProducts(filters)

  const items = products.data?.pages.flatMap((p) => p.products) ?? []
  const activeFilters = ['size', 'min_price', 'max_price'].filter((k) => filters[k]).length + (filters.sort !== 'new' ? 1 : 0)
  const searching = Boolean(filters.q || filters.category_id || activeFilters)
  const onSearch = useCallback((q) => update({ q }), [update])

  return (
    <div>
      <header className="sticky top-0 z-20 bg-cream/95 pb-3 backdrop-blur">
        <div className="flex justify-center pt-3">
          <img src="/logo.webp" alt="Mrs Romol" className="h-14 w-auto" />
        </div>
        <div className="mt-2 flex items-center gap-2 px-4">
          <SearchBox value={filters.q} onChange={onSearch} />
          <button
            type="button"
            aria-label={t('catalog.filters')}
            onClick={() => setFilterOpen(true)}
            className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-rose-200 bg-white text-ink active:bg-rose-50"
          >
            <SlidersIcon className="h-5 w-5" />
            {activeFilters > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white">
                {activeFilters}
              </span>
            )}
          </button>
        </div>
        {meta?.categories?.length > 0 && (
          <div className="no-scrollbar mt-3 flex gap-2 overflow-x-auto px-4">
            {[{ id: '', name_uz: t('catalog.all'), name_ru: t('catalog.all') }, ...meta.categories].map((c) => {
              const active = filters.category_id === c.id
              return (
                <button
                  key={c.id || 'all'}
                  type="button"
                  onClick={() => (haptic.select(), update({ category_id: c.id }))}
                  className={`chip ${active ? 'border-ink bg-ink text-cream' : 'border-rose-200 bg-white text-ink'}`}
                >
                  {pick(c, 'name')}
                </button>
              )
            })}
          </div>
        )}
      </header>

      {products.isPending ? (
        <ProductGridSkeleton />
      ) : products.isError ? (
        <ErrorState error={products.error} onRetry={() => products.refetch()} />
      ) : items.length === 0 ? (
        searching ? (
          <EmptyState
            icon={SearchIcon}
            title={t('catalog.empty_title')}
            text={t('catalog.empty_text')}
            action={
              <Button variant="outline" onClick={() => update({ q: '', category_id: '', size: '', min_price: '', max_price: '', sort: 'new' })}>
                {t('catalog.reset')}
              </Button>
            }
          />
        ) : (
          <EmptyState icon={BagIcon} title={t('catalog.empty_shop_title')} text={t('catalog.empty_shop_text')} />
        )
      ) : (
        <ProductGrid
          products={items}
          hasMore={products.hasNextPage}
          loadingMore={products.isFetchingNextPage}
          onLoadMore={products.fetchNextPage}
        />
      )}

      <FilterSheet open={filterOpen} onClose={() => setFilterOpen(false)} filters={filters} onApply={update} />
    </div>
  )
}
