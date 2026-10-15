// Thin wrapper over window.Telegram.WebApp. Every call is guarded, so the app
// also runs in a normal browser (development) where most features are missing.

const real = window.Telegram?.WebApp

// In `npm run dev` outside Telegram there is no initData — use the API's
// DEV_MODE mock user instead.
const mockMode = import.meta.env.DEV && !real?.initData

export const tg = real
export const initData = mockMode ? 'mock_init_data_for_dev' : real?.initData || ''
export const startParam = real?.initDataUnsafe?.start_param || new URLSearchParams(location.search).get('startapp') || ''
export const telegramUser = real?.initDataUnsafe?.user || (mockMode ? { id: 123456789, first_name: 'Test', language_code: 'uz' } : null)

const CREAM = '#FAF9F5'

function supports(version) {
  return Boolean(real?.isVersionAtLeast?.(version))
}

export function initTelegram() {
  if (!real) return
  real.ready()
  real.expand()
  if (supports('6.1')) {
    real.setHeaderColor(CREAM)
    real.setBackgroundColor(CREAM)
  }
  if (supports('7.10')) real.setBottomBarColor?.(CREAM)
  // Scrolling a long list must not swipe the whole app closed.
  if (supports('7.7')) real.disableVerticalSwipes?.()
}

export const haptic = {
  tap: () => supports('6.1') && real.HapticFeedback.impactOccurred('light'),
  select: () => supports('6.1') && real.HapticFeedback.selectionChanged(),
  success: () => supports('6.1') && real.HapticFeedback.notificationOccurred('success'),
  error: () => supports('6.1') && real.HapticFeedback.notificationOccurred('error'),
}

export const backButton = {
  available: supports('6.1'),
  show(handler) {
    if (!this.available) return () => {}
    real.BackButton.onClick(handler)
    real.BackButton.show()
    return () => {
      real.BackButton.offClick(handler)
      real.BackButton.hide()
    }
  },
}

export function confirmDialog(message) {
  if (supports('6.2')) {
    return new Promise((resolve) => real.showConfirm(message, resolve))
  }
  return Promise.resolve(window.confirm(message))
}

export function alertDialog(message) {
  if (supports('6.2')) return new Promise((resolve) => real.showAlert(message, resolve))
  window.alert(message)
  return Promise.resolve()
}

// External links (Yandex Go tracking etc.) open in the browser / their app,
// not inside the Mini App's webview.
export function openLink(url) {
  if (real?.openLink) real.openLink(url)
  else window.open(url, '_blank', 'noopener')
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Older webviews: fall back to a hidden textarea.
    const el = document.createElement('textarea')
    el.value = text
    el.setAttribute('readonly', '')
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    const ok = document.execCommand('copy')
    el.remove()
    return ok
  }
}

// Ask Telegram for the user's phone number. Resolves to "+998..." or null.
export function requestPhone() {
  if (!supports('6.9')) return Promise.resolve(null)
  return new Promise((resolve) => {
    real.requestContact((ok, response) => {
      const phone = ok && response?.responseUnsafe?.contact?.phone_number
      resolve(phone ? (phone.startsWith('+') ? phone : `+${phone}`) : null)
    })
  })
}

export const canRequestPhone = supports('6.9')

// Current location via Telegram's LocationManager (8.0+) or the browser.
// Resolves to { lat, lng } or null.
export function requestLocation() {
  const lm = real?.LocationManager
  if (supports('8.0') && lm) {
    return new Promise((resolve) => {
      const get = () =>
        lm.getLocation((loc) => resolve(loc ? { lat: loc.latitude, lng: loc.longitude } : null))
      if (lm.isInited) get()
      else lm.init(() => (lm.isLocationAvailable ? get() : resolve(null)))
    })
  }
  if (!navigator.geolocation) return Promise.resolve(null)
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 15000 },
    )
  })
}
