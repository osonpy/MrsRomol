import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { BellIcon, BookIcon, ChevronRightIcon, GlobeIcon, ShieldIcon } from '../components/icons'
import { Button, PageTitle, Sheet } from '../components/ui'
import { toast } from '../lib/toast'
import { useMeta, useUpdateProfile } from '../hooks/queries'
import i18n from '../i18n'
import { phone } from '../lib/format'
import { haptic } from '../lib/telegram'

function Row({ icon: Icon, label, value, onClick, to, children }) {
  const inner = (
    <>
      <Icon className="h-5 w-5 shrink-0 text-rose-500" />
      <span className="flex-1 text-[15px] text-ink">{label}</span>
      {value && <span className="truncate text-sm text-ink-soft">{value}</span>}
      {children}
      {(onClick || to) && <ChevronRightIcon className="h-4 w-4 shrink-0 text-ink-faint" />}
    </>
  )
  const cls = 'flex w-full items-center gap-3 px-4 py-3.5 text-left active:bg-rose-50/60'
  if (to) return <Link to={to} className={cls}>{inner}</Link>
  if (onClick) return <button type="button" onClick={onClick} className={cls}>{inner}</button>
  return <div className={cls}>{inner}</div>
}

function Toggle({ checked, onChange, disabled }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-7 w-12 shrink-0 rounded-full transition ${checked ? 'bg-rose-600' : 'bg-rose-200'}`}
    >
      <span className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all ${checked ? 'left-[1.375rem]' : 'left-0.5'}`} />
    </button>
  )
}

function EditSheet({ open, onClose, me }) {
  const { t } = useTranslation()
  const update = useUpdateProfile()
  const [name, setName] = useState(me.full_name)
  const [tel, setTel] = useState(me.phone)

  function save() {
    const patch = {}
    if (name.trim() && name.trim() !== me.full_name) patch.full_name = name.trim()
    if (tel.trim() && tel.trim() !== me.phone) patch.phone = tel.trim()
    if (!Object.keys(patch).length) return onClose()
    update.mutate(patch, {
      onSuccess: () => {
        toast.show(t('profile.saved'))
        onClose()
      },
      onError: toast.error,
    })
  }

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={t('profile.edit')}
      footer={
        <Button className="w-full" loading={update.isPending} onClick={save}>
          {t('common.save')}
        </Button>
      }
    >
      <div className="space-y-3">
        <label className="block">
          <span className="label">{t('profile.name')}</span>
          <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="block">
          <span className="label">{t('profile.phone')}</span>
          <input className="field" type="tel" inputMode="tel" placeholder="+998 90 123 45 67" value={tel} onChange={(e) => setTel(e.target.value)} />
        </label>
      </div>
    </Sheet>
  )
}

export default function ProfilePage() {
  const { t } = useTranslation()
  const { data: meta } = useMeta()
  const update = useUpdateProfile()
  const [editing, setEditing] = useState(false)
  const [rulesOpen, setRulesOpen] = useState(false)
  const me = meta.me
  const lang = i18n.language === 'ru' ? 'ru' : 'uz'
  const rules = meta.rules?.[lang] || meta.rules?.uz

  function setLanguage(next) {
    if (next === lang) return
    haptic.select()
    i18n.changeLanguage(next)
    update.mutate({ language: next }, { onError: toast.error })
  }

  return (
    <div>
      <PageTitle>{t('profile.title')}</PageTitle>

      <div className="px-4">
        <button type="button" onClick={() => setEditing(true)} className="card flex w-full items-center gap-4 p-4 text-left active:bg-rose-50/60">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-100 font-serif text-2xl font-semibold text-rose-700">
            {(me.full_name || '?').trim().charAt(0).toUpperCase()}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-lg font-semibold">{me.full_name || t('profile.not_set')}</span>
            <span className="block text-sm text-ink-soft">{me.phone ? phone(me.phone) : t('profile.not_set')}</span>
          </span>
          <span className="text-sm font-semibold text-rose-700">{t('profile.edit')}</span>
        </button>

        <div className="card mt-3 divide-y divide-rose-100 overflow-hidden">
          <Row icon={GlobeIcon} label={t('profile.language')}>
            <div className="flex rounded-full bg-rose-100 p-0.5">
              {['uz', 'ru'].map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setLanguage(l)}
                  className={`rounded-full px-3.5 py-1 text-sm font-semibold transition ${lang === l ? 'bg-white text-rose-700 shadow' : 'text-ink-soft'}`}
                >
                  {l === 'uz' ? 'Oʻzbek' : 'Русский'}
                </button>
              ))}
            </div>
          </Row>
          <div className="px-4 py-3.5">
            <div className="flex items-center gap-3">
              <BellIcon className="h-5 w-5 shrink-0 text-rose-500" />
              <span className="flex-1 text-[15px]">{t('profile.notifications')}</span>
              <Toggle
                checked={me.notify_new_products}
                onChange={(v) => (haptic.select(), update.mutate({ notify_new_products: v }, { onError: toast.error }))}
              />
            </div>
            <p className="ml-8 mt-1 text-xs text-ink-soft">{t('profile.notifications_hint')}</p>
          </div>
          <Row icon={BookIcon} label={t('profile.rules')} onClick={() => setRulesOpen(true)} />
        </div>

        {['admin', 'super_admin'].includes(me.role) && (
          <div className="card mt-3 overflow-hidden">
            <Row icon={ShieldIcon} label={t('profile.admin')} to="/admin" />
          </div>
        )}

        <div className="mt-8 flex flex-col items-center gap-2 pb-4 opacity-70">
          <img src="/logo.webp" alt="Mrs Romol" className="w-32" />
        </div>
      </div>

      {editing && <EditSheet open onClose={() => setEditing(false)} me={me} />}
      <Sheet open={rulesOpen} onClose={() => setRulesOpen(false)} title={t('profile.rules')}>
        <p className="whitespace-pre-line pb-4 leading-relaxed text-ink">{rules || t('profile.no_rules')}</p>
      </Sheet>
    </div>
  )
}
