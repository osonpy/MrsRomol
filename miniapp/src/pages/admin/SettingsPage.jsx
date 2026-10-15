import { useState } from 'react'
import { Button, ErrorState, Section, Skeleton, StickyBar } from '../../components/ui'
import { adminKeys, useListMutation, useSettings } from '../../hooks/admin'
import { api } from '../../lib/api'
import { haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'
import { AdminHeader } from './AdminLayout'

function SettingsForm({ settings }) {
  const initial = {
    reservation_minutes: String(settings.reservation_minutes ?? 30),
    rules_uz: settings.rules_uz ?? '',
    rules_ru: settings.rules_ru ?? '',
  }
  const [form, setForm] = useState(initial)
  const save = useListMutation(adminKeys.settings, (body) => api.patch('/admin/settings', body), { refreshMeta: true })
  const minutes = Number(form.reservation_minutes)
  const dirty = JSON.stringify(form) !== JSON.stringify(initial)
  const valid = minutes >= 5 && minutes <= 1440

  return (
    <div className="space-y-3 px-4">
      <Section title="Bron muddati">
        <label className="block">
          <span className="label">Buyurtmadan keyin toʻlov uchun necha daqiqa (5–1440)</span>
          <input
            className="field"
            inputMode="numeric"
            value={form.reservation_minutes}
            onChange={(e) => setForm({ ...form, reservation_minutes: e.target.value.replace(/\D/g, '') })}
          />
        </label>
        <p className="mt-2 text-xs text-ink-soft">Shu vaqt ichida chek kelmasa, buyurtma avtomatik bekor boʻladi va mahsulot sotuvga qaytadi.</p>
      </Section>
      <Section title="Doʻkon qoidalari">
        <label className="block">
          <span className="label">Oʻzbekcha</span>
          <textarea className="field min-h-[8rem]" value={form.rules_uz} onChange={(e) => setForm({ ...form, rules_uz: e.target.value })} placeholder="Sotilgan mahsulot qaytarilmaydi…" />
        </label>
        <label className="mt-3 block">
          <span className="label">Ruscha</span>
          <textarea className="field min-h-[8rem]" value={form.rules_ru} onChange={(e) => setForm({ ...form, rules_ru: e.target.value })} placeholder="Проданный товар возврату не подлежит…" />
        </label>
        <p className="mt-2 text-xs text-ink-soft">Mijozlar buni Profil → «Doʻkon qoidalari» da koʻradi.</p>
      </Section>
      {dirty && (
        <StickyBar>
          <Button
            className="w-full"
            disabled={!valid}
            loading={save.isPending}
            onClick={() =>
              save.mutate(
                { reservation_minutes: minutes, rules_uz: form.rules_uz.trim(), rules_ru: form.rules_ru.trim() },
                { onSuccess: () => (haptic.success(), toast.show('Saqlandi')), onError: toast.error },
              )
            }
          >
            Saqlash
          </Button>
        </StickyBar>
      )}
    </div>
  )
}

export default function SettingsPage() {
  const { data, isPending, isError, error, refetch } = useSettings()
  return (
    <div className="pb-6">
      <AdminHeader title="Sozlamalar" />
      {isPending ? (
        <Skeleton className="mx-4 h-64 rounded-2xl" />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <SettingsForm key={JSON.stringify(data)} settings={data} />
      )}
    </div>
  )
}
