export function PageWrapper({ children, className = '' }) {
  return (
    <div className={`min-h-screen pb-24 ${className}`} style={{ background: 'var(--tg-theme-bg-color)' }}>
      {children}
    </div>
  )
}
