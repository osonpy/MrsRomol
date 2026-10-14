// Walks the customer journey in headless Chrome and saves a screenshot of every
// step. Usage: node walk.mjs <output dir>   (needs e2e/demo_stack.sh + API + Mini App)
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import puppeteer from 'puppeteer-core'
const OUT = process.argv[2] || '../.demo/shots'
mkdirSync(OUT, { recursive: true })
// Smallest valid JPEG header is enough: the demo storage accepts any upload.
const RECEIPT = join(OUT, 'receipt.jpg')
writeFileSync(RECEIPT, Buffer.from([0xff, 0xd8, 0xff, 0xe0, ...new Array(64).fill(0)]))
const CHROME = process.env.CHROME || '/usr/bin/google-chrome'
const BASE = 'http://localhost:5173'
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--lang=uz'] })
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
    const el = [...document.querySelectorAll(sel)].find((e) => e.textContent.trim().includes(text))
    if (el) { el.scrollIntoView({ block: 'center' }); el.click(); return true }
    return false
  }, text, sel)
  if (!ok) throw new Error('not found: ' + text)
  await sleep(400)
}

await page.goto(BASE + '/', { waitUntil: 'networkidle0' })
await shot('01_catalog')

await page.goto(BASE + '/product/a0000000-0000-0000-0000-000000000003', { waitUntil: 'networkidle0' })
await shot('02_product')
await page.evaluate(() => window.scrollTo(0, 700)); await shot('03_product_details')
await clickText('Oʻlchamimni aniqlash')
const inputs = await page.$$('div[role=dialog] input')
await inputs[0].type('92'); await inputs[1].type('141')
await shot('04_size_guide')
await clickText('oʻlchamini tanlash')
await clickText('Savatga qoʻshish')
await shot('05_product_added')

await page.goto(BASE + '/product/a0000000-0000-0000-0000-000000000001', { waitUntil: 'networkidle0' })
await page.click('button[aria-label=favorite]')
await clickText('Savatga qoʻshish')

await page.goto(BASE + '/cart', { waitUntil: 'networkidle0' })
await page.type('input[placeholder=Promokod]', 'bahor10')
await clickText('Qoʻllash'); await sleep(800)
await shot('06_cart')

await clickText('Rasmiylashtirish')
await page.waitForSelector('select')
await page.select('select', 'tashkent_city')
await page.evaluate(() => { const el = document.querySelector('input[autocomplete=name]'); el.focus() })
await page.$eval('input[autocomplete=name]', (el) => (el.value = ''))
await page.type('input[autocomplete=name]', 'Dilnoza')
await page.type('input[type=tel]', '90 123 45 67')
await page.type('textarea', 'Chilonzor 9-kvartal, 12-uy, 34-xonadon')
await shot('07_checkout')
await clickText('Yetkazib berish narxini', 'label'); await clickText('qaytarilmasligiga', 'label')
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await shot('08_checkout_bottom')
await clickText('Buyurtma berish')
await page.waitForFunction(() => location.pathname.startsWith('/orders/'), { timeout: 10000 })
await sleep(800)
await shot('09_order_payment')
await page.evaluate(() => window.scrollTo(0, 650)); await shot('10_order_payment_cards')
const file = await page.$('input[type=file]')
await file.uploadFile(RECEIPT)
await sleep(500)
await clickText('Chekni yuborish'); await sleep(1200)
await page.evaluate(() => window.scrollTo(0, 0)); await shot('11_order_review')

await page.goto(BASE + '/orders', { waitUntil: 'networkidle0' }); await shot('12_orders')
await page.goto(BASE + '/favorites', { waitUntil: 'networkidle0' }); await shot('13_favorites')
await page.goto(BASE + '/profile', { waitUntil: 'networkidle0' }); await shot('14_profile')
await clickText('Русский'); await sleep(600)
await page.goto(BASE + '/', { waitUntil: 'networkidle0' }); await shot('15_catalog_ru')
await page.goto(BASE + '/?q=romol', { waitUntil: 'networkidle0' }); await shot('16_search')
await page.goto(BASE + '/cart', { waitUntil: 'networkidle0' }); await shot('17_cart_empty_ru')

console.log('PROBLEMS:', problems.length ? '\n' + problems.join('\n') : 'none')
await browser.close()
process.exit(problems.length ? 1 : 0)
