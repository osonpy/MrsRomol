import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate } from 'react-router-dom'
import { CheckIcon, ChevronDownIcon, ClockIcon, MapPinIcon, PhoneIcon } from '../components/icons'
import { Button, PageTitle, Section, StickyBar } from '../components/ui'
import { toast } from '../lib/toast'
import { useCreateOrder, useMeta, useQuote } from '../hooks/queries'
import { errorText } from '../i18n'
import { localized, money } from '../lib/format'
import { canRequestPhone, haptic, requestLocation, requestPhone } from '../lib/telegram'
import { useCart } from '../store/cart'

const LAST_DELIVERY = 'mrs-romol-delivery'
const PHONE_RE = /^\+?[0-9 ()-]{7,20}$/

function methodsFor(region) {
  return region === 'tashkent_city' ? ['taxi'] : ['post', 'bts']
}

function loadLast() {
  try {
    return JSON.parse(localStorage.getItem(LAST_DELIVERY)) || {}
  } catch {
    return {}
  }
}

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs font-medium text-red-700">{error}</span>}
    </label>
  )
}

function Check({ checked, onChange, children }) {
  return (
    <label className="flex cursor-pointer items-start gap-3 py-1.5">
      <input type="checkbox" className="peer sr-only" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span
        className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition ${
          checked ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-300 bg-white'
        } peer-focus-visible:ring-2 peer-focus-visible:ring-rose-200`}
      >
        {checked && <CheckIcon className="h-3.5 w-3.5 stroke-[3]" />}
      </span>
      <span className="text-sm text-ink">{children}</span>
    </label>
  )
}

export default function CheckoutPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: meta } = useMeta()
  const { items, promoCode, clear } = useCart()
  const quote = useQuote(items, promoCode)
  const createOrder = useCreateOrder()

  const [form, setForm] = useState(() => {
    const last = loadLast()
    return {
      contact_name: last.contact_name || meta?.me?.full_name || '',
      contact_phone: last.contact_phone || meta?.me?.phone || '',
      region: last.region || '',
      district: last.district || '',
      address: last.address || '',
      delivery_method: last.delivery_method || '',
      customer_note: '',
      location: null,
    }
  })
  const [agreeDelivery, setAgreeDelivery] = useState(false)
  const [agreeReturns, setAgreeReturns] = useState(false)
  const [touched, setTouched] = useState(false)
  const [locating, setLocating] = useState(false)
  const set = (patch) => setForm((f) => ({ ...f, ...patch }))

  // Keep the delivery method valid for the chosen region.
  useEffect(() => {
    if (!form.region) return
    const allowed = methodsFor(form.region)
    if (!allowed.includes(form.delivery_method)) setForm((f) => ({ ...f, delivery_method: allowed[0] }))
  }, [form.region, form.delivery_method])

  if (items.length === 0 && !createOrder.isSuccess) return <Navigate to="/cart" replace />

  const errors = {
    contact_name: !form.contact_name.trim() && t('checkout.required'),
    contact_phone: !PHONE_RE.test(form.contact_phone.trim()) && t('checkout.required'),
    region: !form.region && t('checkout.required'),
    address: !form.address.trim() && t('checkout.required'),
  }
  const valid = !Object.values(errors).some(Boolean) && agreeDelivery && agreeReturns
  const q = quote.data

  async function sharePhone() {
    const phone = await requestPhone()
    if (phone) set({ contact_phone: phone })
  }

  async function addLocation() {
    setLocating(true)
    const loc = await requestLocation()
    setLocating(false)
    if (loc) {
      haptic.success()
      set({ location: loc })
      toast.show(t('checkout.location_ok'))
    } else {
      toast.error(t('checkout.location_fail'))
    }
  }

  function submit() {
    setTouched(true)
    if (!valid) {
      haptic.error()
      return
    }
    const { location, ...delivery } = form
    const body = {
      items: items.map((i) => ({ variant_id: i.variant_id, quantity: i.quantity })),
      promo_code: promoCode || null,
      delivery: {
        ...delivery,
        contact_name: delivery.contact_name.trim(),
        contact_phone: delivery.contact_phone.trim(),
        address: delivery.address.trim(),
        location_lat: location?.lat ?? null,
        location_lng: location?.lng ?? null,
      },
    }
    createOrder.mutate(body, {
      onSuccess: (order) => {
        haptic.success()
        const { contact_name, contact_phone, region, district, address, delivery_method } = form
        localStorage.setItem(LAST_DELIVERY, JSON.stringify({ contact_name, contact_phone, region, district, address, delivery_method }))
        clear()
        navigate(`/orders/${order.id}`, { replace: true, state: { created: true } })
      },
      onError: (err) => {
        haptic.error()
        if (err.code?.startsWith('PROMO_')) {
          toast.error(t(`promo_errors.${err.code}`, { amount: money(err.detail?.min_order_amount) }))
        } else {
          toast.error(errorText(err))
        }
        if (['OUT_OF_STOCK', 'PRODUCT_INACTIVE', 'VARIANT_NOT_FOUND'].includes(err.code) || err.code?.startsWith('PROMO_')) {
          navigate('/cart', { replace: true })
        }
      },
    })
  }

  const showErr = (k) => touched && errors[k]

  return (
    <div>
      <PageTitle>{t('checkout.title')}</PageTitle>

      <div className="space-y-3 px-4">
        <Section title={t('checkout.contact')}>
          <div className="space-y-3">
            <Field label={t('checkout.name')} error={showErr('contact_name')}>
              <input className="field" autoComplete="name" value={form.contact_name} onChange={(e) => set({ contact_name: e.target.value })} />
            </Field>
            <Field label={t('checkout.phone')} error={showErr('contact_phone')}>
              <input
                className="field"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="+998 90 123 45 67"
                value={form.contact_phone}
                onChange={(e) => set({ contact_phone: e.target.value })}
              />
            </Field>
            {canRequestPhone && (
              <button type="button" onClick={sharePhone} className="flex items-center gap-2 text-sm font-semibold text-rose-700">
                <PhoneIcon className="h-4 w-4" />
                {t('checkout.share_phone')}
              </button>
            )}
          </div>
        </Section>

        <Section title={t('checkout.delivery')}>
          <div className="space-y-3">
            <Field label={t('checkout.region')} error={showErr('region')}>
              <div className="relative">
                <select
                  className="field appearance-none pr-10"
                  value={form.region}
                  onChange={(e) => set({ region: e.target.value })}
                >
                  <option value="" disabled>
                    {t('checkout.choose_region')}
                  </option>
                  {meta?.regions.map((r) => (
                    <option key={r.code} value={r.code}>
                      {localized(r)}
                    </option>
                  ))}
                </select>
                <ChevronDownIcon className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
              </div>
            </Field>

            {form.region && form.region !== 'tashkent_city' && (
              <Field label={t('checkout.district')}>
                <input className="field" value={form.district} onChange={(e) => set({ district: e.target.value })} />
              </Field>
            )}

            <Field label={t('checkout.address')} error={showErr('address')}>
              <textarea
                className="field min-h-[5rem] resize-none"
                placeholder={t('checkout.address_ph')}
                value={form.address}
                onChange={(e) => set({ address: e.target.value })}
              />
            </Field>

            {form.region === 'tashkent_city' && (
              <Button variant={form.location ? 'secondary' : 'outline'} className="w-full" loading={locating} onClick={addLocation}>
                {form.location ? <CheckIcon className="h-5 w-5" /> : <MapPinIcon className="h-5 w-5" />}
                {form.location ? t('checkout.location_ok') : t('checkout.location')}
              </Button>
            )}

            {form.region && (
              <div>
                <span className="label">{t('checkout.method')}</span>
                <div className="flex gap-2">
                  {methodsFor(form.region).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => set({ delivery_method: m })}
                      className={`chip ${
                        form.delivery_method === m ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'
                      }`}
                    >
                      {localized(meta?.delivery_methods.find((d) => d.code === m))}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-ink-soft">
                  {t(form.region === 'tashkent_city' ? 'checkout.method_hint_taxi' : 'checkout.method_hint_region')}{' '}
                  {t('cart.delivery_note')}
                </p>
              </div>
            )}

            <Field label={t('checkout.note')}>
              <input
                className="field"
                placeholder={t('checkout.note_ph')}
                value={form.customer_note}
                onChange={(e) => set({ customer_note: e.target.value })}
              />
            </Field>
          </div>
        </Section>

        <Section title={t('checkout.summary')}>
          <dl className="space-y-1.5 text-sm">
            <div className="flex justify-between text-ink-soft">
              <dt>{t('cart.subtotal')}</dt>
              <dd className="tabular-nums">{q ? money(q.subtotal) : '…'}</dd>
            </div>
            {q?.discount > 0 && (
              <div className="flex justify-between text-emerald-700">
                <dt>{t('cart.discount')}</dt>
                <dd className="tabular-nums">−{money(q.discount)}</dd>
              </div>
            )}
            <div className="flex justify-between pt-1 text-base font-semibold">
              <dt>{t('cart.total')}</dt>
              <dd className="tabular-nums">{q ? money(q.total) : '…'}</dd>
            </div>
          </dl>
          <p className="mt-3 flex gap-2 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">
            <ClockIcon className="h-4 w-4 shrink-0" />
            {t('checkout.reservation', { minutes: meta?.reservation_minutes ?? 30 })}
          </p>
          <div className="mt-3">
            <Check checked={agreeDelivery} onChange={setAgreeDelivery}>
              {t('checkout.agree_delivery')}
            </Check>
            <Check checked={agreeReturns} onChange={setAgreeReturns}>
              {t('checkout.agree_returns')}
            </Check>
          </div>
        </Section>
      </div>

      <StickyBar>
        <Button className="w-full" onClick={submit} loading={createOrder.isPending} disabled={touched && !valid}>
          {t('checkout.place_order', { total: q ? money(q.total) : '' })}
        </Button>
      </StickyBar>
    </div>
  )
}
