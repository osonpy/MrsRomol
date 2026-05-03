import { useEffect } from 'react'

export function BottomSheet({ isOpen, onClose, title, children }) {
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div
        className="relative w-full rounded-t-3xl shadow-2xl max-h-[90dvh] flex flex-col"
        style={{
          background: 'var(--tg-theme-bg-color)',
          animation: 'slideUp 0.3s cubic-bezier(0.32, 0.72, 0, 1)',
        }}
      >
        <div className="flex justify-center pt-3 pb-1 flex-shrink-0">
          <div className="w-10 h-1 rounded-full" style={{ background: 'var(--tg-theme-hint-color)', opacity: 0.4 }} />
        </div>
        {title && (
          <div className="flex items-center justify-between px-4 pb-3 flex-shrink-0">
            <h3 className="text-base font-semibold" style={{ color: 'var(--tg-theme-text-color)' }}>
              {title}
            </h3>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full flex items-center justify-center active:opacity-60"
              style={{ background: 'var(--tg-theme-secondary-bg-color)', color: 'var(--tg-theme-text-color)' }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        )}
        <div className="overflow-y-auto px-4 pb-8 flex-1">{children}</div>
      </div>
      <style>{`@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }`}</style>
    </div>
  )
}
