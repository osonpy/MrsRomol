import { useTranslation } from 'react-i18next'
import { useCartStore } from '../store/cartStore'
import { formatPrice } from '../utils/formatPrice'

export function CartItem({ item }) {
  const { t } = useTranslation()
  const { removeItem, updateQty } = useCartStore()
  const { product, qty, selectedColor } = item
  const subtotal = parseFloat(product.sell_price) * qty

  return (
    <div
      className="flex gap-3 p-3 rounded-2xl"
      style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
    >
      <div
        className="w-14 h-14 rounded-xl flex-shrink-0 flex items-center justify-center text-2xl"
        style={{ background: 'var(--tg-theme-bg-color)' }}
      >
        🧣
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold truncate" style={{ color: 'var(--tg-theme-text-color)' }}>
          {product.name}
        </p>
        {selectedColor && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--tg-theme-hint-color)' }}>
            {selectedColor}
          </p>
        )}
        <p className="text-xs mt-0.5 font-medium" style={{ color: 'var(--tg-theme-button-color)' }}>
          {formatPrice(product.sell_price)} × {qty}
        </p>
        <p className="text-sm font-bold mt-0.5" style={{ color: 'var(--tg-theme-text-color)' }}>
          {formatPrice(subtotal)}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <button
          onClick={() => removeItem(product.id)}
          className="w-6 h-6 rounded-full flex items-center justify-center text-red-400 active:scale-90 transition-transform"
          style={{ background: 'var(--tg-theme-bg-color)' }}
          aria-label="remove"
        >
          ×
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => updateQty(product.id, qty - 1)}
            className="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold active:scale-90 transition-transform"
            style={{ background: 'var(--tg-theme-bg-color)', color: 'var(--tg-theme-text-color)' }}
          >
            −
          </button>
          <span className="text-sm font-semibold w-5 text-center" style={{ color: 'var(--tg-theme-text-color)' }}>
            {qty}
          </span>
          <button
            onClick={() => updateQty(product.id, Math.min(qty + 1, product.stock_qty))}
            disabled={qty >= product.stock_qty}
            className="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold active:scale-90 transition-transform disabled:opacity-40"
            style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
          >
            +
          </button>
        </div>
      </div>
    </div>
  )
}
