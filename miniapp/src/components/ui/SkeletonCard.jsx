function Shimmer({ className = '' }) {
  return (
    <div
      className={`rounded animate-pulse ${className}`}
      style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
    />
  )
}

export function SkeletonCard() {
  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
    >
      <Shimmer className="w-full aspect-square" />
      <div className="p-3 space-y-2">
        <Shimmer className="h-4 w-3/4" />
        <Shimmer className="h-3 w-1/2" />
        <Shimmer className="h-5 w-2/3" />
      </div>
    </div>
  )
}

export function SkeletonOrderCard() {
  return (
    <div
      className="rounded-2xl p-4 space-y-3"
      style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
    >
      <div className="flex justify-between">
        <Shimmer className="h-4 w-24" />
        <Shimmer className="h-4 w-16" />
      </div>
      <Shimmer className="h-3 w-full" />
      <Shimmer className="h-3 w-3/4" />
    </div>
  )
}
