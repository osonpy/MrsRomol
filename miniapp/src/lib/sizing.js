// "O'lchamimni aniqlash" — recommend a size from the product's size chart.
//
// size_chart = { columns: ["chest", "length"],
//                rows: [{ size: "M", chest: [88, 92], length: 140 }, ...] }
// A cell is a number or a [min, max] range, in centimetres.

function range(cell) {
  if (Array.isArray(cell)) return [Number(cell[0]), Number(cell[1])]
  const n = Number(cell)
  return [n, n]
}

// How far a measurement is outside a cell's range (0 = fits).
function miss(value, cell) {
  const [lo, hi] = range(cell)
  if (value < lo) return lo - value
  if (value > hi) return value - hi
  return 0
}

/**
 * @param chart     product.size_chart
 * @param measures  { chest: 90, ... } — only the filled-in columns
 * @returns { size, exact } or null when nothing was entered
 */
export function recommendSize(chart, measures) {
  const cols = (chart?.columns || []).filter((c) => Number(measures[c]) > 0)
  if (!cols.length || !chart.rows?.length) return null

  let best = null
  for (const row of chart.rows) {
    const usable = cols.filter((c) => row[c] !== undefined && row[c] !== null && row[c] !== '')
    if (!usable.length) continue
    const score = usable.reduce((sum, c) => sum + miss(Number(measures[c]), row[c]), 0)
    if (!best || score < best.score) best = { size: row.size, score }
  }
  return best && { size: best.size, exact: best.score === 0 }
}

export function formatCell(cell) {
  if (Array.isArray(cell)) return `${cell[0]}–${cell[1]}`
  return cell ?? '—'
}
