import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { tg } from './telegram'

// Optional background music. Off until the customer turns it on; the choice is
// remembered. Browsers only allow sound after a tap, so a remembered "on"
// starts with the customer's first touch of the app.

const TRACKS = ['/music/track1.m4a', '/music/track2.m4a', '/music/track3.m4a']
const VOLUME = 0.35
const FADE_IN = 2.5 // seconds
const FADE_OUT = 0.8

export const useMusic = create(
  persist(
    (set) => ({
      enabled: false,
      hintSeen: false,
      playing: false, // runtime only
      setEnabled: (enabled) => set({ enabled, hintSeen: true }),
      seeHint: () => set({ hintSeen: true }),
    }),
    { name: 'mrs-romol-music', version: 1, partialize: ({ enabled, hintSeen }) => ({ enabled, hintSeen }) },
  ),
)

let audio = null
let ctx = null
let gain = null
let index = Math.floor(Math.random() * TRACKS.length) // a different first track each visit
let stopTimer = null

// iOS ignores audio.volume, so volume and fades go through Web Audio when it exists.
function setup() {
  if (audio) return
  audio = new Audio()
  audio.preload = 'none'
  audio.src = TRACKS[index]
  audio.addEventListener('ended', () => {
    index = (index + 1) % TRACKS.length
    audio.src = TRACKS[index]
    audio.play().catch(() => {})
  })
  audio.addEventListener('playing', () => useMusic.setState({ playing: true }))
  audio.addEventListener('pause', () => useMusic.setState({ playing: false }))
  const AC = window.AudioContext || window.webkitAudioContext
  if (AC) {
    try {
      ctx = new AC()
      gain = ctx.createGain()
      gain.gain.value = 0
      ctx.createMediaElementSource(audio).connect(gain).connect(ctx.destination)
    } catch {
      ctx = gain = null
    }
  }
  if (!gain) audio.volume = VOLUME
}

function fadeTo(value, seconds) {
  if (!gain) return
  const now = ctx.currentTime
  gain.gain.cancelScheduledValues(now)
  gain.gain.setValueAtTime(gain.gain.value, now)
  gain.gain.linearRampToValueAtTime(value, now + seconds)
}

// Must be called from a tap (or right after one).
export async function startMusic() {
  setup()
  clearTimeout(stopTimer)
  try {
    if (ctx?.state === 'suspended') await ctx.resume()
    await audio.play()
    fadeTo(VOLUME, FADE_IN)
  } catch {
    // Blocked or failed to load: show it as off rather than stuck "on".
    useMusic.setState({ playing: false })
  }
}

export function stopMusic() {
  if (!audio || audio.paused) return
  fadeTo(0, FADE_OUT)
  clearTimeout(stopTimer)
  stopTimer = setTimeout(() => audio.pause(), gain ? FADE_OUT * 1000 : 0)
}

export function toggleMusic() {
  const { enabled, setEnabled } = useMusic.getState()
  setEnabled(!enabled)
  if (enabled) stopMusic()
  else startMusic()
}

// Remembered "on": start on the first touch. Pause whenever the app is hidden
// or Telegram is minimised; resume when it comes back.
export function initMusic() {
  const onFirstTouch = (e) => {
    if (e.target.closest?.('[data-music-toggle]')) return // the toggle handles itself
    window.removeEventListener('pointerdown', onFirstTouch, true)
    if (useMusic.getState().enabled && !useMusic.getState().playing) startMusic()
  }
  window.addEventListener('pointerdown', onFirstTouch, true)

  const away = () => audio && !audio.paused && audio.pause()
  const back = () => useMusic.getState().enabled && audio?.paused && audio.currentTime > 0 && startMusic()
  document.addEventListener('visibilitychange', () => (document.hidden ? away() : back()))
  tg?.onEvent?.('deactivated', away)
  tg?.onEvent?.('activated', back)
}
