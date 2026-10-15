import { useState } from 'react'
import { PlusIcon, ShieldIcon, TrashIcon } from '../../components/icons'
import { Button, EmptyState, ErrorState, Sheet, Skeleton } from '../../components/ui'
import { adminKeys, useCards, useListMutation } from '../../hooks/admin'
import { api } from '../../lib/api'
import { cardNumber } from '../../lib/format'
import { confirmDialog, haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'
import { AdminHeader } from './AdminLayout'

const TYPES = ['uzcard', 'humo', 'visa', 'mastercard']

// Guess the card type from the first digits: 8600/5614 Uzcard, 9860 Humo.
function guessType(digits) {
  if (/^(8600|5614)/.test(digits)) return 'uzcard'
  if (/^9860/.test(digits)) return 'humo'
  if (/^4/.test(digits)) return 'visa'
  if (/^5[1-5]/.test(digits)) return 'mastercard'
  return null
}

function CardSheet({ onClose }) {
  const [number, setNumber] = useState('')
  const [holder, setHolder] = useState('')
  const [type, setType] = useState('uzcard')
  const create = useListMutation(adminKeys.cards, (body) => api.post('/admin/payment-cards', body))
  const digits = number.replace(/\D/g, '')
  const valid = digits.length === 16 && holder.trim()

  return (
    <Sheet
      open
      onClose={onClose}
      title="Yangi karta"
      footer={
        <Button
          className="w-full"
          disabled={!valid}
          loading={create.isPending}
          onClick={() =>
            create.mutate(
              { card_number: digits, holder_name: holder.trim().toUpperCase(), card_type: type },
              { onSuccess: () => (haptic.success(), toast.show('Karta qoʻshildi'), onClose()), onError: toast.error },
            )
          }
        >
          Qoʻshish
        </Button>
      }
    >
      <div className="space-y-3">
        <label className="block">
          <span className="label">Karta raqami (16 xona)</span>
          <input
            className="field font-mono tracking-wider"
            inputMode="numeric"
            value={cardNumber(digits)}
            onChange={(e) => {
              const d = e.target.value.replace(/\D/g, '').slice(0, 16)
              setNumber(d)
              const guess = guessType(d)
              if (guess) setType(guess)
            }}
            placeholder="8600 0000 0000 0000"
          />
        </label>
        <label className="block">
          <span className="label">Karta egasi (mijozga koʻrinadi)</span>
          <input className="field uppercase" value={holder} onChange={(e) => setHolder(e.target.value)} placeholder="MAKHMUD A." />
        </label>
        <div>
          <span className="label">Turi</span>
          <div className="flex flex-wrap gap-2">
            {TYPES.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setType(t)}
                className={`chip uppercase ${type === t ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Sheet>
  )
}

export default function CardsPage() {
  const { data, isPending, isError, error, refetch } = useCards()
  const [adding, setAdding] = useState(false)
  const toggle = useListMutation(adminKeys.cards, ({ id, is_active }) => api.patch(`/admin/payment-cards/${id}`, { is_active }))
  const remove = useListMutation(adminKeys.cards, (id) => api.delete(`/admin/payment-cards/${id}`))

  async function onDelete(c) {
    if (!(await confirmDialog(`${cardNumber(c.card_number)} kartasi oʻchirilsinmi?`))) return
    remove.mutate(c.id, { onSuccess: () => toast.show('Oʻchirildi'), onError: toast.error })
  }

  return (
    <div className="pb-6">
      <AdminHeader
        title="Toʻlov kartalari"
        right={
          <Button className="h-10 px-4 text-sm" onClick={() => setAdding(true)}>
            <PlusIcon className="h-5 w-5" /> Qoʻshish
          </Button>
        }
      />
      {isPending ? (
        <Skeleton className="mx-4 h-28 rounded-2xl" />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.cards.length === 0 ? (
        <EmptyState
          icon={ShieldIcon}
          title="Karta qoʻshilmagan"
          text="Kartasiz mijozlar toʻlov qila olmaydi — kamida bittasini qoʻshing"
          action={<Button onClick={() => setAdding(true)}>Karta qoʻshish</Button>}
        />
      ) : (
        <ul className="space-y-3 px-4">
          {data.cards.map((c) => (
            <li key={c.id} className={`card p-4 ${c.is_active ? '' : 'opacity-60'}`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-widest text-ink-soft">{c.card_type}</span>
                <button type="button" aria-label="delete" onClick={() => onDelete(c)} className="p-1 text-ink-faint">
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
              <p className="mt-1 font-mono text-lg tracking-wider">{cardNumber(c.card_number)}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-sm text-ink-soft">{c.holder_name}</span>
                <label className="flex items-center gap-2 text-sm">
                  {c.is_active ? 'Faol' : 'Oʻchiq'}
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-rose-600"
                    checked={c.is_active}
                    onChange={(e) => toggle.mutate({ id: c.id, is_active: e.target.checked }, { onError: toast.error })}
                  />
                </label>
              </div>
            </li>
          ))}
        </ul>
      )}
      {adding && <CardSheet onClose={() => setAdding(false)} />}
    </div>
  )
}
