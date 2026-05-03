export function EmptyState({ emoji = '📭', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      {emoji && <span className="text-5xl">{emoji}</span>}
      {title && (
        <p className="font-semibold text-base" style={{ color: 'var(--tg-theme-text-color)' }}>
          {title}
        </p>
      )}
      {description && (
        <p className="text-sm max-w-xs" style={{ color: 'var(--tg-theme-hint-color)' }}>
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
