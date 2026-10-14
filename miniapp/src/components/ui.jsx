// Small shared building blocks.
import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { errorText } from '../i18n'
import { useToastStore } from '../lib/toast'
import { XIcon } from './icons'

// ── Button ────────────────────────────────────────────────────────────────────

const VARIANTS = {
  primary: 'bg-rose-600 text-white active:bg-rose-700 disabled:bg-rose-300',
  secondary: 'bg-rose-100 text-rose-700 active:bg-rose-200 disabled:opacity-50',
  outline: 'border border-rose-300 bg-white text-rose-700 active:bg-rose-50 disabled:opacity-50',
  ghost: 'text-rose-700 active:bg-rose-50 disabled:opacity-50',
  danger: 'border border-red-200 bg-white text-red-700 active:bg-red-50 disabled:opacity-50',
}

export function Button({ variant = 'primary', loading = false, className = '', children, disabled, ...props }) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={`inline-flex h-12 items-center justify-center gap-2 rounded-xl px-5 font-semibold transition
        active:scale-[0.98] disabled:active:scale-100 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {loading ? <Spinner className="h-5 w-5" /> : children}
    </button>
  )
}

export function Spinner({ className = 'h-6 w-6' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

// ── Bottom sheet ──────────────────────────────────────────────────────────────

export function Sheet({ open, onClose, title, children, footer }) {
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end" role="dialog" aria-modal="true">
      <div className="absolute inset-0 animate-fade-in bg-ink/40" onClick={onClose} />
      <div className="relative flex max-h-[88vh] w-full animate-slide-up flex-col rounded-t-3xl bg-cream shadow-sheet">
        <div className="mx-auto mt-2.5 h-1 w-10 rounded-full bg-rose-200" />
        <div className="flex items-center justify-between px-5 pb-2 pt-3">
          <h2 className="font-serif text-2xl font-semibold text-ink">{title}</h2>
          <button onClick={onClose} className="-mr-2 rounded-full p-2 text-ink-soft active:bg-rose-100" aria-label="close">
            <XIcon className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 pb-4">{children}</div>
        {footer && <div className="border-t border-rose-100 px-5 pb-safe pt-3">{footer}</div>}
      </div>
    </div>,
    document.body,
  )
}

// ── Toast ─────────────────────────────────────────────────────────────────────

export function Toaster() {
  const { message, tone } = useToastStore()
  if (!message) return null
  return (
    <div className="pointer-events-none fixed inset-x-0 top-3 z-[60] flex justify-center px-4">
      <div
        role="status"
        className={`animate-fade-in rounded-2xl px-4 py-3 text-sm font-medium shadow-card ${
          tone === 'error' ? 'bg-red-700 text-white' : 'bg-ink text-cream'
        }`}
      >
        {message}
      </div>
    </div>
  )
}

// ── States ────────────────────────────────────────────────────────────────────

export function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <div className="flex flex-col items-center px-8 py-16 text-center">
      {Icon && (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-100 text-rose-500">
          <Icon className="h-8 w-8" />
        </div>
      )}
      <h3 className="font-serif text-2xl font-semibold text-ink">{title}</h3>
      {text && <p className="mt-1.5 text-sm text-ink-soft">{text}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

export function ErrorState({ error, onRetry }) {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col items-center px-8 py-16 text-center">
      <p className="text-ink-soft">{errorText(error)}</p>
      {onRetry && (
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          {t('common.retry')}
        </Button>
      )}
    </div>
  )
}

export function Skeleton({ className = '' }) {
  return <div className={`skeleton rounded-xl ${className}`} />
}

// ── Page chrome ───────────────────────────────────────────────────────────────

export function PageTitle({ children, right }) {
  return (
    <div className="flex items-end justify-between px-4 pb-3 pt-4">
      <h1 className="font-serif text-3xl font-semibold leading-none text-ink">{children}</h1>
      {right}
    </div>
  )
}

// Fixed bar above the bottom nav (or at the very bottom when there is no nav).
export function StickyBar({ children, aboveNav = false }) {
  return (
    <>
      <div className={aboveNav ? 'h-24' : 'h-28'} />
      <div
        className={`fixed inset-x-0 z-30 border-t border-rose-100 bg-cream/95 px-4 pt-3 backdrop-blur ${
          aboveNav ? 'bottom-[calc(4rem+env(safe-area-inset-bottom))] pb-3' : 'bottom-0 pb-safe'
        }`}
      >
        {children}
      </div>
    </>
  )
}

export function Section({ title, children, className = '' }) {
  return (
    <section className={`card p-4 ${className}`}>
      {title && <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-soft">{title}</h2>}
      {children}
    </section>
  )
}
