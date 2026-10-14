import i18n from '../i18n'

const NBSP = ' '

export function money(amount) {
  const n = Math.round(Number(amount) || 0)
  return `${n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, NBSP)}${NBSP}${i18n.t('common.currency')}`
}

// Localised field: pick(product, 'name') → product.name_ru for Russian users,
// falling back to Uzbek when the Russian text is empty.
export function pick(obj, field) {
  if (!obj) return ''
  const lang = i18n.language === 'ru' ? 'ru' : 'uz'
  return obj[`${field}_${lang}`] || obj[`${field}_uz`] || ''
}

// For {uz, ru} objects such as colours: localized({uz: 'Qora', ru: 'Чёрный'})
export function localized(obj) {
  if (!obj) return ''
  return (i18n.language === 'ru' && obj.ru) || obj.uz || ''
}

const MONTHS = {
  uz: ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'],
  ru: ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'],
}

export function dateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const lang = i18n.language === 'ru' ? 'ru' : 'uz'
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getDate()} ${MONTHS[lang][d.getMonth()]}, ${hh}:${mm}`
}

// "+998901234567" → "+998 90 123 45 67"
export function phone(p) {
  const m = /^\+998(\d{2})(\d{3})(\d{2})(\d{2})$/.exec(p || '')
  return m ? `+998 ${m[1]} ${m[2]} ${m[3]} ${m[4]}` : p || ''
}

// "8600123412341234" → "8600 1234 1234 1234"
export function cardNumber(n) {
  return (n || '').replace(/(\d{4})(?=\d)/g, `$1${NBSP}`)
}
