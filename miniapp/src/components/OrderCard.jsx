import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge, statusBadge, paymentBadge } from './ui/Badge'
import { Button } from './ui/Button'
import { formatPrice } from '../utils/formatPrice'
import { formatDate } from '../utils/formatDate'

const STATUS_STEPS = ['pending', 'confirmed', 'shipped', 'delivered']

export function OrderCard({ order, onSendReceipt }) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const shortId = order.id.slice(-8).toUpperCase()
  const { emoji, variant: statusVariant } = statusBadge(order.status)
  const hasPayment = !!order.payment
  const canSendReceipt = (order.status === 'pending' || order.status === 'confirmed') && !hasPayment
  const stepIndex = STATUS_STEPS.indexOf(order.status)

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
      <button
        className="w-full p-4 text-left active:opacity-80 transition-opacity"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs mb-1" style={{ color: 'var(--tg-theme-hint-color)' }}>
              {formatDate(order.created_at)}
            </p>
            <p className="font-semibold text-sm" style={{ color: 'var(--tg-theme-text-color)' }}>
              {t('orders.order_num', { id: shortId })}
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--tg-theme-hint-color)' }}>
              {t('orders.items_count', { n: order.items?.length ?? 0 })}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <Badge variant={statusVariant}>
              {emoji} {t(`orders.status.${order.status}`, order.status)}
            </Badge>
            <p className="font-bold text-sm" style={{ color: 'var(--tg-theme-text-color)' }}>
              {formatPrice(order.total_amount)}
            </p>
            <span
              className="text-xs transition-transform duration-200"
              style={{
                color: 'var(--tg-theme-hint-color)',
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                display: 'inline-block',
              }}
            >
              ▼
            </span>
          </div>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t" style={{ borderColor: 'var(--tg-theme-bg-color)' }}>
          {order.status !== 'cancelled' && (
            <div className="flex items-center gap-1 pt-4">
              {STATUS_STEPS.map((step, idx) => (
                <div key={step} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors duration-300"
                      style={{
                        background: idx <= stepIndex ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-bg-color)',
                        color: idx <= stepIndex ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-hint-color)',
                      }}
                    >
                      {idx < stepIndex ? '✓' : idx + 1}
                    </div>
                    <p className="text-center mt-1" style={{ color: 'var(--tg-theme-hint-color)', fontSize: '9px' }}>
                      {t(`orders.status.${step}`)}
                    </p>
                  </div>
                  {idx < STATUS_STEPS.length - 1 && (
                    <div
                      className="h-0.5 flex-1 -mt-5 transition-colors duration-300"
                      style={{
                        background: idx < stepIndex ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                        filter: 'brightness(0.8)',
                      }}
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="space-y-1">
            {order.items?.map((item, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span style={{ color: 'var(--tg-theme-text-color)' }}>
                  {item.product_name} × {item.quantity}
                </span>
                <span className="font-medium" style={{ color: 'var(--tg-theme-text-color)' }}>
                  {formatPrice(item.unit_price * item.quantity)}
                </span>
              </div>
            ))}
          </div>

          {hasPayment && (
            <div className="flex items-center gap-2">
              <span className="text-xs" style={{ color: 'var(--tg-theme-hint-color)' }}>
                {t('payment.title')}:
              </span>
              {(() => {
                const { emoji: pe, variant } = paymentBadge(order.payment.status)
                return (
                  <Badge variant={variant}>
                    {pe} {t(`orders.payment_status.${order.payment.status}`, order.payment.status)}
                  </Badge>
                )
              })()}
            </div>
          )}

          {canSendReceipt && (
            <Button variant="primary" fullWidth onClick={() => onSendReceipt?.(order)}>
              💳 {t('orders.send_receipt')}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
