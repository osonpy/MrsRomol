import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useProducts } from '../hooks/useProducts'
import { ProductGrid } from '../components/ProductGrid'
import { SkeletonCard } from '../components/ui/SkeletonCard'
import { EmptyState } from '../components/ui/EmptyState'
import { PageWrapper } from '../components/layout/PageWrapper'
import { Button } from '../components/ui/Button'

const ALL = '__all__'

export default function CatalogPage() {
  const { t } = useTranslation()
  const { products, loading, error, refetch } = useProducts()
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState(ALL)

  const categories = useMemo(() => {
    const cats = [...new Set(products.map((p) => p.category).filter(Boolean))]
    return [ALL, ...cats]
  }, [products])

  const filtered = useMemo(() => {
    return products.filter((p) => {
      const matchCat = activeCategory === ALL || p.category === activeCategory
      const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase())
      return matchCat && matchSearch
    })
  }, [products, activeCategory, search])

  return (
    <PageWrapper>
      <div
        className="sticky top-0 z-10 px-4 pt-4 pb-3 space-y-3"
        style={{ background: 'var(--tg-theme-bg-color)' }}
      >
        <h1 className="text-xl font-bold" style={{ color: 'var(--tg-theme-text-color)' }}>
          {t('catalog.title')}
        </h1>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm">🔍</span>
          <input
            className="tg-input pl-9"
            placeholder={t('catalog.search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {!loading && categories.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all active:scale-95 ${
                  activeCategory === cat ? 'chip-active' : 'chip-inactive'
                }`}
                style={{
                  background: activeCategory === cat ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                  color: activeCategory === cat ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-text-color)',
                }}
              >
                {cat === ALL ? t('catalog.all_categories') : cat}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 pb-4">
        {error && !loading && (
          <EmptyState
            emoji="😕"
            title={t('common.error')}
            action={<Button onClick={refetch}>{t('common.retry')}</Button>}
          />
        )}

        {loading && (
          <div className="grid grid-cols-2 gap-3 pt-2">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <EmptyState emoji="🧣" title={t('catalog.empty')} />
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="pt-2">
            <ProductGrid products={filtered} />
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
