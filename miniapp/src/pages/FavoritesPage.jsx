import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { HeartIcon } from '../components/icons'
import { ProductGrid, ProductGridSkeleton } from '../components/product'
import { Button, EmptyState, ErrorState, PageTitle } from '../components/ui'
import { useFavorites } from '../hooks/queries'

export default function FavoritesPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data, isPending, isError, error, refetch } = useFavorites()

  return (
    <div>
      <PageTitle>{t('favorites.title')}</PageTitle>
      {isPending ? (
        <ProductGridSkeleton count={4} />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : data.products.length === 0 ? (
        <EmptyState
          icon={HeartIcon}
          title={t('favorites.empty_title')}
          text={t('favorites.empty_text')}
          action={<Button onClick={() => navigate('/')}>{t('cart.to_catalog')}</Button>}
        />
      ) : (
        <ProductGrid products={data.products} />
      )}
    </div>
  )
}
