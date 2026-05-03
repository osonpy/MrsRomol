// utils/formatPrice.js
/**
 * Format a numeric price as Uzbek so'm.
 * Example: 150000 → "150 000 so'm"
 */
export function formatPrice(amount, currency = "so'm") {
  if (amount == null || isNaN(amount)) return `0 ${currency}`
  return (
    new Intl.NumberFormat('uz-UZ', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount) + ` ${currency}`
  )
}

/**
 * Format price without currency symbol.
 * Example: 150000 → "150 000"
 */
export function formatNumber(amount) {
  if (amount == null || isNaN(amount)) return '0'
  return new Intl.NumberFormat('uz-UZ', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}
