import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckIcon, MinusIcon, PlusIcon } from './icons'

const STATUS_STYLE = {
  awaiting_payment: 'bg-amber-50 text-amber-800 ring-amber-200',
  payment_review: 'bg-sky-50 text-sky-800 ring-sky-200',
  confirmed: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  shipped: 'bg-violet-50 text-violet-800 ring-violet-200',
  delivered: 'bg-rose-50 text-rose-700 ring-rose-200',
  cancelled: 'bg-stone-100 text-stone-600 ring-stone-200',
}

export function StatusBadge({ status }) {
  const { t } = useTranslation()
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${STATUS_STYLE[status]}`}>
      {t(`order.status.${status}`)}
    </span>
  )
}

const STEPS = ['awaiting_payment', 'payment_review', 'confirmed', 'shipped', 'delivered']

export function OrderTimeline({ status }) {
  const { t } = useTranslation()
  const current = STEPS.indexOf(status)
  return (
    <ol className="flex items-start">
      {STEPS.map((step, i) => {
        const done = i < current || status === 'delivered'
        const active = i === current && status !== 'delivered'
        return (
          <li key={step} className="relative flex flex-1 flex-col items-center text-center">
            {i > 0 && (
              <span
                className={`absolute right-1/2 top-3 h-0.5 w-full -translate-y-1/2 ${i <= current ? 'bg-rose-400' : 'bg-rose-100'}`}
              />
            )}
            <span
              className={`relative z-10 flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
                done ? 'bg-rose-600 text-white' : active ? 'bg-white text-rose-700 ring-2 ring-rose-500' : 'bg-rose-100 text-rose-300'
              }`}
            >
              {done ? <CheckIcon className="h-3.5 w-3.5 stroke-[3]" /> : i + 1}
            </span>
            <span className={`mt-1.5 text-[10px] leading-tight ${done || active ? 'text-ink' : 'text-ink-faint'}`}>
              {t(`order.status.${step}`)}
            </span>
          </li>
        )
      })}
    </ol>
  )
}

// mm:ss until `until`; calls onExpire once when it reaches zero.
export function Countdown({ until, onExpire }) {
  const target = new Date(until).getTime()
  const [left, setLeft] = useState(() => Math.max(0, target - Date.now()))

  useEffect(() => {
    const id = setInterval(() => {
      const ms = Math.max(0, target - Date.now())
      setLeft(ms)
      if (ms === 0) {
        clearInterval(id)
        onExpire?.()
      }
    }, 1000)
    return () => clearInterval(id)
  }, [target, onExpire])

  const total = Math.ceil(left / 1000)
  const mm = String(Math.floor(total / 60)).padStart(2, '0')
  const ss = String(total % 60).padStart(2, '0')
  return (
    <span className={`font-mono text-2xl font-bold tabular-nums ${total < 300 ? 'text-red-700' : 'text-ink'}`}>
      {mm}:{ss}
    </span>
  )
}

export function QtyStepper({ value, max = 100, onChange, disabled }) {
  return (
    <div className="inline-flex h-9 items-center rounded-full border border-rose-200 bg-white">
      <button
        type="button"
        aria-label="-"
        disabled={disabled}
        onClick={() => onChange(value - 1)}
        className="flex h-9 w-9 items-center justify-center text-ink-soft active:text-rose-700 disabled:opacity-40"
      >
        <MinusIcon className="h-4 w-4" />
      </button>
      <span className="min-w-[1.75rem] text-center text-sm font-semibold tabular-nums">{value}</span>
      <button
        type="button"
        aria-label="+"
        disabled={disabled || value >= max}
        onClick={() => onChange(value + 1)}
        className="flex h-9 w-9 items-center justify-center text-ink-soft active:text-rose-700 disabled:opacity-40"
      >
        <PlusIcon className="h-4 w-4" />
      </button>
    </div>
  )
}
