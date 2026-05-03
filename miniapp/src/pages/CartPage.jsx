import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useCartStore } from '../store/cartStore'
import { CartItem } from '../components/CartItem'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { PageWrapper } from '../components/layout/PageWrapper'
import { ordersApi } from '../api/orders'
import { formatPrice } from '../utils/formatPrice'

export default function CartPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const items = useCartStore((s) => s.items)
  const clear = useCartStore((s) => s.clear)
  const total = useCartStore((s) => s.total())

  const [deliveryType, setDeliveryType] = useState('pickup')
  const [address, setAddress] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handlePlaceOrder = async () => {
    if (deliveryType === 'delivery' && !address.trim()) {
      setError(t('cart.address_required'))
      return
    }
    setError(null)
    setLoading(true)
    try {
      await ordersApi.create({
        items: items.map((i) => ({ product_id: i.product.id, quantity: i.qty })),
        delivery_type: deliveryType,
        address: address.trim() || null,
        notes: notes.trim() || null,
      })
      clear()
      navigate('/orders')
    } catch (e) {
      const msg = (e?.error ?? e?.message ?? '').toLowerCase()
      if (msg.includes('stock') || msg.includes('out_of_stock')) {
        setError(t('cart.stock_error'))
      } else {
        setError(t('cart.error'))
      }
    } finally {
      setLoading(false)
    }
  }

  if (items.length === 0) {
    return (
      <PageWrapper className="flex flex-col items-center justify-center">
        <EmptyState
          emoji="🛒"
          title={t('cart.empty')}
          description={t('cart.empty_hint')}
          action={
            <Button onClick={() => navigate('/')}>🛍️ {t('cart.go_to_catalog')}</Button>
          }
        />
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="px-4 pt-4 pb-3 sticky top-0 z-10" style={{ background: 'var(--tg-theme-bg-color)' }}>
        <h1 className="text-xl font-bold" style={{ color: 'var(--tg-theme-text-color)' }}>
          🛒 {t('cart.title')}
        </h1>
      </div>

      <div className="px-4 pb-4 space-y-3">
        {items.map((item) => (
          <CartItem key={item.product.id} item={item} />
        ))}

        <hr style={{ borderColor: 'var(--tg-theme-secondary-bg-color)' }} />

        <div>
          <p className="text-sm font-semibold mb-2" style={{ color: 'var(--tg-theme-text-color)' }}>
            {t('cart.pickup')} / {t('cart.delivery')}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'pickup',   icon: '🏪', label: t('cart.pickup') },
              { value: 'delivery', icon: '🚚', label: t('cart.delivery') },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setDeliveryType(opt.value)}
                className="p-3 rounded-xl text-center transition-all active:scale-95"
                style={{
                  background: deliveryType === opt.value ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                  color: deliveryType === opt.value ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-text-color)',
                }}
              >
                <div className="text-xl mb-1">{opt.icon}</div>
                <div className="text-xs font-medium">{opt.label}</div>
              </button>
            ))}
          </div>
        </div>

        {deliveryType === 'delivery' && (
          <div>
            <p className="text-sm font-semibold mb-2" style={{ color: 'var(--tg-theme-text-color)' }}>
              {t('cart.address')} *
            </p>
            <textarea
              className="tg-input resize-none"
              rows={3}
              placeholder={t('cart.address_placeholder')}
              value={address}
              onChange={(e) => { setAddress(e.target.value); setError(null) }}
            />
          </div>
        )}

        <div>
          <p className="text-sm font-semibold mb-2" style={{ color: 'var(--tg-theme-text-color)' }}>
            {t('cart.notes')}
          </p>
          <textarea
            className="tg-input resize-none"
            rows={2}
            placeholder={t('cart.notes_placeholder')}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {error && (
          <div className="rounded-xl p-3 bg-red-50 border border-red-200">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div
          className="flex justify-between items-center p-4 rounded-2xl"
          style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
        >
          <span className="text-sm font-semibold" style={{ color: 'var(--tg-theme-text-color)' }}>
            {t('cart.total')}
          </span>
          <span className="text-xl font-extrabold" style={{ color: 'var(--tg-theme-button-color)' }}>
            {formatPrice(total)}
          </span>
        </div>

        <Button fullWidth size="lg" loading={loading} disabled={loading} onClick={handlePlaceOrder}>
          {loading
            ? t('cart.ordering')
            : `✅ ${t('cart.order')} · ${formatPrice(total)}`}
        </Button>
      </div>
    </PageWrapper>
  )
}
