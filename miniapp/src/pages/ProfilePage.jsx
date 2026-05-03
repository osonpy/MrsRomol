import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useUserStore } from '../store/userStore'
import { useOrders } from '../hooks/useOrders'
import { customersApi } from '../api/customers'
import { Button } from '../components/ui/Button'
import { PageWrapper } from '../components/layout/PageWrapper'
import { formatPrice } from '../utils/formatPrice'

const LANGUAGES = [
  { code: 'uz', label: "O'zbekcha", flag: '🇺🇿' },
  { code: 'ru', label: 'Русский',   flag: '🇷🇺' },
  { code: 'en', label: 'English',   flag: '🇬🇧' },
]

export default function ProfilePage() {
  const { t, i18n } = useTranslation()
  const { customer, telegramUser, setCustomer } = useUserStore()
  const { orders } = useOrders()

  const [phone, setPhone] = useState(customer?.phone || '')
  const [lang, setLang] = useState(customer?.language || i18n.language || 'uz')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState(null)

  useEffect(() => {
    if (customer) {
      setPhone(customer.phone || '')
      setLang(customer.language || 'uz')
    }
  }, [customer?.id])

  const stats = {
    count: orders.length,
    total: orders.reduce((s, o) => s + parseFloat(o.total_amount || 0), 0),
  }

  const handleSave = async () => {
    if (!customer) return
    setSaving(true)
    setSaveError(null)
    try {
      const updated = await customersApi.updateMe({ phone: phone.trim(), language: lang })
      setCustomer(updated)
      await i18n.changeLanguage(lang)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setSaveError(e?.error ?? e?.message ?? t('common.error'))
    } finally {
      setSaving(false)
    }
  }

  const displayName =
    customer?.full_name ||
    [telegramUser?.first_name, telegramUser?.last_name].filter(Boolean).join(' ') ||
    'User'

  return (
    <PageWrapper>
      <div className="px-4 pt-4 pb-3 sticky top-0 z-10" style={{ background: 'var(--tg-theme-bg-color)' }}>
        <h1 className="text-xl font-bold" style={{ color: 'var(--tg-theme-text-color)' }}>
          👤 {t('profile.title')}
        </h1>
      </div>

      <div className="px-4 pb-4 space-y-4">
        <div
          className="flex items-center gap-4 p-4 rounded-2xl"
          style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
        >
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold flex-shrink-0"
            style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
          >
            {displayName.slice(0, 1).toUpperCase()}
          </div>
          <div>
            <p className="font-bold text-base" style={{ color: 'var(--tg-theme-text-color)' }}>
              {displayName}
            </p>
            {telegramUser?.username && (
              <p className="text-sm" style={{ color: 'var(--tg-theme-hint-color)' }}>
                @{telegramUser.username}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: t('profile.orders'), value: stats.count, icon: '📦' },
            { label: t('profile.spent'),  value: formatPrice(stats.total), icon: '💰' },
          ].map((stat) => (
            <div
              key={stat.label}
              className="p-4 rounded-2xl text-center"
              style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
            >
              <div className="text-2xl mb-1">{stat.icon}</div>
              <div className="text-lg font-bold" style={{ color: 'var(--tg-theme-text-color)' }}>
                {stat.value}
              </div>
              <div className="text-xs" style={{ color: 'var(--tg-theme-hint-color)' }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        <div>
          <label className="text-sm font-medium mb-1.5 block" style={{ color: 'var(--tg-theme-hint-color)' }}>
            📱 {t('profile.phone')}
          </label>
          <input
            type="tel"
            className="tg-input"
            placeholder={t('profile.phone_placeholder')}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block" style={{ color: 'var(--tg-theme-hint-color)' }}>
            🌐 {t('profile.language')}
          </label>
          <div className="grid grid-cols-3 gap-2">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                onClick={() => setLang(l.code)}
                className="p-3 rounded-xl text-center transition-all active:scale-95"
                style={{
                  background: lang === l.code ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                  color: lang === l.code ? 'var(--tg-theme-button-text-color)' : 'var(--tg-theme-text-color)',
                }}
              >
                <div className="text-xl mb-0.5">{l.flag}</div>
                <div className="text-xs font-medium">{l.label}</div>
              </button>
            ))}
          </div>
        </div>

        {saveError && (
          <div className="rounded-xl p-3 bg-red-50 border border-red-200">
            <p className="text-sm text-red-600">{saveError}</p>
          </div>
        )}

        <Button fullWidth size="lg" loading={saving} disabled={saving || !customer} onClick={handleSave}>
          {saved ? `✅ ${t('common.saved')}` : saving ? t('common.saving') : `💾 ${t('common.save')}`}
        </Button>
      </div>
    </PageWrapper>
  )
}
