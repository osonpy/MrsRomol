export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  onClick,
  type = 'button',
  className = '',
}) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed select-none'

  const sizes = { sm: 'px-3 py-2 text-xs', md: 'px-5 py-3 text-sm', lg: 'px-6 py-4 text-base' }

  const variantStyle =
    variant === 'primary'
      ? { background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }
      : variant === 'secondary'
      ? { background: 'var(--tg-theme-secondary-bg-color)', color: 'var(--tg-theme-text-color)' }
      : variant === 'ghost'
      ? { background: 'transparent', color: 'var(--tg-theme-text-color)' }
      : variant === 'danger'
      ? { background: '#ef4444', color: '#fff' }
      : {}

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      style={variantStyle}
      className={`${base} ${sizes[size] ?? sizes.md} ${fullWidth ? 'w-full' : ''} ${className}`}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  )
}
