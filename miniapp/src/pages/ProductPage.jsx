import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { BagIcon, InfoIcon, RulerIcon, XIcon } from '../components/icons'
import { HeartButton, PriceLabel, ProductImage } from '../components/product'
import { Button, EmptyState, ErrorState, Sheet, Skeleton, StickyBar } from '../components/ui'
import { toast } from '../lib/toast'
import { useProduct } from '../hooks/queries'
import { localized, money, pick } from '../lib/format'
import { formatCell, recommendSize } from '../lib/sizing'
import { haptic } from '../lib/telegram'
import { useCart } from '../store/cart'

// ── gallery ───────────────────────────────────────────────────────────────────

function Gallery({ images, name, scrollTo, onOpen }) {
  const ref = useRef(null)
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (scrollTo == null || !ref.current) return
    ref.current.scrollTo({ left: scrollTo * ref.current.clientWidth, behavior: 'smooth' })
  }, [scrollTo])

  if (!images.length) return <ProductImage image={null} className="aspect-[3/4] w-full" />

  return (
    <div className="relative">
      <div
        ref={ref}
        onScroll={(e) => setIndex(Math.round(e.currentTarget.scrollLeft / e.currentTarget.clientWidth))}
        className="no-scrollbar flex aspect-[3/4] w-full snap-x snap-mandatory overflow-x-auto"
      >
        {images.map((img, i) => (
          <button key={img.id} type="button" onClick={() => onOpen(i)} className="h-full w-full shrink-0 snap-center">
            <img
              src={img.url}
              alt={name}
              loading={i === 0 ? 'eager' : 'lazy'}
              className="h-full w-full bg-rose-50 object-cover"
            />
          </button>
        ))}
      </div>
      {images.length > 1 && (
        <div className="absolute inset-x-0 bottom-3 flex justify-center gap-1.5">
          {images.map((img, i) => (
            <span
              key={img.id}
              className={`h-1.5 rounded-full transition-all ${i === index ? 'w-5 bg-white' : 'w-1.5 bg-white/60'}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function Lightbox({ images, start, onClose }) {
  const ref = useRef(null)
  useEffect(() => {
    ref.current?.scrollTo({ left: start * ref.current.clientWidth })
  }, [start])
  return createPortal(
    <div className="fixed inset-0 z-50 animate-fade-in bg-black">
      <div ref={ref} className="no-scrollbar flex h-full snap-x snap-mandatory overflow-x-auto">
        {images.map((img) => (
          <div key={img.id} className="flex h-full w-full shrink-0 snap-center items-center justify-center">
            <img src={img.url} alt="" className="max-h-full max-w-full object-contain" />
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label="close"
        className="absolute right-4 top-4 rounded-full bg-white/15 p-2.5 text-white backdrop-blur"
      >
        <XIcon className="h-6 w-6" />
      </button>
    </div>,
    document.body,
  )
}

// ── size guide ────────────────────────────────────────────────────────────────

function columnLabel(t, col) {
  const key = `sizing.columns.${col}`
  const label = t(key)
  return label === key ? col : label
}

function SizeGuide({ chart, open, onClose, onPick }) {
  const { t } = useTranslation()
  const [measures, setMeasures] = useState({})
  const result = recommendSize(chart, measures)

  return (
    <Sheet open={open} onClose={onClose} title={t('sizing.title')}>
      <p className="text-sm text-ink-soft">{t('sizing.intro')}</p>
      <div className="mt-4 grid grid-cols-2 gap-3">
        {chart.columns.map((col) => (
          <label key={col}>
            <span className="label">{columnLabel(t, col)}</span>
            <div className="relative">
              <input
                inputMode="decimal"
                className="field pr-10"
                value={measures[col] || ''}
                onChange={(e) => setMeasures((m) => ({ ...m, [col]: e.target.value.replace(/[^\d.,]/g, '').replace(',', '.') }))}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-faint">{t('common.cm')}</span>
            </div>
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-faint">{t('sizing.how')}</p>

      <div className="mt-5 rounded-2xl bg-rose-50 p-4 text-center">
        {result ? (
          <>
            <p className="font-serif text-2xl font-semibold text-rose-700">
              {t(result.exact ? 'sizing.result' : 'sizing.result_near', { size: result.size })}
            </p>
            <Button className="mt-3 w-full" onClick={() => (onPick(result.size), onClose())}>
              {t('sizing.choose', { size: result.size })}
            </Button>
          </>
        ) : (
          <p className="text-sm text-ink-soft">{t('sizing.fill')}</p>
        )}
      </div>

      <h3 className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wider text-ink-soft">{t('product.size_chart')}</h3>
      <SizeTable chart={chart} highlight={result?.size} />
    </Sheet>
  )
}

function SizeTable({ chart, highlight }) {
  const { t } = useTranslation()
  return (
    <div className="overflow-x-auto rounded-xl border border-rose-100">
      <table className="w-full text-center text-sm">
        <thead className="bg-rose-50 text-ink-soft">
          <tr>
            <th className="px-3 py-2 font-semibold">{t('product.choose_size')}</th>
            {chart.columns.map((c) => (
              <th key={c} className="px-3 py-2 font-semibold">
                {columnLabel(t, c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chart.rows.map((row) => (
            <tr key={row.size} className={`border-t border-rose-100 ${row.size === highlight ? 'bg-rose-100 font-semibold' : 'bg-white'}`}>
              <td className="px-3 py-2 font-semibold">{row.size}</td>
              {chart.columns.map((c) => (
                <td key={c} className="px-3 py-2 tabular-nums">
                  {formatCell(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── page ──────────────────────────────────────────────────────────────────────

function ProductSkeleton() {
  return (
    <div>
      <Skeleton className="aspect-[3/4] w-full rounded-none" />
      <div className="space-y-3 p-4">
        <Skeleton className="h-7 w-3/4" />
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  )
}

export default function ProductPage() {
  const { id } = useParams()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: p, isPending, isError, error, refetch } = useProduct(id)
  const add = useCart((s) => s.add)
  const cartItems = useCart((s) => s.items)

  const [color, setColor] = useState(null)
  const [size, setSize] = useState(null)
  const [lightbox, setLightbox] = useState(null)
  const [guideOpen, setGuideOpen] = useState(false)
  const [wantSelection, setWantSelection] = useState(false)

  const { colors, sizes } = useMemo(() => {
    const vs = p?.variants ?? []
    const colorMap = new Map()
    vs.forEach((v) => v.color_uz && !colorMap.has(v.color_uz) && colorMap.set(v.color_uz, { uz: v.color_uz, ru: v.color_ru, hex: v.color_hex }))
    return { colors: [...colorMap.values()], sizes: [...new Set(vs.filter((v) => v.size).map((v) => v.size))] }
  }, [p])

  // Pre-select the first colour that is in stock, and the only size if there is one.
  useEffect(() => {
    if (!p) return
    const firstInStock = p.variants.find((v) => v.in_stock && v.color_uz)
    setColor(firstInStock?.color_uz ?? colors[0]?.uz ?? null)
    setSize(sizes.length === 1 ? sizes[0] : null)
  }, [p, colors, sizes])

  const variantFor = (c, s) =>
    p?.variants.find((v) => (v.color_uz ?? null) === (colors.length ? c : null) && (v.size ?? null) === (sizes.length ? s : null))
  const selected = variantFor(color, size)
  const inCart = selected ? cartItems.find((i) => i.variant_id === selected.id)?.quantity ?? 0 : 0
  const colorImageIndex = p?.images.findIndex((img) => img.color_uz && img.color_uz === color)

  if (isPending) return <ProductSkeleton />
  if (isError) {
    return error?.status === 404 ? (
      <EmptyState
        icon={BagIcon}
        title={t('product.not_found')}
        action={<Button variant="outline" onClick={() => navigate('/', { replace: true })}>{t('common.back_home')}</Button>}
      />
    ) : (
      <ErrorState error={error} onRetry={refetch} />
    )
  }

  const name = pick(p, 'name')
  const description = pick(p, 'description')

  function addToCart() {
    if (!selected) {
      haptic.error()
      setWantSelection(true)
      toast.show(t('product.choose_variant'))
      return
    }
    add({
      variant_id: selected.id,
      product_id: p.id,
      name_uz: p.name_uz,
      name_ru: p.name_ru,
      color_uz: selected.color_uz,
      color_ru: selected.color_ru,
      size: selected.size,
      price: selected.price,
      image: p.images.find((img) => img.color_uz === selected.color_uz) ?? p.images[0] ?? null,
    })
    haptic.success()
    toast.show(t('product.added'))
  }

  return (
    <div className="pb-4">
      <div className="relative">
        <Gallery images={p.images} name={name} scrollTo={colorImageIndex >= 0 ? colorImageIndex : null} onOpen={setLightbox} />
        <HeartButton productId={p.id} active={p.is_favorite} className="absolute right-4 top-4 h-11 w-11" />
      </div>

      <div className="px-4 pt-4">
        <h1 className="font-serif text-[28px] font-semibold leading-tight text-ink">{name}</h1>
        <div className="mt-1.5 flex items-center gap-3">
          {selected ? (
            <span className="text-xl font-semibold text-rose-700">{money(selected.price)}</span>
          ) : (
            <PriceLabel price={p.price} priceMax={p.price_max} className="text-xl" />
          )}
          {selected?.low_stock && (
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">{t('product.low_stock')}</span>
          )}
        </div>

        {colors.length > 0 && (
          <div className="mt-5">
            <h2 className="label">
              {t('product.choose_color')}: <span className="text-ink">{localized(colors.find((c) => c.uz === color))}</span>
            </h2>
            <div className="flex flex-wrap gap-2.5">
              {colors.map((c) => {
                const available = p.variants.some((v) => v.color_uz === c.uz && v.in_stock)
                const active = c.uz === color
                return (
                  <button
                    key={c.uz}
                    type="button"
                    aria-label={localized(c)}
                    aria-pressed={active}
                    onClick={() => (haptic.select(), setColor(c.uz), setWantSelection(false))}
                    className={`relative flex h-10 items-center gap-2 rounded-full border pl-1.5 pr-3.5 text-sm transition ${
                      active ? 'border-rose-600 ring-1 ring-rose-600' : 'border-rose-200'
                    } ${available ? 'bg-white' : 'bg-white/60 text-ink-faint'}`}
                  >
                    <span className="h-7 w-7 rounded-full border border-ink/10" style={{ background: c.hex || '#E8DED8' }} />
                    {localized(c)}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {sizes.length > 0 && (
          <div className="mt-5">
            <div className="flex items-center justify-between">
              <h2 className={`label ${wantSelection && !size ? 'text-red-700' : ''}`}>{t('product.choose_size')}</h2>
              {p.size_chart && (
                <button type="button" onClick={() => setGuideOpen(true)} className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-rose-700">
                  <RulerIcon className="h-5 w-5" />
                  {t('product.find_my_size')}
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {sizes.map((s) => {
                const v = variantFor(color, s)
                const available = Boolean(v?.in_stock)
                const active = s === size
                return (
                  <button
                    key={s}
                    type="button"
                    disabled={!v}
                    onClick={() => (haptic.select(), setSize(s), setWantSelection(false))}
                    className={`h-11 min-w-[3.25rem] rounded-xl border px-3 text-sm font-semibold transition ${
                      active
                        ? 'border-rose-600 bg-rose-600 text-white'
                        : available
                          ? 'border-rose-200 bg-white text-ink'
                          : 'border-rose-100 bg-white/50 text-ink-faint line-through'
                    } disabled:opacity-40`}
                  >
                    {s}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {selected && !selected.in_stock && <p className="mt-3 text-sm font-medium text-red-700">{t('product.out_of_stock')}</p>}

        {description && (
          <div className="mt-6">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-ink-soft">{t('product.description')}</h2>
            <p className="whitespace-pre-line leading-relaxed text-ink">{description}</p>
          </div>
        )}

        {p.size_chart && (
          <div className="mt-6">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-ink-soft">{t('product.size_chart')}</h2>
            <SizeTable chart={p.size_chart} highlight={size} />
          </div>
        )}

        <div className="mt-6 flex gap-3 rounded-2xl bg-rose-50 p-4 text-sm text-rose-800">
          <InfoIcon className="h-5 w-5 shrink-0" />
          <p>{t('product.no_returns')}</p>
        </div>
      </div>

      <StickyBar>
        {inCart > 0 ? (
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={addToCart} disabled={!selected?.in_stock}>
              + 1
            </Button>
            <Button className="flex-[3]" onClick={() => navigate('/cart')}>
              <BagIcon className="h-5 w-5" />
              {t('product.in_cart', { count: inCart })}
            </Button>
          </div>
        ) : (
          <Button className="w-full" onClick={addToCart} disabled={selected ? !selected.in_stock : !p.in_stock}>
            <BagIcon className="h-5 w-5" />
            {t('product.add_to_cart')}
          </Button>
        )}
      </StickyBar>

      {lightbox !== null && <Lightbox images={p.images} start={lightbox} onClose={() => setLightbox(null)} />}
      {p.size_chart && (
        <SizeGuide
          chart={p.size_chart}
          open={guideOpen}
          onClose={() => setGuideOpen(false)}
          onPick={(s) => sizes.includes(s) && setSize(s)}
        />
      )}
    </div>
  )
}
