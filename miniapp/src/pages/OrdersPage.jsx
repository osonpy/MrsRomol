import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useOrders } from '../hooks/useOrders'
import { paymentsApi } from '../api/payments'
import { OrderCard } from '../components/OrderCard'
import { SkeletonOrderCard } from '../components/ui/SkeletonCard'
import { BottomSheet } from '../components/ui/BottomSheet'
import { EmptyState } from '../components/ui/EmptyState'
import { Button } from '../components/ui/Button'
import { PageWrapper } from '../components/layout/PageWrapper'
import { formatPrice } from '../utils/formatPrice'

export default function OrdersPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { orders, loading, error, refetch } = useOrders()

  const [receiptOrder, setReceiptOrder] = useState(null)
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState('card')
  const [receiptFile, setReceiptFile] = useState(null)
  const [receiptPreview, setReceiptPreview] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [payError, setPayError] = useState(null)
  const [paySuccess, setPaySuccess] = useState(false)

  const METHODS = [
    { value: 'card',  label: `💳 ${t('payment.methods.card')}` },
    { value: 'click', label: `📱 ${t('payment.methods.click')}` },
    { value: 'payme', label: `📱 ${t('payment.methods.payme')}` },
    { value: 'cash',  label: `💵 ${t('payment.methods.cash')}` },
  ]

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setReceiptFile(file)
    const reader = new FileReader()
    reader.onload = (ev) => setReceiptPreview(ev.target.result)
    reader.readAsDataURL(file)
  }

  const handleSubmitPayment = async () => {
    if (!payAmount || isNaN(parseFloat(payAmount))) {
      setPayError(t('payment.amount_required'))
      return
    }
    if (!receiptFile) {
      setPayError(t('payment.receipt_required'))
      return
    }
    setPayError(null)
    setSubmitting(true)
    try {
      const { file_id } = await paymentsApi.uploadReceipt(receiptFile)
      await paymentsApi.create({
        order_id: receiptOrder.id,
        method: payMethod,
        amount: parseFloat(payAmount),
        receipt_file_id: file_id,
      })
      setPaySuccess(true)
      setTimeout(() => {
        setReceiptOrder(null)
        setPaySuccess(false)
        setReceiptFile(null)
        setReceiptPreview(null)
        setPayAmount('')
        refetch()
      }, 2000)
    } catch (e) {
      setPayError(e?.error ?? e?.message ?? t('payment.error'))
    } finally {
      setSubmitting(false)
    }
  }

  const openReceipt = (order) => {
    setReceiptOrder(order)
    setPayAmount(String(Math.round(order.total_amount)))
    setPayError(null)
    setPaySuccess(false)
    setReceiptFile(null)
    setReceiptPreview(null)
  }

  return (
    <PageWrapper>
      <div className="px-4 pt-4 pb-3 sticky top-0 z-10" style={{ background: 'var(--tg-theme-bg-color)' }}>
        <h1 className="text-xl font-bold" style={{ color: 'var(--tg-theme-text-color)' }}>
          📦 {t('orders.title')}
        </h1>
      </div>

      <div className="px-4 pb-4 space-y-3">
        {loading && Array.from({ length: 3 }).map((_, i) => <SkeletonOrderCard key={i} />)}

        {error && !loading && (
          <EmptyState
            emoji="😕"
            title={t('common.error')}
            action={<Button onClick={refetch}>{t('common.retry')}</Button>}
          />
        )}

        {!loading && !error && orders.length === 0 && (
          <EmptyState
            emoji="📭"
            title={t('orders.empty')}
            description={t('orders.empty_hint')}
            action={<Button onClick={() => navigate('/')}>🛍️ {t('cart.go_to_catalog')}</Button>}
          />
        )}

        {!loading && !error && orders.map((order) => (
          <OrderCard key={order.id} order={order} onSendReceipt={openReceipt} />
        ))}
      </div>

      <BottomSheet
        isOpen={!!receiptOrder}
        onClose={() => { setReceiptOrder(null); setPayError(null) }}
        title={t('payment.title')}
      >
        {paySuccess ? (
          <div className="flex flex-col items-center py-8 gap-3">
            <span className="text-5xl">✅</span>
            <p className="font-semibold text-green-600">{t('payment.sent')}</p>
          </div>
        ) : (
          <div className="space-y-4 pb-4">
            <div>
              <label className="text-sm font-medium mb-1 block" style={{ color: 'var(--tg-theme-hint-color)' }}>
                {t('payment.amount')} (so'm)
              </label>
              <input
                type="number"
                inputMode="numeric"
                className="tg-input"
                placeholder="0"
                value={payAmount}
                onChange={(e) => { setPayAmount(e.target.value); setPayError(null) }}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--tg-theme-hint-color)' }}>
                {t('payment.method')}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {METHODS.map((m) => (
                  <button
                    key={m.value}
                    onClick={() => setPayMethod(m.value)}
                    className="p-2.5 rounded-xl text-sm font-medium transition-all active:scale-95"
                    style={{
                      background: payMethod === m.value ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                      color: payMethod === m.value ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-text-color)',
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--tg-theme-hint-color)' }}>
                {t('payment.receipt')}
              </label>
              <label
                className="flex flex-col items-center justify-center w-full h-32 rounded-xl border-2 border-dashed cursor-pointer"
                style={{
                  borderColor: receiptPreview ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-hint-color)',
                  background: 'var(--tg-theme-secondary-bg-color)',
                }}
              >
                {receiptPreview ? (
                  <img src={receiptPreview} alt="receipt" className="h-28 object-contain rounded-lg" />
                ) : (
                  <>
                    <span className="text-3xl">📸</span>
                    <span className="text-xs mt-1" style={{ color: 'var(--tg-theme-hint-color)' }}>
                      {t('payment.receipt')}
                    </span>
                  </>
                )}
                <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
              </label>
            </div>

            {payError && (
              <div className="rounded-xl p-3 bg-red-50 border border-red-200">
                <p className="text-sm text-red-600">{payError}</p>
              </div>
            )}

            <Button fullWidth size="lg" loading={submitting} onClick={handleSubmitPayment}>
              💳 {t('payment.submit')}
            </Button>
          </div>
        )}
      </BottomSheet>
    </PageWrapper>
  )
}
