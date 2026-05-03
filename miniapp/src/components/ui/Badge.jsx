const VARIANTS = {
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  danger:  'bg-red-100 text-red-700',
  info:    'bg-blue-100 text-blue-700',
  gray:    'bg-gray-100 text-gray-500',
  purple:  'bg-purple-100 text-purple-700',
  // legacy aliases
  green:   'bg-green-100 text-green-700',
  yellow:  'bg-yellow-100 text-yellow-700',
  red:     'bg-red-100 text-red-700',
  blue:    'bg-blue-100 text-blue-700',
}

export function Badge({ children, variant = 'gray', className = '' }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${VARIANTS[variant] ?? VARIANTS.gray} ${className}`}
    >
      {children}
    </span>
  )
}

export function statusBadge(status) {
  const map = {
    pending:   { emoji: '⏳', variant: 'warning' },
    confirmed: { emoji: '✅', variant: 'success' },
    shipped:   { emoji: '🚚', variant: 'info' },
    delivered: { emoji: '📬', variant: 'purple' },
    cancelled: { emoji: '❌', variant: 'danger' },
  }
  return map[status] ?? { emoji: '', variant: 'gray' }
}

export function paymentBadge(status) {
  const map = {
    pending_verification: { emoji: '⏳', variant: 'warning' },
    confirmed:            { emoji: '✅', variant: 'success' },
    rejected:             { emoji: '❌', variant: 'danger' },
  }
  return map[status] ?? { emoji: '', variant: 'gray' }
}
