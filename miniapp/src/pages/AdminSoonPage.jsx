import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ShieldIcon } from '../components/icons'
import { Button, EmptyState } from '../components/ui'

// Placeholder until the admin section is built (phase 4).
export default function AdminSoonPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  return (
    <EmptyState
      icon={ShieldIcon}
      title={t('profile.admin')}
      text={t('profile.admin_soon')}
      action={<Button variant="outline" onClick={() => navigate('/', { replace: true })}>{t('common.back_home')}</Button>}
    />
  )
}
