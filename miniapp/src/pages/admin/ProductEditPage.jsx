import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChevronDownIcon, ImageIcon, PlusIcon, TrashIcon, XIcon } from '../../components/icons'
import { QtyStepper } from '../../components/order'
import { Button, ErrorState, Section, Sheet, Skeleton, StickyBar } from '../../components/ui'
import { useAdminProduct, useCategories, useProductMutation } from '../../hooks/admin'
import { api } from '../../lib/api'
import { money } from './uz'
import { confirmDialog, haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'

const SIZE_PRESETS = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', 'S/M', 'L/XL', 'Standart']
const COLOR_PRESETS = [
  ['Qora', 'Чёрный', '#1F1B1D'],
  ['Oq', 'Белый', '#F4F1EC'],
  ['Bej', 'Бежевый', '#D6BEA0'],
  ['Pushti', 'Розовый', '#D6A096'],
  ['Moviy', 'Голубой', '#9DB7D5'],
  ['Toʻq koʻk', 'Тёмно-синий', '#2C385C'],
  ['Kulrang', 'Серый', '#9A9A9A'],
  ['Jigarrang', 'Коричневый', '#6B4A3A'],
  ['Yashil', 'Зелёный', '#5E7D5A'],
  ['Qizil', 'Красный', '#A8323A'],
]
const CHART_COLUMNS = [
  ['chest', 'Koʻkrak aylanasi'],
  ['waist', 'Bel aylanasi'],
  ['hips', 'Son aylanasi'],
  ['length', 'Uzunligi'],
  ['shoulder', 'Yelka kengligi'],
  ['sleeve', 'Yeng uzunligi'],
  ['head', 'Bosh aylanasi'],
]
const MAX_PHOTOS = 5

const digits = (v) => String(v ?? '').replace(/\D/g, '')

// ── basic info ────────────────────────────────────────────────────────────────

function emptyForm() {
  return { name_uz: '', name_ru: '', category_id: '', price: '', cost_price: '', description_uz: '', description_ru: '', is_active: false }
}

function toForm(p) {
  return {
    name_uz: p.name_uz,
    name_ru: p.name_ru,
    category_id: p.category_id || '',
    price: String(p.price),
    cost_price: p.cost_price == null ? '' : String(p.cost_price),
    description_uz: p.description_uz,
    description_ru: p.description_ru,
    is_active: p.is_active,
  }
}

function toBody(f) {
  return {
    name_uz: f.name_uz.trim(),
    name_ru: f.name_ru.trim(),
    category_id: f.category_id || null,
    price: Number(digits(f.price)),
    cost_price: f.cost_price === '' ? null : Number(digits(f.cost_price)),
    description_uz: f.description_uz.trim(),
    description_ru: f.description_ru.trim(),
    is_active: f.is_active,
  }
}

function InfoForm({ form, set, categories }) {
  return (
    <div className="space-y-3">
      <label className="block">
        <span className="label">Nomi (oʻzbekcha) *</span>
        <input className="field" value={form.name_uz} onChange={(e) => set({ name_uz: e.target.value })} placeholder="Ipak roʻmol «Nil»" />
      </label>
      <label className="block">
        <span className="label">Nomi (ruscha)</span>
        <input className="field" value={form.name_ru} onChange={(e) => set({ name_ru: e.target.value })} placeholder="Шёлковый платок «Нил»" />
      </label>
      <label className="block">
        <span className="label">Kategoriya</span>
        <div className="relative">
          <select className="field appearance-none pr-10" value={form.category_id} onChange={(e) => set({ category_id: e.target.value })}>
            <option value="">— Tanlanmagan —</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name_uz}
              </option>
            ))}
          </select>
          <ChevronDownIcon className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
        </div>
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="label">Narxi, soʻm *</span>
          <input className="field" inputMode="numeric" value={form.price} onChange={(e) => set({ price: digits(e.target.value) })} placeholder="150000" />
        </label>
        <label className="block">
          <span className="label">Tannarx (yashirin)</span>
          <input className="field" inputMode="numeric" value={form.cost_price} onChange={(e) => set({ cost_price: digits(e.target.value) })} placeholder="80000" />
        </label>
      </div>
      {form.price && <p className="-mt-1 text-xs text-ink-soft">Mijoz koʻradi: {money(form.price)}</p>}
      <label className="block">
        <span className="label">Tavsif (oʻzbekcha)</span>
        <textarea className="field min-h-[5rem]" value={form.description_uz} onChange={(e) => set({ description_uz: e.target.value })} placeholder="Matosi, oʻlchami, parvarishi…" />
      </label>
      <label className="block">
        <span className="label">Tavsif (ruscha)</span>
        <textarea className="field min-h-[5rem]" value={form.description_ru} onChange={(e) => set({ description_ru: e.target.value })} />
      </label>
      <label className="flex items-center justify-between rounded-xl bg-rose-50 px-4 py-3">
        <span>
          <span className="block font-medium">Doʻkonda koʻrsatish</span>
          <span className="text-xs text-ink-soft">Rasm va variantlar tayyor boʻlgach yoqing</span>
        </span>
        <input type="checkbox" className="h-6 w-6 accent-rose-600" checked={form.is_active} onChange={(e) => set({ is_active: e.target.checked })} />
      </label>
    </div>
  )
}

