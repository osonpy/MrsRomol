// utils/formatDate.js
/**
 * Format ISO datetime string to human-readable date.
 * Example: "2024-03-15T10:30:00Z" → "15 Mar 2024, 10:30"
 */
export function formatDate(isoString, lang = 'uz') {
  if (!isoString) return ''
  const localeMap = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-US' }
  const locale = localeMap[lang] ?? 'uz-UZ'
  try {
    return new Date(isoString).toLocaleDateString(locale, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return isoString.slice(0, 16).replace('T', ' ')
  }
}

/**
 * Format as short date only.
 * Example: "2024-03-15T10:30:00Z" → "15 Mar"
 */
export function formatShortDate(isoString, lang = 'uz') {
  if (!isoString) return ''
  const localeMap = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-US' }
  const locale = localeMap[lang] ?? 'uz-UZ'
  try {
    return new Date(isoString).toLocaleDateString(locale, {
      day: 'numeric',
      month: 'short',
    })
  } catch {
    return isoString.slice(0, 10)
  }
}
