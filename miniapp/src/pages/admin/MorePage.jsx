import { Link } from 'react-router-dom'
import { BookIcon, ChevronRightIcon, GridIcon, ShieldIcon, SlidersIcon, UserIcon } from '../../components/icons'
import { useIsSuperAdmin } from '../../hooks/admin'
import { AdminHeader } from './AdminLayout'

const ITEMS = [
  { to: '/admin/categories', icon: GridIcon, label: 'Kategoriyalar', hint: 'Roʻmollar, liboslar…' },
  { to: '/admin/promo', icon: BookIcon, label: 'Promokodlar', hint: 'Chegirma kodlari' },
  { to: '/admin/cards', icon: ShieldIcon, label: 'Toʻlov kartalari', hint: 'Mijozlar shu kartalarga toʻlaydi', superOnly: true },
  { to: '/admin/settings', icon: SlidersIcon, label: 'Sozlamalar', hint: 'Bron muddati, doʻkon qoidalari', superOnly: true },
  { to: '/admin/staff', icon: UserIcon, label: 'Xodimlar', hint: 'Admin tayinlash', superOnly: true },
]

export default function MorePage() {
  const isSuper = useIsSuperAdmin()
  return (
    <div>
      <AdminHeader title="Boshqa" />
      <div className="card mx-4 divide-y divide-rose-100 overflow-hidden">
        {ITEMS.filter((i) => isSuper || !i.superOnly).map(({ to, icon: Icon, label, hint }) => (
          <Link key={to} to={to} className="flex items-center gap-3 px-4 py-3.5 active:bg-rose-50/60">
            <Icon className="h-5 w-5 shrink-0 text-rose-500" />
            <span className="flex-1">
              <span className="block text-[15px]">{label}</span>
              <span className="block text-xs text-ink-soft">{hint}</span>
            </span>
            <ChevronRightIcon className="h-4 w-4 text-ink-faint" />
          </Link>
        ))}
      </div>
    </div>
  )
}
