import { useTranslation } from 'react-i18next'

const STEPS = ['pending', 'confirmed', 'shipped', 'delivered']

const STEP_ICONS = {
  pending:   '⏳',
  confirmed: '✅',
  shipped:   '🚚',
  delivered: '📬',
}

export function OrderTimeline({ status }) {
  const { t } = useTranslation()
  const currentIdx = STEPS.indexOf(status)
  if (status === 'cancelled') return null

  return (
    <div className="flex items-start gap-1">
      {STEPS.map((step, idx) => {
        const done = idx < currentIdx
        const active = idx === currentIdx

        return (
          <div key={step} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-base transition-all duration-300"
                style={{
                  background: done || active ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                  color: done || active ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-hint-color)',
                  opacity: done || active ? 1 : 0.5,
                }}
              >
                {done ? '✓' : STEP_ICONS[step]}
              </div>
              <p
                className="text-center mt-1 leading-tight"
                style={{ color: active ? 'var(--tg-theme-text-color)' : 'var(--tg-theme-hint-color)', fontSize: '9px' }}
              >
                {t(`orders.status.${step}`)}
              </p>
            </div>
            {idx < STEPS.length - 1 && (
              <div
                className="h-0.5 flex-1 -mt-4 transition-colors duration-300"
                style={{
                  background: idx < currentIdx ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
