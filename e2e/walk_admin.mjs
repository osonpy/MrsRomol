// Admin walk-through: review a payment, ship the order, create a product with
// photos, variants and a size chart, publish it. Run after walk.mjs (which
// leaves an order waiting for payment review).
// Usage: node walk_admin.mjs <output dir>
import { mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import puppeteer from 'puppeteer-core'
const OUT = process.argv[2] || '../.demo/shots-admin'
mkdirSync(OUT, { recursive: true })
const PHOTO = resolve('../.demo/storage/product-images/demo/lilac0.webp')
const BASE = 'http://localhost:5173'
const browser = await puppeteer.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox'] })
const page = await browser.newPage()
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true })
const problems = []
page.on('console', (m) => m.type() === 'error' && problems.push('console: ' + m.text()))
page.on('pageerror', (e) => problems.push('pageerror: ' + e.message))
page.on('response', (r) => r.status() >= 400 && problems.push(`${r.status()} ${r.request().method()} ${r.url()}`))
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const shot = async (name) => { await sleep(700); await page.screenshot({ path: `${OUT}/${name}.png` }); console.log('shot', name) }
const clickText = async (text, sel = 'button, a, label') => {
  const ok = await page.evaluate((text, sel) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.textContent.trim().includes(text))
    const el = els[els.length - 1] // the last match: sheets render above the page
    if (el) { el.scrollIntoView({ block: 'center' }); el.click(); return true }
    return false
  }, text, sel)
  if (!ok) throw new Error('not found: ' + text)
  await sleep(500)
}
const typeInto = async (selector, text) => { await page.click(selector, { clickCount: 3 }); await page.type(selector, text) }

// ── orders ────────────────────────────────────────────────────────────────────
await page.goto(BASE + '/admin', { waitUntil: 'networkidle0' })
await shot('a01_dashboard')
await clickText('Chekni tekshirish kerak')
await page.waitForFunction(() => location.search.includes('payment_review'))
await sleep(600); await shot('a02_orders_review')
await page.click('a[href^="/admin/orders/"]')
await page.waitForSelector('img[alt=Chek]'); await sleep(800)
await shot('a03_order_receipt')
await clickText('Tasdiqlash'); await sleep(1200)
await shot('a04_order_confirmed')
await clickText('Yuborildi deb belgilash')
await page.type('div[role=dialog] textarea', 'Yandex taksi, 01 A 123 BC')
await clickText('Tasdiqlash — mijozga xabar boradi'); await sleep(1200)
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await shot('a05_order_shipped')

// ── new product ───────────────────────────────────────────────────────────────
await page.goto(BASE + '/admin/products', { waitUntil: 'networkidle0' })
await shot('a06_products')
await clickText('Qoʻshish')
await page.waitForSelector('input[placeholder="Ipak roʻmol «Nil»"]')
await page.type('input[placeholder="Ipak roʻmol «Nil»"]', 'Kashmir roʻmol «Sahro»')
await page.type('input[placeholder="Шёлковый платок «Нил»"]', 'Кашемировый платок «Сахра»')
await page.select('select', (await page.$$eval('select option', (os) => os.find((o) => o.textContent.includes('Roʻmollar')).value)))
await page.type('input[placeholder="150000"]', '210000')
await page.type('textarea', 'Yumshoq kashmir, 70×200 sm. Qishki mavsum uchun.')
await shot('a07_product_new')
await clickText('Yaratish')
await page.waitForFunction(() => /\/admin\/products\/[0-9a-f-]{36}$/.test(location.pathname), { timeout: 10000 })
await sleep(800); await shot('a08_product_created')

const fileInput = await page.$('input[type=file]')
await fileInput.uploadFile(PHOTO)
await page.waitForFunction(() => document.querySelectorAll('img[src*="_thumb.webp"]').length >= 1, { timeout: 15000 })
await sleep(800); await shot('a09_photo_uploaded')

await clickText('Variant qoʻshish')
await clickText('Qora', 'div[role=dialog] button'); await clickText('Bej', 'div[role=dialog] button')
await clickText('Oʻlchamsiz', 'div[role=dialog] label')
await shot('a10_variants_sheet')
await clickText('ta variant yaratish'); await sleep(1500)
await shot('a11_variants_created')

await page.evaluate(() => { const i = [...document.querySelectorAll('input[type=checkbox]')].pop(); i.scrollIntoView({ block: 'center' }); i.click() })
await sleep(300)
await clickText('Oʻzgarishlarni saqlash'); await sleep(1200)
await page.goto(BASE + '/?q=kashmir', { waitUntil: 'networkidle0' }); await shot('a12_published_in_shop')

await page.goto(BASE + '/admin/more', { waitUntil: 'networkidle0' }); await shot('a13_more')

console.log('PROBLEMS:', problems.length ? '\n' + problems.join('\n') : 'none')
await browser.close()
process.exit(problems.length ? 1 : 0)
