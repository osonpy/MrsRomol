import { useState } from 'react'
import { BookIcon, PlusIcon } from '../../components/icons'
import { Button, EmptyState, ErrorState, Sheet, Skeleton } from '../../components/ui'
import { adminKeys, useListMutation, usePromos } from '../../hooks/admin'
import { api } from '../../lib/api'
import { haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'
import { AdminHeader } from './AdminLayout'
import { dateTime, money } from './uz'

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 shrink-0 rounded-full transition ${checked ? 'bg-rose-600' : 'bg-rose-200'}`}
    >
      <span className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all ${checked ? 'left-[1.375rem]' : 'left-0.5'}`} />
    </button>
  )
}

function PromoSheet({ onClose }) {
  const [form, setForm] = useState({
    code: '',
    discount_type: 'percent',
    discount_value: '',
    min_order_amount: '',
    max_uses: '',
    per_customer_limit: '1',
    ends_at: '',
  })
  const set = (patch) => setForm((f) => ({ ...f, ...patch }))
  const digits = (v) => v.replace(/\D/g, '')
  const create = useListMutation(adminKeys.promos, (body) => api.post('/admin/promo-codes', body))
  const value = Number(form.discount_value)
  const valid = /^[A-Za-z0-9_-]{3,32}$/.test(form.code) && value > 0 && (form.discount_type === 'fixed' || value <= 100)

  function submit() {
    create.mutate(
      {
        code: form.code.toUpperCase(),
        discount_type: form.discount_type,
        discount_value: value,
        min_order_amount: Number(form.min_order_amount) || 0,
        max_uses: form.max_uses ? Number(form.max_uses) : null,
        per_customer_limit: Number(form.per_customer_limit) || 1,
        // End of the chosen day, Tashkent time.
        ends_at: form.ends_at ? `${form.ends_at}T23:59:59+05:00` : null,
      },
      {
        onSuccess: () => {
          haptic.success()
          toast.show('Promokod yaratildi')
          onClose()
        },
        onError: (err) => toast.error(err.code === 'CONFLICT' ? 'Bu kod allaqachon bor' : err),
      },
    )
  }

  return (
    <Sheet
      open
      onClose={onClose}
      title="Yangi promokod"
      footer={
        <Button className="w-full" disabled={!valid} loading={create.isPending} onClick={submit}>
          Yaratish
        </Button>
      }
    >
      <div className="space-y-3">
        <label className="block">
          <span className="label">Kod (lotin harflari va raqamlar)</span>
          <input
            className="field font-mono uppercase"
            autoCapitalize="characters"
            value={form.code}
            onChange={(e) => set({ code: e.target.value.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 32) })}
            placeholder="BAHOR10"
          />
        </label>
        <div>
          <span className="label">Chegirma turi</span>
          <div className="flex gap-2">
            {[
              ['percent', 'Foiz (%)'],
              ['fixed', 'Summa (soʻm)'],
            ].map(([v, label]) => (
              <button
                key={v}
                type="button"
                onClick={() => set({ discount_type: v })}
                className={`chip flex-1 justify-center ${form.discount_type === v ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <label className="block">
          <span className="label">{form.discount_type === 'percent' ? 'Necha foiz (1–100)' : 'Necha soʻm'}</span>
          <input className="field" inputMode="numeric" value={form.discount_value} onChange={(e) => set({ discount_value: digits(e.target.value) })} />
        </label>
        <label className="block">
          <span className="label">Minimal xarid summasi (ixtiyoriy)</span>
          <input className="field" inputMode="numeric" value={form.min_order_amount} onChange={(e) => set({ min_order_amount: digits(e.target.value) })} placeholder="0" />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="label">Jami necha marta</span>
            <input className="field" inputMode="numeric" value={form.max_uses} onChange={(e) => set({ max_uses: digits(e.target.value) })} placeholder="Cheksiz" />
          </label>
          <label className="block">
            <span className="label">Bir mijozga</span>
            <input className="field" inputMode="numeric" value={form.per_customer_limit} onChange={(e) => set({ per_customer_limit: digits(e.target.value) })} />
          </label>
        </div>
        <label className="block">
          <span className="label">Amal qilish muddati (ixtiyoriy)</span>
          <input className="field" type="date" value={form.ends_at} onChange={(e) => set({ ends_at: e.target.value })} />
        </label>
      </div>
    </Sheet>
  )
}

export default function PromoPage() {
  const { data, isPending, isError, error, refetch } = usePromos()
  const [creating, setCreating] = useState(false)
  const toggle = useListMutation(adminKeys.promos, ({ id, is_active }) => api.patch(`/admin/promo-codes/${id}`, { is_active }))

  return (
    <div className="pb-6">
      <AdminHeader
        title="Promokodlar"
        right={
          <Button className="h-10 px-4 text-sm" onClick={() => setCreating(true)}>
            <PlusIcon className="h-5 w-5" /> Yangi
          </Button>
        }
      />
      {isPending ? (
        <div className="space-y-2 px-4">
          <Skeleton className="h-20 w-full rounded-2xl" />
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.promo_codes.length === 0 ? (
        <EmptyState icon={BookIcon} title="Promokod yoʻq" text="Aksiyalar uchun chegirma kodlari yarating" action={<Button onClick={() => setCreating(true)}>Yaratish</Button>} />
      ) : (
        <ul className="space-y-2 px-4">
          {data.promo_codes.map((p) => {
            const expired = p.ends_at && new Date(p.ends_at) < new Date()
            const exhausted = p.max_uses != null && p.used_count >= p.max_uses
            return (
              <li key={p.id} className={`card flex items-center gap-3 p-4 ${!p.is_active || expired || exhausted ? 'opacity-60' : ''}`}>
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-lg font-bold">{p.code}</p>
                  <p className="text-sm text-rose-700">
                    −{p.discount_type === 'percent' ? `${p.discount_value}%` : money(p.discount_value)}
                    {p.min_order_amount > 0 && <span className="text-ink-soft"> · {money(p.min_order_amount)} dan</span>}
                  </p>
                  <p className="mt-0.5 text-xs text-ink-soft">
                    Ishlatilgan: {p.used_count}
                    {p.max_uses != null && ` / ${p.max_uses}`}
                    {p.ends_at && ` · ${expired ? 'muddati tugagan' : `${dateTime(p.ends_at).split(',')[0]} gacha`}`}
                  </p>
                </div>
                <Toggle checked={p.is_active} onChange={(v) => toggle.mutate({ id: p.id, is_active: v }, { onError: toast.error })} />
              </li>
            )
          })}
        </ul>
      )}
      {creating && <PromoSheet onClose={() => setCreating(false)} />}
    </div>
  )
}
