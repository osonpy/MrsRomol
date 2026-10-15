import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { CheckIcon, CopyIcon, ImageIcon, PackageIcon, TruckIcon } from '../components/icons'
import { Countdown, OrderTimeline, StatusBadge } from '../components/order'
import { ProductImage } from '../components/product'
import { Button, EmptyState, ErrorState, LinkifiedText, Section, Skeleton } from '../components/ui'
import { toast } from '../lib/toast'
import { useCancelOrder, useMeta, useOrder, useSubmitPayment } from '../hooks/queries'
import { cardNumber, dateTime, localized, money, phone, pick } from '../lib/format'
import { confirmDialog, copyText, haptic } from '../lib/telegram'

const CARD_STYLE = {
  uzcard: 'from-[#2B4A7E] to-[#1C3159]',
  humo: 'from-[#2F6B4F] to-[#1E4A36]',
  visa: 'from-[#3A2A25] to-[#5E3B32]',
  mastercard: 'from-[#3A2A25] to-[#5E3B32]',
}

function CopyButton({ value, label }) {
  const { t } = useTranslation()
  const [done, setDone] = useState(false)
  return (
    <button
      type="button"
      onClick={async () => {
        if (await copyText(value)) {
          haptic.success()
          setDone(true)
          toast.show(t('common.copied'))
          setTimeout(() => setDone(false), 1500)
        }
      }}
      className="flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold"
      aria-label={label}
    >
      {done ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
      {t('common.copy')}
    </button>
  )
}

function PaymentCard({ card, selected, onSelect }) {
  return (
    // div, not button: it contains the copy button, and buttons can't nest.
    <div
      role="radio"
      aria-checked={selected}
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect()}
      className={`w-full cursor-pointer rounded-2xl bg-gradient-to-br p-4 text-left text-white transition ${CARD_STYLE[card.card_type]} ${
        selected ? 'ring-2 ring-rose-500 ring-offset-2 ring-offset-cream' : 'opacity-90'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-widest opacity-80">{card.card_type}</span>
        <span
          className={`flex h-5 w-5 items-center justify-center rounded-full border ${selected ? 'border-white bg-white text-rose-700' : 'border-white/60'}`}
        >
          {selected && <CheckIcon className="h-3.5 w-3.5 stroke-[3]" />}
        </span>
      </div>
      <p className="mt-3 font-mono text-lg tracking-wider">{cardNumber(card.card_number)}</p>
      <div className="mt-2 flex items-center justify-between">
        <span className="text-sm opacity-90">{card.holder_name}</span>
        <span onClick={(e) => e.stopPropagation()}>
          <CopyButton value={card.card_number} />
        </span>
      </div>
    </div>
  )
}

function PaymentBlock({ order }) {
  const { t } = useTranslation()
  const cards = order.payment_cards ?? []
  const [picked, setPicked] = useState(null)
  const cardId = picked ?? cards[0]?.id ?? null // first card until the customer picks one
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const input = useRef(null)
  const submit = useSubmitPayment(order.id)
  const { refetch } = useOrder(order.id)
  const onExpire = useCallback(() => setTimeout(refetch, 1500), [refetch])

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function send() {
    submit.mutate(
      { file, cardId },
      {
        onSuccess: () => {
          haptic.success()
          toast.show(t('order.receipt_sent'))
        },
        onError: (err) => {
          haptic.error()
          toast.error(err)
        },
      },
    )
  }

  return (
    <Section title={t('order.pay_title')}>
      <div className="mb-4 flex items-center justify-between rounded-xl bg-amber-50 px-4 py-3">
        <span className="text-sm text-amber-900">{t('order.time_left')}</span>
        <Countdown until={order.expires_at} onExpire={onExpire} />
      </div>

      <ol className="space-y-4">
        <li>
          <p className="mb-2 text-sm font-medium text-ink">
            <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-600 text-[11px] font-bold text-white">1</span>
            {t('order.pay_step1', { amount: money(order.total) })}
          </p>
          <div className="mb-3 flex items-center justify-between rounded-xl border border-rose-200 bg-white px-4 py-2.5">
            <div>
              <p className="text-xs text-ink-soft">{t('order.amount')}</p>
              <p className="text-lg font-bold tabular-nums text-ink">{money(order.total)}</p>
            </div>
            <span className="rounded-full bg-rose-600 text-white">
              <CopyButton value={String(order.total)} />
            </span>
          </div>
          {cards.length ? (
            <div className="space-y-2.5">
              {cards.map((c) => (
                <PaymentCard key={c.id} card={c} selected={c.id === cardId} onSelect={() => setPicked(c.id)} />
              ))}
            </div>
          ) : (
            <p className="rounded-xl bg-red-50 p-3 text-sm text-red-800">{t('order.no_cards')}</p>
          )}
        </li>
        <li>
          <p className="mb-2 text-sm font-medium text-ink">
            <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-600 text-[11px] font-bold text-white">2</span>
            {t('order.pay_step2')}
          </p>
          <input
            ref={input}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/heic"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
          />
          {preview ? (
            <div className="space-y-2.5">
              <img src={preview} alt="" className="max-h-72 w-full rounded-xl border border-rose-100 bg-white object-contain" />
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => input.current?.click()}>
                  {t('order.change_receipt')}
                </Button>
                <Button className="flex-1" loading={submit.isPending} onClick={send}>
                  {t('order.send_receipt')}
                </Button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => input.current?.click()}
              className="flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed border-rose-300 bg-rose-50/50 py-8 text-rose-700 active:bg-rose-50"
            >
              <ImageIcon className="h-8 w-8" />
              <span className="text-sm font-semibold">{t('order.choose_receipt')}</span>
            </button>
          )}
        </li>
      </ol>
    </Section>
  )
}

function OrderSkeleton() {
  return (
    <div className="space-y-3 p-4">
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

export default function OrderPage() {
  const { id } = useParams()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { state } = useLocation()
  const { data: meta } = useMeta()
  const { data: order, isPending, isError, error, refetch } = useOrder(id)
  const cancel = useCancelOrder(id)

  if (isPending) return <OrderSkeleton />
  if (isError) {
    return error?.status === 404 ? (
      <EmptyState icon={PackageIcon} title={t('errors.NOT_FOUND')} action={<Button variant="outline" onClick={() => navigate('/orders')}>{t('orders.title')}</Button>} />
    ) : (
      <ErrorState error={error} onRetry={refetch} />
    )
  }

  const region = meta?.regions.find((r) => r.code === order.region)

  async function onCancel() {
    if (!(await confirmDialog(t('order.cancel_confirm')))) return
    cancel.mutate(undefined, { onError: toast.error })
  }

  return (
    <div className="space-y-3 px-4 pb-10 pt-4">
      {state?.created && order.status === 'awaiting_payment' && (
        <div className="flex items-center gap-3 rounded-2xl bg-emerald-50 p-4 text-emerald-800">
          <CheckIcon className="h-6 w-6 shrink-0" />
          <p className="font-semibold">{t('order.created')}</p>
        </div>
      )}

      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-serif text-3xl font-semibold leading-none">
            {t('order.title', { n: '' })}
            <span className="font-sans text-[26px] font-bold tracking-tight">{order.number}</span>
          </h1>
          <p className="mt-1.5 text-sm text-ink-soft">{dateTime(order.created_at)}</p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {order.status === 'cancelled' ? (
        <div className="rounded-2xl bg-stone-100 p-4 text-sm text-stone-700">
          <p className="font-semibold">{t(`order.cancel_reason.${order.cancel_reason}`)}</p>
          {order.payment?.reject_reason && (
            <p className="mt-1">
              {t('order.reject_reason')}: {order.payment.reject_reason}
            </p>
          )}
        </div>
      ) : (
        <Section>
          <OrderTimeline status={order.status} />
          {t(`order.hint.${order.status}`, { defaultValue: '' }) && (
            <p className="mt-4 text-center text-sm text-ink-soft">{t(`order.hint.${order.status}`)}</p>
          )}
          {order.tracking_number && (
            <div className="mt-3 flex items-center justify-between rounded-xl bg-violet-50 px-4 py-3 text-violet-900">
              <span className="flex items-center gap-2 text-sm">
                <TruckIcon className="h-5 w-5" />
                {t('order.tracking')}: <b className="font-mono">{order.tracking_number}</b>
              </span>
              <button type="button" onClick={() => copyText(order.tracking_number).then(() => toast.show(t('common.copied')))}>
                <CopyIcon className="h-5 w-5" />
              </button>
            </div>
          )}
          {order.delivery_info && (
            <div className="mt-3 rounded-xl bg-violet-50 px-4 py-3 text-violet-900">
              <p className="mb-1 flex items-center gap-2 text-sm font-semibold">
                <TruckIcon className="h-5 w-5" />
                {t('order.delivery_info')}
              </p>
              <LinkifiedText text={order.delivery_info} className="text-sm" />
            </div>
          )}
        </Section>
      )}

      {order.status === 'awaiting_payment' && <PaymentBlock order={order} />}

      <Section title={t('order.items')}>
        <ul className="divide-y divide-rose-100">
          {order.items.map((it) => (
            <li key={it.id} className="flex gap-3 py-3 first:pt-0 last:pb-0">
              <Link to={it.product_id ? `/product/${it.product_id}` : '#'} className="shrink-0">
                <ProductImage image={it.image} alt="" className="h-20 w-[3.75rem] rounded-lg" />
              </Link>
              <div className="min-w-0 flex-1">
                <p className="line-clamp-2 text-sm font-medium">{pick(it, 'name')}</p>
                <p className="mt-0.5 text-xs text-ink-soft">
                  {[pick(it, 'color'), it.size].filter(Boolean).join(' · ')}
                </p>
                <p className="mt-1 text-sm tabular-nums text-ink-soft">
                  {it.quantity} × {money(it.unit_price)}
                </p>
              </div>
              <span className="text-sm font-semibold tabular-nums">{money(it.line_total)}</span>
            </li>
          ))}
        </ul>
        <dl className="mt-3 space-y-1.5 border-t border-rose-100 pt-3 text-sm">
          {order.discount > 0 && (
            <>
              <div className="flex justify-between text-ink-soft">
                <dt>{t('cart.subtotal')}</dt>
                <dd className="tabular-nums">{money(order.subtotal)}</dd>
              </div>
              <div className="flex justify-between text-emerald-700">
                <dt>{t('cart.discount')}</dt>
                <dd className="tabular-nums">−{money(order.discount)}</dd>
              </div>
            </>
          )}
          <div className="flex justify-between text-base font-semibold">
            <dt>{t('cart.total')}</dt>
            <dd className="tabular-nums">{money(order.total)}</dd>
          </div>
        </dl>
      </Section>

      <Section title={t('order.delivery')}>
        <dl className="space-y-1 text-sm">
          <dd className="font-medium">
            {order.contact_name} · {phone(order.contact_phone)}
          </dd>
          <dd className="text-ink-soft">
            {[localized(region), order.district, order.address].filter(Boolean).join(', ')}
          </dd>
          <dd className="text-ink-soft">{t(`order.methods.${order.delivery_method}`)}</dd>
          {order.customer_note && <dd className="italic text-ink-soft">“{order.customer_note}”</dd>}
        </dl>
      </Section>

      {order.status === 'awaiting_payment' && (
        <Button variant="danger" className="w-full" loading={cancel.isPending} onClick={onCancel}>
          {t('order.cancel')}
        </Button>
      )}
    </div>
  )
}
