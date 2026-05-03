import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { productsApi } from '../api/products'
import { formatPrice } from '../utils/formatPrice'

export function ProductCard({ product }) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const inStock = product.stock_qty > 0
  const imageUrl = product.image_file_id ? productsApi.imageUrl(product.id, 0) : null

  return (
    <div
      className="rounded-2xl overflow-hidden cursor-pointer active:scale-95 transition-transform duration-150"
      style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
      onClick={() => navigate(`/product/${product.id}`)}
    >
      <div className="relative aspect-square overflow-hidden" style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={product.name}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">🧣</div>
        )}
        {!inStock && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <span className="text-white font-semibold text-xs bg-red-500 px-2 py-1 rounded-full">
              {t('product.out_of_stock')}
            </span>
          </div>
        )}
      </div>
      <div className="p-3 space-y-1">
        {product.category && (
          <p className="text-xs truncate" style={{ color: 'var(--tg-theme-hint-color)' }}>
            {product.category}
          </p>
        )}
        <p className="text-sm font-semibold leading-tight line-clamp-2" style={{ color: 'var(--tg-theme-text-color)' }}>
          {product.name}
        </p>
        <p className="text-sm font-bold" style={{ color: 'var(--tg-theme-button-color)' }}>
          {formatPrice(product.sell_price)}
        </p>
      </div>
    </div>
  )
}
