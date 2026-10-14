import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useToggleFavorite } from '../hooks/queries'
import { localized, money, pick } from '../lib/format'
import { haptic } from '../lib/telegram'
import { HeartFilledIcon, HeartIcon, ImageIcon } from './icons'
import { Skeleton, Spinner } from './ui'
import { toast } from '../lib/toast'

export function HeartButton({ productId, active, className = '' }) {
  const toggle = useToggleFavorite()
  return (
    <button
      type="button"
      aria-label="favorite"
      aria-pressed={active}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        haptic.select()
        toggle.mutate({ id: productId, on: !active }, { onError: toast.error })
      }}
      className={`flex h-9 w-9 items-center justify-center rounded-full bg-white/85 backdrop-blur transition active:scale-90 ${className}`}
    >
      {active ? <HeartFilledIcon className="h-5 w-5 text-rose-600" /> : <HeartIcon className="h-5 w-5 text-ink" />}
    </button>
  )
}

export function ProductImage({ image, alt, large = false, className = '' }) {
  if (!image) {
    return (
      <div className={`flex items-center justify-center bg-rose-50 text-rose-300 ${className}`}>
        <ImageIcon className="h-10 w-10" />
      </div>
    )
  }
  return (
    <img
      src={large ? image.url : image.thumb_url}
      alt={alt}
      loading="lazy"
      decoding="async"
      className={`bg-rose-50 object-cover ${className}`}
    />
  )
}

export function PriceLabel({ price, priceMax, className = '' }) {
  const { t } = useTranslation()
  return (
    <span className={`font-semibold text-rose-700 ${className}`}>
      {priceMax > price ? t('common.from', { price: money(price) }) : money(price)}
    </span>
  )
}

export function ProductCard({ product }) {
  const { t } = useTranslation()
  const name = pick(product, 'name')
  return (
    <Link to={`/product/${product.id}`} className="group block">
      <div className="relative overflow-hidden rounded-2xl">
        <ProductImage image={product.image} alt={name} className="aspect-[3/4] w-full transition group-active:scale-[1.02]" />
        {product.is_new && product.in_stock && (
          <span className="absolute left-2 top-2 rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-rose-700">
            {t('catalog.new')}
          </span>
        )}
        {!product.in_stock && (
          <div className="absolute inset-x-0 bottom-0 bg-ink/55 py-1.5 text-center text-xs font-semibold text-white">
            {t('catalog.sold_out')}
          </div>
        )}
        <HeartButton productId={product.id} active={product.is_favorite} className="absolute right-2 top-2" />
      </div>
      <div className="px-0.5 pt-2">
        <h3 className="line-clamp-2 text-sm leading-snug text-ink">{name}</h3>
        <PriceLabel price={product.price} priceMax={product.price_max} className="mt-1 block text-[15px]" />
        {product.colors.length > 1 && (
          <div className="mt-1.5 flex gap-1">
            {product.colors.slice(0, 6).map((c) => (
              <span
                key={c.uz}
                title={localized(c)}
                className="h-3 w-3 rounded-full border border-ink/10"
                style={{ background: c.hex || '#E8DED8' }}
              />
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}

export function ProductGridSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-2 gap-x-3 gap-y-5 px-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i}>
          <Skeleton className="aspect-[3/4] w-full rounded-2xl" />
          <Skeleton className="mt-2.5 h-3.5 w-4/5" />
          <Skeleton className="mt-2 h-4 w-1/2" />
        </div>
      ))}
    </div>
  )
}

// Grid with "load more when the end scrolls into view".
export function ProductGrid({ products, hasMore, loadingMore, onLoadMore }) {
  const { t } = useTranslation()
  const sentinel = useRef(null)

  useEffect(() => {
    if (!hasMore || !sentinel.current) return
    const io = new IntersectionObserver((entries) => entries[0].isIntersecting && onLoadMore(), {
      rootMargin: '600px',
    })
    io.observe(sentinel.current)
    return () => io.disconnect()
  }, [hasMore, onLoadMore])

  return (
    <>
      <div className="grid grid-cols-2 gap-x-3 gap-y-5 px-4">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {hasMore && (
        <div ref={sentinel} className="flex justify-center py-6 text-ink-soft">
          {loadingMore && <Spinner className="h-5 w-5" />}
          <span className="sr-only">{t('catalog.loading_more')}</span>
        </div>
      )}
    </>
  )
}
