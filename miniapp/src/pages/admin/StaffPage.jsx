import { useEffect, useState } from 'react'
import { SearchIcon } from '../../components/icons'
import { Button, ErrorState, Section, Skeleton } from '../../components/ui'
import { adminKeys, useCustomerSearch, useListMutation, useStaff } from '../../hooks/admin'
import { api } from '../../lib/api'
import { phone } from '../../lib/format'
import { confirmDialog, haptic } from '../../lib/telegram'
import { toast } from '../../lib/toast'
import { AdminHeader } from './AdminLayout'

const ROLE_LABEL = { super_admin: 'Egasi', admin: 'Admin', seller: 'Sotuvchi', customer: 'Mijoz' }

function Person({ p, action }) {
  return (
    <li className="flex items-center gap-3 py-3">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-100 font-semibold text-rose-700">
        {(p.full_name || '?').charAt(0).toUpperCase()}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{p.full_name || 'Ismsiz'}</p>
        <p className="truncate text-xs text-ink-soft">
          {p.phone ? phone(p.phone) : `ID ${p.telegram_id}`} · {ROLE_LABEL[p.role]}
        </p>
      </div>
      {action}
    </li>
  )
}

export default function StaffPage() {
  const staff = useStaff()
  const [text, setText] = useState('')
  const [q, setQ] = useState('')
  useEffect(() => {
    const id = setTimeout(() => setQ(text.trim()), 350)
    return () => clearTimeout(id)
  }, [text])
  const search = useCustomerSearch(q)
  const setRole = useListMutation(adminKeys.staff, ({ telegramId, role }) => api.put(`/admin/staff/${telegramId}`, { role }))

  async function change(p, role) {
    const question =
      role === 'admin'
        ? `${p.full_name || 'Bu foydalanuvchi'} admin boʻladi: buyurtmalar, mahsulotlar va promokodlarni boshqara oladi. Davom etasizmi?`
        : `${p.full_name || 'Bu foydalanuvchi'} adminlikdan olinadi. Davom etasizmi?`
    if (!(await confirmDialog(question))) return
    setRole.mutate(
      { telegramId: p.telegram_id, role },
      {
        onSuccess: () => {
          haptic.success()
          toast.show(role === 'admin' ? 'Admin tayinlandi' : 'Adminlikdan olindi')
          search.refetch()
        },
        onError: toast.error,
      },
    )
  }

  return (
    <div className="space-y-3 px-4 pb-6">
      <div className="-mx-4">
        <AdminHeader title="Xodimlar" />
      </div>

      <Section title="Hozirgi xodimlar">
        {staff.isPending ? (
          <Skeleton className="h-14 w-full" />
        ) : staff.isError ? (
          <ErrorState error={staff.error} onRetry={staff.refetch} />
        ) : (
          <ul className="divide-y divide-rose-100">
            {staff.data.staff.map((p) => (
              <Person
                key={p.id}
                p={p}
                action={
                  p.role !== 'super_admin' && (
                    <Button variant="outline" className="h-9 px-3 text-sm" onClick={() => change(p, 'customer')}>
                      Olib tashlash
                    </Button>
                  )
                }
              />
            ))}
          </ul>
        )}
      </Section>

      <Section title="Admin qoʻshish">
        <p className="mb-3 text-sm text-ink-soft">
          Avval u kishi botda /start bosib, doʻkonni bir marta ochishi kerak. Keyin uni ismi, telefoni yoki Telegram ID orqali toping.
        </p>
        <label className="relative block">
          <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
          <input
            className="field pl-11"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ism, telefon yoki ID"
          />
        </label>
        {q.length >= 2 && (
          <ul className="mt-2 divide-y divide-rose-100">
            {search.data?.customers.length === 0 && <li className="py-3 text-sm text-ink-soft">Topilmadi</li>}
            {search.data?.customers.map((p) => (
              <Person
                key={p.id}
                p={p}
                action={
                  p.role === 'customer' ? (
                    <Button className="h-9 px-3 text-sm" onClick={() => change(p, 'admin')}>
                      Admin qilish
                    </Button>
                  ) : (
                    <span className="text-xs font-semibold text-rose-700">{ROLE_LABEL[p.role]}</span>
                  )
                }
              />
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}
