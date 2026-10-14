import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { CheckIcon, CopyIcon, MapPinIcon, PhoneIcon, TruckIcon, XIcon } from '../../components/icons'
import { StatusBadge } from '../../components/order'
import { ProductImage } from '../../components/product'
import { Button, ErrorState, Section, Sheet, Skeleton, StickyBar } from '../../components/ui'
import { useAdminCancelOrder, useAdminOrder, useAdvanceOrder, useOrderNote, useReviewPayment } from '../../hooks/admin'
import { useMeta } from '../../hooks/queries'
import { cardNumber, phone } from '../../lib/format'
import { dateTime, money, t } from './uz'
import { copyText, haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'

const REJECT_REASONS = ['Chek oʻqilmaydi', 'Summa mos emas', 'Pul kelib tushmadi', 'Boshqa buyurtmaning cheki']

function ReasonSheet({ open, onClose, title, presets = [], placeholder, confirmLabel, danger, loading, onConfirm, required }) {
  const [text, setText] = useState('')
  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={title}
      footer={
        <Button
          className={`w-full ${danger ? '!bg-red-700' : ''}`}
          loading={loading}
          disabled={required && !text.trim()}
          onClick={() => onConfirm(text.trim())}
        >
          {confirmLabel}
        </Button>
      }
    >
      {presets.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {presets.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setText(p)}
              className={`chip ${text === p ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
      <textarea className="field min-h-[5rem] resize-none" placeholder={placeholder} value={text} onChange={(e) => setText(e.target.value)} />
    </Sheet>
  )
}

function Receipt({ payment }) {
  const [full, setFull] = useState(false)
  if (!payment?.receipt_url) return <p className="text-sm text-ink-soft">Chek rasmi topilmadi</p>
  return (
    <>
      <button type="button" onClick={() => setFull(true)} className="block w-full">
        <img src={payment.receipt_url} alt="Chek" className="max-h-96 w-full rounded-xl border border-rose-100 bg-white object-contain" />
      </button>
      <p className="mt-1.5 text-center text-xs text-ink-soft">Kattalashtirish uchun bosing</p>
      {full && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black" onClick={() => setFull(false)}>
          <img src={payment.receipt_url} alt="Chek" className="max-h-full max-w-full object-contain" />
          <button type="button" aria-label="close" className="absolute right-4 top-4 rounded-full bg-white/15 p-2.5 text-white">
            <XIcon className="h-6 w-6" />
          </button>
        </div>
      )}
    </>
  )
}

export default function AdminOrderPage() {
  const { id } = useParams()
  const { data: meta } = useMeta()
  const { data: o, isPending, isError, error, refetch } = useAdminOrder(id)
  const review = useReviewPayment(id)
  const advance = useAdvanceOrder(id)
  const cancel = useAdminCancelOrder(id)
  const saveNote = useOrderNote(id)
  const [sheet, setSheet] = useState(null) // 'reject' | 'ship' | 'cancel'
  const [note, setNote] = useState(null)

  if (isPending) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    )
  }
  if (isError) return <ErrorState error={error} onRetry={refetch} />

  const run = (mutation, args, message) =>
    mutation.mutate(args, {
      onSuccess: () => {
        haptic.success()
        toast.show(message)
        setSheet(null)
      },
      onError: (err) => {
        haptic.error()
        toast.error(err)
        refetch()
      },
    })

  const region = meta?.regions.find((r) => r.code === o.region)
  const mapUrl = o.location_lat != null ? `https://yandex.uz/maps/?pt=${o.location_lng},${o.location_lat}&z=17&l=map` : null
  const canCancel = ['awaiting_payment', 'payment_review', 'confirmed'].includes(o.status)
  const tgLink = o.customer?.telegram_id ? `tg://user?id=${o.customer.telegram_id}` : null

  return (
    <div className="space-y-3 px-4 pb-6 pt-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold leading-none tracking-tight">#{o.number}</h1>
          <p className="mt-1.5 text-sm text-ink-soft">{dateTime(o.created_at)}</p>
        </div>
        <StatusBadge status={o.status} lng="uz" />
      </div>

      {o.status === 'cancelled' && (
        <div className="rounded-2xl bg-stone-100 p-4 text-sm text-stone-700">
          <b>{t(`order.cancel_reason.${o.cancel_reason}`)}</b>
          {o.payment?.reject_reason && <p className="mt-1">Sabab: {o.payment.reject_reason}</p>}
        </div>
      )}

      {o.payment && (
        <Section title={`Chek · ${money(o.payment.amount)}`}>
          {o.payment.card && (
            <p className="mb-3 text-sm text-ink-soft">
              Karta: <b className="uppercase text-ink">{o.payment.card.card_type}</b> {cardNumber(o.payment.card.card_number)}
            </p>
          )}
          <Receipt payment={o.payment} />
          {o.payment.status !== 'pending_verification' && (
            <p className={`mt-3 text-sm font-semibold ${o.payment.status === 'verified' ? 'text-emerald-700' : 'text-red-700'}`}>
              {o.payment.status === 'verified' ? '✅ Tasdiqlangan' : '❌ Rad etilgan'} · {dateTime(o.payment.reviewed_at)}
            </p>
          )}
        </Section>
      )}

      <Section title="Mijoz">
        <p className="font-semibold">{o.contact_name}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <a href={`tel:${o.contact_phone}`} className="chip border-rose-200 bg-white text-ink">
            <PhoneIcon className="mr-1.5 h-4 w-4" />
            {phone(o.contact_phone)}
          </a>
          {tgLink && (
            <a href={tgLink} className="chip border-rose-200 bg-white text-ink">
              Telegram
            </a>
          )}
        </div>
      </Section>

      <Section title="Yetkazib berish">
        <p className="text-sm">
          <b>{t(`order.methods.${o.delivery_method}`)}</b> · {region?.uz}
          {o.district ? `, ${o.district}` : ''}
        </p>
        <div className="mt-1 flex items-start justify-between gap-3">
          <p className="text-sm text-ink-soft">{o.address}</p>
          <button type="button" aria-label="copy" onClick={() => copyText(`${o.contact_name}, ${o.contact_phone}, ${o.address}`).then(() => toast.show('Nusxalandi'))}>
            <CopyIcon className="h-5 w-5 text-ink-faint" />
          </button>
        </div>
        {mapUrl && (
          <a href={mapUrl} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1.5 text-sm font-semibold text-rose-700">
            <MapPinIcon className="h-4 w-4" /> Xaritada ochish
          </a>
        )}
        {o.customer_note && <p className="mt-2 rounded-lg bg-amber-50 p-2.5 text-sm text-amber-900">💬 {o.customer_note}</p>}
        {o.tracking_number && (
          <p className="mt-2 flex items-center gap-2 text-sm">
            <TruckIcon className="h-4 w-4 text-violet-700" /> Trek: <b className="font-mono">{o.tracking_number}</b>
          </p>
        )}
      </Section>

      <Section title={`Mahsulotlar · ${money(o.total)}`}>
        <ul className="divide-y divide-rose-100">
          {o.items.map((it) => (
            <li key={it.id} className="flex gap-3 py-2.5 first:pt-0 last:pb-0">
              <ProductImage image={it.image} alt="" className="h-16 w-12 shrink-0 rounded-lg" />
              <div className="min-w-0 flex-1 text-sm">
                <p className="font-medium">{it.name_uz}</p>
                <p className="text-ink-soft">{[it.color_uz, it.size].filter(Boolean).join(' · ')}</p>
              </div>
              <div className="text-right text-sm">
                <p className="font-bold">× {it.quantity}</p>
                <p className="text-ink-soft">{money(it.line_total)}</p>
              </div>
            </li>
          ))}
        </ul>
        {o.discount > 0 && <p className="mt-2 text-sm text-emerald-700">Chegirma: −{money(o.discount)}</p>}
      </Section>

      <Section title="Ichki izoh (mijoz koʻrmaydi)">
        <textarea
          className="field min-h-[4rem] resize-none"
          value={note ?? o.admin_note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Masalan: taksi raqami, kuryer ismi…"
        />
        {note !== null && note !== o.admin_note && (
          <Button variant="secondary" className="mt-2 h-10 w-full" loading={saveNote.isPending} onClick={() => run(saveNote, note, 'Saqlandi')}>
            Saqlash
          </Button>
        )}
      </Section>

      <Section title="Tarix">
        <ol className="space-y-2 text-sm">
          {o.history.map((h, i) => (
            <li key={i} className="flex justify-between gap-3">
              <span>
                {t(`order.status.${h.to_status}`)}
                {h.note && <span className="text-ink-soft"> — {h.note}</span>}
              </span>
              <span className="shrink-0 text-ink-soft">{dateTime(h.created_at)}</span>
            </li>
          ))}
        </ol>
      </Section>

      {canCancel && (
        <Button variant="danger" className="w-full" onClick={() => setSheet('cancel')}>
          Buyurtmani bekor qilish
        </Button>
      )}

      {o.status === 'payment_review' && o.payment && (
        <StickyBar>
          <div className="flex gap-3">
            <Button variant="danger" className="flex-1 px-3" onClick={() => setSheet('reject')}>
              <XIcon className="h-5 w-5" /> Rad etish
            </Button>
            <Button
              className="flex-1 !bg-emerald-700"
              loading={review.isPending}
              onClick={() => run(review, { paymentId: o.payment.id, approve: true }, 'Toʻlov tasdiqlandi')}
            >
              <CheckIcon className="h-5 w-5" /> Tasdiqlash
            </Button>
          </div>
        </StickyBar>
      )}
      {o.status === 'confirmed' && (
        <StickyBar>
          <Button className="w-full" onClick={() => setSheet('ship')}>
            <TruckIcon className="h-5 w-5" /> Yuborildi deb belgilash
          </Button>
        </StickyBar>
      )}
      {o.status === 'shipped' && (
        <StickyBar>
          <Button className="w-full" loading={advance.isPending} onClick={() => run(advance, { to: 'delivered' }, 'Yetkazildi')}>
            <CheckIcon className="h-5 w-5" /> Yetkazildi
          </Button>
        </StickyBar>
      )}

      <ReasonSheet
        open={sheet === 'reject'}
        onClose={() => setSheet(null)}
        title="Toʻlovni rad etish"
        presets={REJECT_REASONS}
        placeholder="Sabab (mijozga yuboriladi)"
        confirmLabel="Rad etish va bekor qilish"
        danger
        required
        loading={review.isPending}
        onConfirm={(reason) => run(review, { paymentId: o.payment?.id, approve: false, reason }, 'Rad etildi')}
      />
      <ReasonSheet
        open={sheet === 'ship'}
        onClose={() => setSheet(null)}
        title="Yuborildi"
        placeholder={o.delivery_method === 'taxi' ? 'Izoh: masalan, taksi raqami (ixtiyoriy)' : 'Trek raqami (pochta / BTS)'}
        confirmLabel="Tasdiqlash — mijozga xabar boradi"
        loading={advance.isPending}
        onConfirm={(text) =>
          run(advance, o.delivery_method === 'taxi' ? { to: 'shipped', note: text } : { to: 'shipped', tracking_number: text }, 'Yuborildi')
        }
      />
      <ReasonSheet
        open={sheet === 'cancel'}
        onClose={() => setSheet(null)}
        title="Bekor qilish"
        placeholder="Sabab (mijozga yuboriladi, ixtiyoriy)"
        confirmLabel="Bekor qilish — mahsulot omborga qaytadi"
        danger
        loading={cancel.isPending}
        onConfirm={(note) => run(cancel, note, 'Bekor qilindi')}
      />
    </div>
  )
}
