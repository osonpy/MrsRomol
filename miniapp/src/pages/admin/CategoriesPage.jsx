import { useState } from 'react'
import { GridIcon, PlusIcon, TrashIcon } from '../../components/icons'
import { Button, EmptyState, ErrorState, Sheet, Skeleton } from '../../components/ui'
import { adminKeys, useCategories, useListMutation } from '../../hooks/admin'
import { api } from '../../lib/api'
import { confirmDialog, haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'
import { AdminHeader } from './AdminLayout'

// "Roʻmollar va shapkalar" → "romollar-va-shapkalar"
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[ʻʼ'`‘’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64)
}

function CategorySheet({ category, nextSort, onClose }) {
  const isNew = !category.id
  const [form, setForm] = useState({
    name_uz: category.name_uz || '',
    name_ru: category.name_ru || '',
    sort_order: category.sort_order ?? nextSort, // new ones go to the end
    is_active: category.is_active ?? true,
  })
  const save = useListMutation(
    adminKeys.categories,
    (body) => (isNew ? api.post('/admin/categories', body) : api.patch(`/admin/categories/${category.id}`, body)),
    { refreshMeta: true },
  )
  const valid = form.name_uz.trim() && form.name_ru.trim() && slugify(form.name_uz)

  function submit() {
    const body = { ...form, name_uz: form.name_uz.trim(), name_ru: form.name_ru.trim(), sort_order: Number(form.sort_order) || 0 }
    if (isNew) body.slug = slugify(form.name_uz)
    save.mutate(body, {
      onSuccess: () => {
        haptic.success()
        toast.show('Saqlandi')
        onClose()
      },
      onError: (err) => toast.error(err.code === 'CONFLICT' ? 'Bunday kategoriya allaqachon bor' : err),
    })
  }

  return (
    <Sheet
      open
      onClose={onClose}
      title={isNew ? 'Yangi kategoriya' : 'Kategoriya'}
      footer={
        <Button className="w-full" disabled={!valid} loading={save.isPending} onClick={submit}>
          Saqlash
        </Button>
      }
    >
      <div className="space-y-3">
        <label className="block">
          <span className="label">Nomi (oʻzbekcha)</span>
          <input className="field" value={form.name_uz} onChange={(e) => setForm({ ...form, name_uz: e.target.value })} placeholder="Roʻmollar" />
        </label>
        <label className="block">
          <span className="label">Nomi (ruscha)</span>
          <input className="field" value={form.name_ru} onChange={(e) => setForm({ ...form, name_ru: e.target.value })} placeholder="Платки" />
        </label>
        <label className="block">
          <span className="label">Tartib raqami (kichigi oldinda)</span>
          <input className="field" inputMode="numeric" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: e.target.value.replace(/\D/g, '') })} />
        </label>
        <label className="flex items-center justify-between rounded-xl bg-rose-50 px-4 py-3">
          <span className="font-medium">Doʻkonda koʻrsatish</span>
          <input type="checkbox" className="h-6 w-6 accent-rose-600" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
        </label>
      </div>
    </Sheet>
  )
}

export default function CategoriesPage() {
  const { data, isPending, isError, error, refetch } = useCategories()
  const [editing, setEditing] = useState(null)
  const remove = useListMutation(adminKeys.categories, (id) => api.delete(`/admin/categories/${id}`), { refreshMeta: true })

  async function onDelete(c) {
    if (!(await confirmDialog(`«${c.name_uz}» oʻchirilsinmi? Mahsulotlar oʻchmaydi, faqat kategoriyasiz qoladi.`))) return
    remove.mutate(c.id, { onSuccess: () => toast.show('Oʻchirildi'), onError: toast.error })
  }

  return (
    <div className="pb-6">
      <AdminHeader
        title="Kategoriyalar"
        right={
          <Button className="h-10 px-4 text-sm" onClick={() => setEditing({})}>
            <PlusIcon className="h-5 w-5" /> Qoʻshish
          </Button>
        }
      />
      {isPending ? (
        <div className="space-y-2 px-4">
          <Skeleton className="h-14 w-full rounded-2xl" />
          <Skeleton className="h-14 w-full rounded-2xl" />
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.categories.length === 0 ? (
        <EmptyState icon={GridIcon} title="Kategoriya yoʻq" text="Masalan: Roʻmollar, Liboslar, Shapkalar" action={<Button onClick={() => setEditing({})}>Qoʻshish</Button>} />
      ) : (
        <ul className="card mx-4 divide-y divide-rose-100 overflow-hidden">
          {data.categories.map((c) => (
            <li key={c.id} className="flex items-center gap-2 pr-2">
              <button type="button" onClick={() => setEditing(c)} className="flex-1 px-4 py-3 text-left active:bg-rose-50/60">
                <span className="block text-[15px]">
                  {c.name_uz}
                  {!c.is_active && <span className="ml-2 rounded bg-stone-200 px-1.5 text-[11px] font-semibold text-stone-700">Yashirin</span>}
                </span>
                <span className="block text-xs text-ink-soft">{c.name_ru}</span>
              </button>
              <button type="button" aria-label="delete" onClick={() => onDelete(c)} className="p-2 text-ink-faint">
                <TrashIcon className="h-5 w-5" />
              </button>
            </li>
          ))}
        </ul>
      )}
      {editing && (
        <CategorySheet
          category={editing}
          nextSort={Math.max(0, ...(data?.categories ?? []).map((c) => c.sort_order)) + 1}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
