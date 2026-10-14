import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { BagIcon, CheckIcon, InfoIcon, TrashIcon } from '../components/icons'
import { QtyStepper } from '../components/order'
import { ProductImage } from '../components/product'
import { Button, EmptyState, PageTitle, Section, StickyBar } from '../components/ui'
import { useQuote } from '../hooks/queries'
import { money, pick } from '../lib/format'
import { haptic } from '../lib/telegram'
import { useCart } from '../store/cart'

function variantText(line) {
  return [pick(line, 'color'), line.size].filter(Boolean).join(' · ')
}

function PromoBox({ quote }) {
  const { t } = useTranslation()
  const { promoCode, setPromo } = useCart()
  const [text, setText] = useState(promoCode)
  const promo = quote?.promo

  return (
    <div>
      <div className="flex gap-2">
        <input
          className="field h-11 py-0 uppercase"
          placeholder={t('cart.promo')}
          value={text}
          autoCapitalize="characters"
          onChange={(e) => setText(e.target.value.replace(/\s/g, ''))}
        />
        <Button variant="outline" className="h-11 shrink-0" onClick={() => setPromo(text.trim())} disabled={text.trim() === promoCode}>
          {t('cart.apply')}
        </Button>
      </div>
      {promoCode && promo && (
        <p className={`mt-2 flex items-center gap-1.5 text-sm ${promo.valid ? 'text-emerald-700' : 'text-red-700'}`}>
          {promo.valid && <CheckIcon className="h-4 w-4" />}
          {promo.valid
            ? t('cart.promo_ok')
            : t(`promo_errors.${promo.error_code}`, { amount: money(promo.detail?.min_order_amount) })}
        </p>
      )}
    </div>
  )
}

export default function CartPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { items, promoCode, setQuantity, remove } = useCart()
  const quote = useQuote(items, promoCode)

  if (items.length === 0) {
    return (
      <>
        <PageTitle>{t('cart.title')}</PageTitle>
        <EmptyState
          icon={BagIcon}
          title={t('cart.empty_title')}
          text={t('cart.empty_text')}
          action={<Button onClick={() => navigate('/')}>{t('cart.to_catalog')}</Button>}
        />
      </>
    )
  }

  const q = quote.data
  const issues = Object.fromEntries((q?.issues ?? []).map((i) => [i.variant_id, i]))
  const linesById = Object.fromEntries((q?.lines ?? []).map((l) => [l.variant_id, l]))
  const hasIssues = (q?.issues ?? []).length > 0

  return (
    <div>
      <PageTitle>{t('cart.title')}</PageTitle>

      <ul className="space-y-3 px-4">
        {items.map((item) => {
          const line = linesById[item.variant_id]
          const issue = issues[item.variant_id]
          const gone = issue && issue.code !== 'OUT_OF_STOCK'
          const price = line?.unit_price ?? item.price
          return (
            <li key={item.variant_id} className={`card flex gap-3 p-3 ${issue ? 'ring-1 ring-red-200' : ''}`}>
              <Link to={`/product/${item.product_id}`} className="shrink-0">
                <ProductImage image={line?.image ?? item.image} alt="" className={`h-28 w-[5.25rem] rounded-xl ${gone ? 'opacity-50' : ''}`} />
              </Link>
              <div className="flex min-w-0 flex-1 flex-col">
                <div className="flex items-start justify-between gap-2">
                  <Link to={`/product/${item.product_id}`} className="line-clamp-2 text-sm font-medium leading-snug text-ink">
                    {pick(line ?? item, 'name')}
                  </Link>
                  <button
                    type="button"
                    aria-label={t('cart.remove')}
                    onClick={() => (haptic.tap(), remove(item.variant_id))}
                    className="-mr-1 -mt-1 rounded-full p-1.5 text-ink-faint active:bg-rose-50"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
                <p className="mt-0.5 text-xs text-ink-soft">{variantText(line ?? item)}</p>

                {issue && (
                  <p className="mt-1 text-xs font-semibold text-red-700">
                    {gone ? t('cart.unavailable') : t('cart.only_left', { count: issue.available })}
                    {!gone && issue.available > 0 && (
                      <button type="button" className="ml-2 underline" onClick={() => setQuantity(item.variant_id, issue.available)}>
                        {t('cart.set_to_max', { count: issue.available })}
                      </button>
                    )}
                  </p>
                )}

                <div className="mt-auto flex items-end justify-between pt-2">
                  <span className="font-semibold text-rose-700">{money(price * item.quantity)}</span>
                  {!gone && (
                    <QtyStepper
                      value={item.quantity}
                      max={line?.available ?? 100}
                      onChange={(n) => (haptic.select(), setQuantity(item.variant_id, n))}
                    />
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      <div className="space-y-3 px-4 pt-4">
        <Section>
          <PromoBox quote={q} />
        </Section>

        <Section>
          <dl className="space-y-2 text-sm">
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
            <div className="flex justify-between border-t border-rose-100 pt-2 text-base font-semibold text-ink">
              <dt>{t('cart.total')}</dt>
              <dd className="tabular-nums">{q ? money(q.total) : '…'}</dd>
            </div>
          </dl>
          <p className="mt-3 flex gap-2 text-xs text-ink-soft">
            <InfoIcon className="h-4 w-4 shrink-0" />
            {t('cart.delivery_note')}
          </p>
        </Section>
      </div>

      <StickyBar aboveNav>
        {hasIssues && <p className="mb-2 text-center text-xs font-medium text-red-700">{t('cart.fix_issues')}</p>}
        <Button
          className="w-full"
          disabled={!q || hasIssues || quote.isFetching}
          loading={quote.isPending}
          onClick={() => navigate('/checkout')}
        >
          {t('cart.checkout')}
          {q && !hasIssues && <span className="font-normal opacity-90">· {money(q.total)}</span>}
        </Button>
      </StickyBar>
    </div>
  )
}
