import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { productsApi } from '../api/products'
import { useCartStore } from '../store/cartStore'
import { useTelegram } from '../hooks/useTelegram'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { SkeletonCard } from '../components/ui/SkeletonCard'
import { formatPrice } from '../utils/formatPrice'

export default function ProductPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { tg } = useTelegram()
  const addItem = useCartStore((s) => s.addItem)
  const cartItems = useCartStore((s) => s.items)

  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [qty, setQty] = useState(1)
  const [selectedColor, setSelectedColor] = useState(null)
  const [added, setAdded] = useState(false)

  useEffect(() => {
    if (!tg?.BackButton) return
    tg.BackButton.show()
    tg.BackButton.onClick(() => navigate(-1))
    return () => tg.BackButton.hide()
  }, [tg, navigate])

  useEffect(() => {
    setLoading(true)
    productsApi
      .get(id)
      .then((p) => {
        setProduct(p)
        const colors = p.metadata?.colors
        if (colors?.length) setSelectedColor(colors[0])
      })
      .catch((e) => setError(e?.error ?? e?.message ?? 'Error'))
      .finally(() => setLoading(false))
  }, [id])

  const inStock = product?.stock_qty > 0
  const colors = product?.metadata?.colors ?? []
  const totalInCart = cartItems
    .filter((i) => i.product.id === id)
    .reduce((s, i) => s + i.qty, 0)
  const maxQty = product ? Math.max(0, product.stock_qty - totalInCart) : 0

  const handleAdd = () => {
    if (!product || !inStock) return
    addItem(product, qty)
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
    setQty(1)
  }

  if (loading) {
    return (
      <div className="p-4 space-y-3">
        <div className="aspect-square rounded-2xl overflow-hidden">
          <SkeletonCard />
        </div>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4 p-8">
        <span className="text-5xl">😕</span>
        <p style={{ color: 'var(--tg-theme-hint-color)' }}>{error || t('common.error')}</p>
        <Button onClick={() => navigate(-1)}>{t('common.back')}</Button>
      </div>
    )
  }

  const imageUrl = product.image_file_id ? productsApi.imageUrl(product.id, 0) : null

  return (
    <div className="flex flex-col min-h-screen pb-28" style={{ background: 'var(--tg-theme-bg-color)' }}>
      {!tg?.BackButton && (
        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 z-20 w-9 h-9 rounded-full flex items-center justify-center shadow active:scale-90 transition-transform"
          style={{ background: 'var(--tg-theme-bg-color)' }}
        >
          ←
        </button>
      )}

      <div className="relative aspect-square overflow-hidden" style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
        {imageUrl ? (
          <img src={imageUrl} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-7xl">🧣</div>
        )}
      </div>

      <div className="px-4 pt-4 space-y-4">
        <div>
          {product.category && (
            <Badge variant="info" className="mb-2">{product.category}</Badge>
          )}
          <h1 className="text-xl font-bold leading-snug" style={{ color: 'var(--tg-theme-text-color)' }}>
            {product.name}
          </h1>
        </div>

        <div>
          {inStock ? (
            <Badge variant="success">✅ {t('product.in_stock')} · {t('product.stock_qty', { qty: product.stock_qty })}</Badge>
          ) : (
            <Badge variant="danger">❌ {t('product.out_of_stock')}</Badge>
          )}
        </div>

        <p className="text-2xl font-extrabold" style={{ color: 'var(--tg-theme-button-color)' }}>
          {formatPrice(product.sell_price)}
        </p>

        {colors.length > 0 && (
          <div>
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--tg-theme-hint-color)' }}>
              {t('product.color')}: <span style={{ color: 'var(--tg-theme-text-color)' }}>{selectedColor}</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {colors.map((color) => (
                <button
                  key={color}
                  onClick={() => setSelectedColor(color)}
                  className="px-3 py-1.5 rounded-xl text-sm font-medium transition-all active:scale-95"
                  style={{
                    background: selectedColor === color ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                    color: selectedColor === color ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-text-color)',
                  }}
                >
                  {color}
                </button>
              ))}
            </div>
          </div>
        )}

        {inStock && (
          <div>
            <p className="text-xs font-medium mb-2" style={{ color: 'var(--tg-theme-hint-color)' }}>
              {t('product.quantity')}
            </p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setQty((q) => Math.max(1, q - 1))}
                disabled={qty <= 1}
                className="w-10 h-10 rounded-xl flex items-center justify-center text-xl font-bold transition-all active:scale-90 disabled:opacity-40"
                style={{ background: 'var(--tg-theme-secondary-bg-color)', color: 'var(--tg-theme-text-color)' }}
              >
                −
              </button>
              <span className="text-xl font-bold w-8 text-center" style={{ color: 'var(--tg-theme-text-color)' }}>
                {qty}
              </span>
              <button
                onClick={() => setQty((q) => Math.min(maxQty, q + 1))}
                disabled={qty >= maxQty}
                className="w-10 h-10 rounded-xl flex items-center justify-center text-xl font-bold transition-all active:scale-90 disabled:opacity-40"
                style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
              >
                +
              </button>
              <span className="text-sm" style={{ color: 'var(--tg-theme-hint-color)' }}>max {maxQty}</span>
            </div>
          </div>
        )}

        {product.description && (
          <div>
            <p className="text-xs font-medium mb-1" style={{ color: 'var(--tg-theme-hint-color)' }}>
              {t('product.description')}
            </p>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--tg-theme-text-color)' }}>
              {product.description}
            </p>
          </div>
        )}
      </div>

      <div
        className="fixed bottom-16 left-0 right-0 px-4 pb-2 pt-3"
        style={{ background: 'var(--tg-theme-bg-color)' }}
      >
        <Button fullWidth size="lg" disabled={!inStock || added || qty > maxQty} onClick={handleAdd}>
          {added
            ? t('product.added')
            : inStock
            ? `🛒 ${t('product.add_to_cart')} · ${formatPrice(parseFloat(product.sell_price) * qty)}`
            : t('product.out_of_stock')}
        </Button>
      </div>
    </div>
  )
}