// ── photos ────────────────────────────────────────────────────────────────────

function Photos({ product }) {
  const input = useRef(null)
  const colors = [...new Set(product.variants.map((v) => v.color_uz).filter(Boolean))]
  const upload = useProductMutation(product.id, (files) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    return api.upload(`/admin/products/${product.id}/images`, form)
  })
  const remove = useProductMutation(product.id, (imageId) => api.delete(`/admin/images/${imageId}`))
  const reorder = useProductMutation(product.id, (ids) => api.put(`/admin/products/${product.id}/images/order`, { image_ids: ids }))
  const setColor = useProductMutation(product.id, ({ id, color_uz }) => api.patch(`/admin/images/${id}`, { color_uz }))
  const left = MAX_PHOTOS - product.images.length

  function move(i, dir) {
    const ids = product.images.map((img) => img.id)
    ;[ids[i], ids[i + dir]] = [ids[i + dir], ids[i]]
    reorder.mutate(ids, { onError: toast.error })
  }

  return (
    <Section title={`Rasmlar · ${product.images.length}/${MAX_PHOTOS}`}>
      <div className="grid grid-cols-3 gap-2">
        {product.images.map((img, i) => (
          <div key={img.id} className="relative">
            <img src={img.thumb_url} alt="" className="aspect-[3/4] w-full rounded-lg bg-rose-50 object-cover" />
            {i === 0 && <span className="absolute left-1 top-1 rounded bg-white/90 px-1.5 text-[10px] font-bold text-rose-700">ASOSIY</span>}
            <button
              type="button"
              aria-label="delete"
              onClick={async () => (await confirmDialog('Rasmni oʻchirasizmi?')) && remove.mutate(img.id, { onError: toast.error })}
              className="absolute right-1 top-1 rounded-full bg-white/90 p-1 text-red-700"
            >
              <XIcon className="h-4 w-4" />
            </button>
            <div className="mt-1 flex items-center gap-1">
              <button type="button" disabled={i === 0} onClick={() => move(i, -1)} className="h-7 flex-1 rounded bg-rose-50 text-sm disabled:opacity-30">
                ←
              </button>
              <button type="button" disabled={i === product.images.length - 1} onClick={() => move(i, 1)} className="h-7 flex-1 rounded bg-rose-50 text-sm disabled:opacity-30">
                →
              </button>
            </div>
            {colors.length > 0 && (
              <select
                className="mt-1 h-7 w-full rounded border border-rose-200 bg-white text-xs"
                value={img.color_uz || ''}
                onChange={(e) => setColor.mutate({ id: img.id, color_uz: e.target.value }, { onError: toast.error })}
              >
                <option value="">Barcha ranglar</option>
                {colors.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            )}
          </div>
        ))}
        {left > 0 && (
          <button
            type="button"
            onClick={() => input.current?.click()}
            disabled={upload.isPending}
            className="flex aspect-[3/4] flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-rose-300 text-rose-700 disabled:opacity-60"
          >
            {upload.isPending ? <span className="text-xs">Yuklanmoqda…</span> : <><ImageIcon className="h-7 w-7" /><span className="text-xs font-semibold">Qoʻshish</span></>}
          </button>
        )}
      </div>
      <input
        ref={input}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        className="hidden"
        onChange={(e) => {
          const files = [...(e.target.files || [])].slice(0, left)
          e.target.value = ''
          if (files.length) upload.mutate(files, { onSuccess: () => toast.show('Rasm qoʻshildi'), onError: toast.error })
        }}
      />
      <p className="mt-2 text-xs text-ink-soft">Birinchi rasm katalogda koʻrinadi. Rangga bogʻlangan rasm shu rang tanlanganda chiqadi.</p>
    </Section>
  )
}

