import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import uz from './uz.json'
import ru from './ru.json'
import { telegramUser } from '../lib/telegram'

// Start in the Telegram client language; the saved profile language
// (from /meta) takes over as soon as it loads.
const initial = telegramUser?.language_code?.startsWith('ru') ? 'ru' : 'uz'

i18n.use(initReactI18next).init({
  resources: { uz: { translation: uz }, ru: { translation: ru } },
  lng: initial,
  fallbackLng: 'uz',
  interpolation: { escapeValue: false },
})

document.documentElement.lang = initial
i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng
})

export default i18n

// Message for an ApiError (or anything thrown), in the current language.
export function errorText(err) {
  const code = err?.code
  return code && i18n.exists(`errors.${code}`) ? i18n.t(`errors.${code}`) : i18n.t('errors.generic')
}
