import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { toggleMusic, useMusic } from '../lib/music'
import { haptic } from '../lib/telegram'
import { MusicIcon } from './icons'

// Three bars that move while music plays.
function Equalizer() {
  return (
    <span className="flex h-4 items-end gap-[3px]" aria-hidden>
      {[0, 0.35, 0.7].map((delay) => (
        <span
          key={delay}
          className="h-full w-[3px] origin-bottom animate-eq-bar rounded-full bg-current"
          style={{ animationDelay: `${delay}s` }}
        />
      ))}
    </span>
  )
}

export default function MusicToggle({ className = '' }) {
  const { t } = useTranslation()
  const enabled = useMusic((s) => s.enabled)
  const playing = useMusic((s) => s.playing)
  const hintSeen = useMusic((s) => s.hintSeen)
  const seeHint = useMusic((s) => s.seeHint)
  const on = enabled && playing

  // The invitation shows once, for a few seconds.
  useEffect(() => {
    if (hintSeen) return
    const id = setTimeout(seeHint, 6000)
    return () => clearTimeout(id)
  }, [hintSeen, seeHint])

  return (
    <div className={className}>
      {!hintSeen && (
        <span className="pointer-events-none absolute right-0 top-full z-30 mt-1.5 animate-fade-in whitespace-nowrap rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-rose-700 shadow-card">
          {t('music.hint')}
        </span>
      )}
      <button
        type="button"
        data-music-toggle
        aria-label={enabled ? t('music.off') : t('music.on')}
        aria-pressed={enabled}
        onClick={() => {
          haptic.tap()
          toggleMusic()
        }}
        className={`relative flex h-10 w-10 items-center justify-center rounded-full border transition-colors ${
          on ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-rose-700'
        }`}
      >
        {!hintSeen && <span className="absolute inset-0 animate-soft-ping rounded-full border border-rose-400" />}
        {on ? <Equalizer /> : <MusicIcon className={`h-5 w-5 ${enabled ? 'animate-pulse' : ''}`} />}
      </button>
    </div>
  )
}