// ── variants ──────────────────────────────────────────────────────────────────

function AddVariantsSheet({ open, onClose, product }) {
  const existingColors = useMemo(() => {
    const m = new Map()
    product.variants.forEach((v) => v.color_uz && m.set(v.color_uz, { uz: v.color_uz, ru: v.color_ru || '', hex: v.color_hex || '#CCCCCC' }))
    return [...m.values()]
  }, [product.variants])
  const existingSizes = [...new Set(product.variants.map((v) => v.size).filter(Boolean))]

  const [colors, setColors] = useState([])
  const [sizes, setSizes] = useState([])
  const [noColor, setNoColor] = useState(false)
  const [noSize, setNoSize] = useState(false)
  const [custom, setCustom] = useState({ uz: '', ru: '', hex: '#C29786' })
  const [customSize, setCustomSize] = useState('')
  const [stock, setStock] = useState(5)
  const [busy, setBusy] = useState(false)
  const qcMutation = useProductMutation(product.id, () => api.get(`/admin/products/${product.id}`))

  useEffect(() => {
    if (!open) return
    setColors(existingColors)
    setSizes(existingSizes)
    setNoColor(product.variants.length > 0 && existingColors.length === 0)
    setNoSize(product.variants.length > 0 && existingSizes.length === 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const toggleColor = (c) => setColors((cs) => (cs.some((x) => x.uz === c.uz) ? cs.filter((x) => x.uz !== c.uz) : [...cs, c]))
  const toggleSize = (s) => setSizes((ss) => (ss.includes(s) ? ss.filter((x) => x !== s) : [...ss, s]))

  const colorList = noColor ? [null] : colors
  const sizeList = noSize ? [null] : sizes
  const exists = (c, s) => product.variants.some((v) => (v.color_uz ?? null) === (c?.uz ?? null) && (v.size ?? null) === s)
  const toCreate = colorList.flatMap((c) => sizeList.map((s) => [c, s])).filter(([c, s]) => !exists(c, s))

  async function create() {
    setBusy(true)
    try {
      for (const [c, s] of toCreate) {
        await api.post(`/admin/products/${product.id}/variants`, {
          color_uz: c?.uz || null,
          color_ru: c?.ru || null,
          color_hex: c?.hex || null,
          size: s,
          stock,
        })
      }
      await qcMutation.mutateAsync()
      haptic.success()
      toast.show(`${toCreate.length} ta variant qoʻshildi`)
      onClose()
    } catch (err) {
      toast.error(err)
      await qcMutation.mutateAsync().catch(() => {})
    } finally {
      setBusy(false)
    }
  }

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Variantlar qoʻshish"
      footer={
        <Button className="w-full" loading={busy} disabled={toCreate.length === 0} onClick={create}>
          {toCreate.length ? `${toCreate.length} ta variant yaratish` : 'Yangi variant yoʻq'}
        </Button>
      }
    >
      <h3 className="label">Ranglar</h3>
      <label className="mb-2 flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-rose-600" checked={noColor} onChange={(e) => setNoColor(e.target.checked)} /> Rangsiz (bitta rang)
      </label>
      {!noColor && (
        <>
          <div className="mb-3 flex flex-wrap gap-2">
            {[...existingColors, ...COLOR_PRESETS.map(([uz, ru, hex]) => ({ uz, ru, hex })).filter((p) => !existingColors.some((e) => e.uz === p.uz))].map((c) => {
              const on = colors.some((x) => x.uz === c.uz)
              return (
                <button
                  key={c.uz}
                  type="button"
                  onClick={() => toggleColor(c)}
                  className={`chip gap-1.5 pl-1.5 ${on ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
                >
                  <span className="h-6 w-6 rounded-full border border-black/10" style={{ background: c.hex }} />
                  {c.uz}
                </button>
              )
            })}
          </div>
          <div className="mb-5 flex items-end gap-2 rounded-xl bg-rose-50 p-2.5">
            <input type="color" value={custom.hex} onChange={(e) => setCustom((x) => ({ ...x, hex: e.target.value }))} className="h-11 w-11 shrink-0 rounded-lg border-0 bg-transparent p-0" />
            <input className="field h-11 py-0" placeholder="Rang (uz)" value={custom.uz} onChange={(e) => setCustom((x) => ({ ...x, uz: e.target.value }))} />
            <input className="field h-11 py-0" placeholder="Цвет (ru)" value={custom.ru} onChange={(e) => setCustom((x) => ({ ...x, ru: e.target.value }))} />
            <Button
              variant="secondary"
              className="h-11 w-11 shrink-0 px-0"
              disabled={!custom.uz.trim()}
              onClick={() => {
                toggleColor({ uz: custom.uz.trim(), ru: custom.ru.trim(), hex: custom.hex })
                setCustom({ uz: '', ru: '', hex: '#C29786' })
              }}
            >
              <PlusIcon className="h-5 w-5" />
            </Button>
          </div>
        </>
      )}

      <h3 className="label">Oʻlchamlar</h3>
      <label className="mb-2 flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-rose-600" checked={noSize} onChange={(e) => setNoSize(e.target.checked)} /> Oʻlchamsiz (masalan, roʻmol)
      </label>
      {!noSize && (
        <div className="mb-5 flex flex-wrap gap-2">
          {[...new Set([...existingSizes, ...SIZE_PRESETS, ...sizes])].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => toggleSize(s)}
              className={`chip min-w-[3rem] justify-center ${sizes.includes(s) ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
            >
              {s}
            </button>
          ))}
          <div className="flex gap-1">
            <input className="field h-9 w-24 py-0 text-sm" placeholder="Boshqa" value={customSize} onChange={(e) => setCustomSize(e.target.value)} />
            <Button variant="secondary" className="h-9 px-3" disabled={!customSize.trim()} onClick={() => (toggleSize(customSize.trim()), setCustomSize(''))}>
              <PlusIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between rounded-xl bg-rose-50 px-4 py-3">
        <span className="text-sm font-medium">Har biriga boshlangʻich qoldiq</span>
        <QtyStepper value={stock} max={10000} onChange={(n) => setStock(Math.max(0, n))} />
      </div>
    </Sheet>
  )
}

function VariantRow({ v, productId, basePrice }) {
  const [stock, setStock] = useState(v.stock)
  const [priceOpen, setPriceOpen] = useState(false)
  const [price, setPrice] = useState(v.price_override == null ? '' : String(v.price_override))
  const update = useProductMutation(productId, (patch) => api.patch(`/admin/variants/${v.id}`, patch))
  const remove = useProductMutation(productId, () => api.delete(`/admin/variants/${v.id}`))
  useEffect(() => setStock(v.stock), [v.stock])

  // Save stock 600 ms after the last tap.
  useEffect(() => {
    if (stock === v.stock) return
    const id = setTimeout(() => update.mutate({ stock }, { onError: (e) => (toast.error(e), setStock(v.stock)) }), 600)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stock])

  return (
    <li className="flex items-center gap-2 py-2.5">
      {v.color_hex && <span className="h-6 w-6 shrink-0 rounded-full border border-black/10" style={{ background: v.color_hex }} />}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{[v.color_uz, v.size].filter(Boolean).join(' · ') || 'Asosiy'}</p>
        <button type="button" onClick={() => setPriceOpen(true)} className="text-xs text-ink-soft underline decoration-dotted">
          {money(v.price_override ?? basePrice)}
          {v.price_override != null && ' (alohida narx)'}
        </button>
      </div>
      <QtyStepper value={stock} max={100000} onChange={(n) => setStock(Math.max(0, n))} />
      <button
        type="button"
        aria-label="delete"
        onClick={async () => (await confirmDialog('Variantni oʻchirasizmi?')) && remove.mutate(undefined, { onError: toast.error })}
        className="p-1.5 text-ink-faint"
      >
        <TrashIcon className="h-5 w-5" />
      </button>
      <Sheet
        open={priceOpen}
        onClose={() => setPriceOpen(false)}
        title="Variant narxi"
        footer={
          <Button
            className="w-full"
            loading={update.isPending}
            onClick={() =>
              update.mutate({ price_override: price === '' ? null : Number(price) }, { onSuccess: () => setPriceOpen(false), onError: toast.error })
            }
          >
            Saqlash
          </Button>
        }
      >
        <p className="mb-3 text-sm text-ink-soft">Boʻsh qoldirilsa, mahsulot narxi ({money(basePrice)}) ishlatiladi.</p>
        <input className="field" inputMode="numeric" placeholder={String(basePrice)} value={price} onChange={(e) => setPrice(digits(e.target.value))} />
      </Sheet>
    </li>
  )
}

function Variants({ product }) {
  const [open, setOpen] = useState(false)
  return (
    <Section title={`Variantlar va qoldiq · ${product.total_stock} dona`}>
      {product.variants.length === 0 ? (
        <p className="mb-3 text-sm text-ink-soft">Rang va oʻlchamlarni qoʻshing — har birining qoldigʻi alohida hisoblanadi.</p>
      ) : (
        <ul className="mb-3 divide-y divide-rose-100">
          {product.variants.map((v) => (
            <VariantRow key={v.id} v={v} productId={product.id} basePrice={product.price} />
          ))}
        </ul>
      )}
      <Button variant="outline" className="w-full" onClick={() => setOpen(true)}>
        <PlusIcon className="h-5 w-5" /> Variant qoʻshish
      </Button>
      <AddVariantsSheet open={open} onClose={() => setOpen(false)} product={product} />
    </Section>
  )
}

// ── size chart ────────────────────────────────────────────────────────────────

function SizeChartEditor({ product }) {
  const sizes = [...new Set(product.variants.map((v) => v.size).filter(Boolean))]
  const initial = product.size_chart
  const [columns, setColumns] = useState(initial?.columns ?? [])
  const [cells, setCells] = useState(() => {
    const m = {}
    initial?.rows?.forEach((r) =>
      (initial.columns || []).forEach((c) => {
        const v = r[c]
        m[`${r.size}|${c}`] = Array.isArray(v) ? [String(v[0]), String(v[1])] : v == null ? ['', ''] : [String(v), '']
      }),
    )
    return m
  })
  const save = useProductMutation(product.id, (size_chart) => api.patch(`/admin/products/${product.id}`, { size_chart }))
  if (sizes.length === 0) return null

  const cell = (s, c) => cells[`${s}|${c}`] ?? ['', '']
  const setCell = (s, c, i, value) =>
    setCells((m) => {
      const next = [...cell(s, c)]
      next[i] = value.replace(/[^\d.]/g, '')
      return { ...m, [`${s}|${c}`]: next }
    })

  function submit() {
    if (columns.length === 0) {
      save.mutate(null, { onSuccess: () => toast.show('Jadval olib tashlandi'), onError: toast.error })
      return
    }
    const rows = sizes.map((s) => {
      const row = { size: s }
      columns.forEach((c) => {
        const [a, b] = cell(s, c)
        if (a && b) row[c] = [Number(a), Number(b)]
        else if (a || b) row[c] = Number(a || b)
      })
      return row
    })
    save.mutate({ columns, rows }, { onSuccess: () => (haptic.success(), toast.show('Jadval saqlandi')), onError: toast.error })
  }

  return (
    <Section title="Oʻlchamlar jadvali">
      <p className="mb-2 text-xs text-ink-soft">
        Qaysi oʻlchovlar kerak? Har bir oʻlcham uchun santimetrda «dan — gacha» kiriting. Mijozlar «Oʻlchamimni aniqlash» orqali shundan foydalanadi.
      </p>
      <div className="mb-3 flex flex-wrap gap-2">
        {CHART_COLUMNS.map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setColumns((cs) => (cs.includes(key) ? cs.filter((x) => x !== key) : [...cs, key]))}
            className={`chip ${columns.includes(key) ? 'border-rose-600 bg-rose-600 text-white' : 'border-rose-200 bg-white text-ink'}`}
          >
            {label}
          </button>
        ))}
      </div>
      {columns.length > 0 && (
        <div className="space-y-3">
          {sizes.map((s) => (
            <div key={s} className="rounded-xl bg-rose-50 p-3">
              <p className="mb-2 font-semibold">{s}</p>
              <div className="space-y-2">
                {columns.map((c) => (
                  <div key={c} className="flex items-center gap-2 text-sm">
                    <span className="w-28 shrink-0 text-ink-soft">{CHART_COLUMNS.find(([k]) => k === c)?.[1] ?? c}</span>
                    <input className="field h-9 py-0 text-sm" inputMode="decimal" placeholder="dan" value={cell(s, c)[0]} onChange={(e) => setCell(s, c, 0, e.target.value)} />
                    <span className="text-ink-faint">—</span>
                    <input className="field h-9 py-0 text-sm" inputMode="decimal" placeholder="gacha" value={cell(s, c)[1]} onChange={(e) => setCell(s, c, 1, e.target.value)} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
      <Button variant="secondary" className="mt-3 w-full" loading={save.isPending} onClick={submit}>
        Jadvalni saqlash
      </Button>
    </Section>
  )
}

// ── page ──────────────────────────────────────────────────────────────────────

export default function ProductEditPage() {
  const { id } = useParams()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const product = useAdminProduct(isNew ? null : id)
  const { data: catData } = useCategories()
  const [form, setForm] = useState(emptyForm)
  const [loadedId, setLoadedId] = useState(null)
  const set = (patch) => setForm((f) => ({ ...f, ...patch }))

  // Fill the form once when the product arrives (not on every refetch, so
  // edits in progress aren't overwritten).
  if (product.data && loadedId !== product.data.id) {
    setLoadedId(product.data.id)
    setForm(toForm(product.data))
  }

  const create = useProductMutation(null, (body) => api.post('/admin/products', body))
  const update = useProductMutation(id, (body) => api.patch(`/admin/products/${id}`, body))
  const remove = useProductMutation(id, () => api.delete(`/admin/products/${id}`))

  if (!isNew && product.isPending) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    )
  }
  if (!isNew && product.isError) return <ErrorState error={product.error} onRetry={product.refetch} />

  const p = product.data
  const valid = form.name_uz.trim() && digits(form.price)
  const dirty = isNew || (p && JSON.stringify(toForm(p)) !== JSON.stringify(form))

  function saveInfo() {
    if (!valid) {
      haptic.error()
      toast.error('Nomi va narxini kiriting')
      return
    }
    if (isNew) {
      create.mutate(toBody(form), {
        onSuccess: (created) => {
          haptic.success()
          toast.show('Yaratildi — endi rasm va variantlarni qoʻshing')
          navigate(`/admin/products/${created.id}`, { replace: true })
        },
        onError: toast.error,
      })
    } else {
      update.mutate(toBody(form), { onSuccess: () => (haptic.success(), toast.show('Saqlandi')), onError: toast.error })
    }
  }

  async function deleteProduct() {
    if (!(await confirmDialog('Mahsulot butunlay oʻchiriladi. Eski buyurtmalar saqlanib qoladi. Davom etasizmi?'))) return
    remove.mutate(undefined, { onSuccess: () => navigate('/admin/products', { replace: true }), onError: toast.error })
  }

  return (
    <div className="space-y-3 px-4 pb-4 pt-4">
      <h1 className="font-serif text-[28px] font-semibold leading-tight">{isNew ? 'Yangi mahsulot' : p.name_uz}</h1>

      <Section title="Asosiy maʼlumot">
        <InfoForm form={form} set={set} categories={catData?.categories ?? []} />
      </Section>

      {isNew ? (
        <p className="px-1 text-sm text-ink-soft">Saqlangandan keyin rasmlar, ranglar va oʻlchamlarni qoʻsha olasiz.</p>
      ) : (
        <>
          <Photos product={p} />
          <Variants product={p} />
          <SizeChartEditor key={p.id + (p.variants.length ? 'v' : '')} product={p} />
          {p.is_active && (p.images.length === 0 || p.variants.length === 0) && (
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
              ⚠️ Mahsulot doʻkonda koʻrinmoqda, lekin {p.images.length === 0 ? 'rasmi' : 'varianti'} yoʻq — mijozlar uni sotib ololmaydi.
            </p>
          )}
          <Button variant="danger" className="w-full" loading={remove.isPending} onClick={deleteProduct}>
            <TrashIcon className="h-5 w-5" /> Mahsulotni oʻchirish
          </Button>
        </>
      )}

      {dirty && (
        <StickyBar>
          <Button className="w-full" loading={create.isPending || update.isPending} onClick={saveInfo}>
            {isNew ? 'Yaratish' : 'Oʻzgarishlarni saqlash'}
          </Button>
        </StickyBar>
      )}
    </div>
  )
}
