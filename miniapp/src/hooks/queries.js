// All server state goes through TanStack Query: cached, deduplicated,
// refetched on focus. Mutations update or invalidate the affected queries.
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import i18n from '../i18n'
import { api } from '../lib/api'

export const keys = {
  meta: ['meta'],
  products: (filters) => ['products', filters],
  product: (id) => ['product', id],
  favorites: ['favorites'],
  quote: (items, promo) => ['quote', items, promo],
  orders: ['orders'],
  order: (id) => ['order', id],
}

// Applies the saved profile language *before* any page renders with the data.
// (Switching it later from an effect races with components subscribing to
// i18n, and the first switch could be missed.)
async function fetchMeta() {
  const meta = await api.get('/meta')
  const lang = meta.me?.language
  if (lang && lang !== i18n.language) await i18n.changeLanguage(lang)
  return meta
}

export function useMeta() {
  return useQuery({ queryKey: keys.meta, queryFn: fetchMeta, staleTime: 5 * 60_000 })
}

export function useProducts(filters) {
  return useInfiniteQuery({
    queryKey: keys.products(filters),
    queryFn: ({ pageParam }) => api.get('/products', { ...filters, page: pageParam, limit: 20 }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.pages ? last.page + 1 : undefined),
    staleTime: 60_000,
  })
}

export function useProduct(id) {
  return useQuery({ queryKey: keys.product(id), queryFn: () => api.get(`/products/${id}`), staleTime: 60_000 })
}

export function useFavorites() {
  return useQuery({ queryKey: keys.favorites, queryFn: () => api.get('/favorites') })
}

export function useToggleFavorite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, on }) => (on ? api.put(`/favorites/${id}`) : api.delete(`/favorites/${id}`)),
    // Flip the heart immediately everywhere; roll back if the request fails.
    onMutate: async ({ id, on }) => {
      const patch = (p) => (p?.id === id ? { ...p, is_favorite: on } : p)
      const productLists = qc.getQueriesData({ queryKey: ['products'] })
      const detail = qc.getQueryData(keys.product(id))
      qc.setQueriesData({ queryKey: ['products'] }, (data) =>
        data && { ...data, pages: data.pages.map((pg) => ({ ...pg, products: pg.products.map(patch) })) },
      )
      if (detail) qc.setQueryData(keys.product(id), patch(detail))
      return { productLists, detail }
    },
    onError: (_err, { id }, ctx) => {
      ctx?.productLists?.forEach(([key, data]) => qc.setQueryData(key, data))
      if (ctx?.detail) qc.setQueryData(keys.product(id), ctx.detail)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: keys.favorites }),
  })
}

export function useQuote(items, promoCode) {
  const lines = items.map((i) => ({ variant_id: i.variant_id, quantity: i.quantity }))
  return useQuery({
    queryKey: keys.quote(lines, promoCode),
    queryFn: () => api.post('/cart/quote', { items: lines, promo_code: promoCode || null }),
    enabled: lines.length > 0,
    placeholderData: (prev) => prev, // keep showing the last total while re-pricing
  })
}

export function useCreateOrder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body) => api.post('/orders', body),
    onSuccess: (order) => {
      qc.setQueryData(keys.order(order.id), order)
      qc.invalidateQueries({ queryKey: keys.orders })
      qc.invalidateQueries({ queryKey: ['products'] }) // stock changed
      qc.invalidateQueries({ queryKey: keys.meta }) // phone/name may have been saved
    },
  })
}

export function useOrders() {
  return useQuery({ queryKey: keys.orders, queryFn: () => api.get('/orders', { limit: 50 }) })
}

export function useOrder(id) {
  return useQuery({
    queryKey: keys.order(id),
    queryFn: () => api.get(`/orders/${id}`),
    // While an order is moving, check for admin updates now and then.
    refetchInterval: (q) => (['payment_review', 'confirmed', 'shipped'].includes(q.state.data?.status) ? 30_000 : false),
  })
}

function useOrderMutation(fn) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (order) => {
      qc.setQueryData(keys.order(order.id), order)
      qc.invalidateQueries({ queryKey: keys.orders })
    },
  })
}

export function useSubmitPayment(orderId) {
  return useOrderMutation(({ file, cardId }) => {
    const form = new FormData()
    form.append('receipt', file)
    if (cardId) form.append('card_id', cardId)
    return api.upload(`/orders/${orderId}/payment`, form)
  })
}

export function useCancelOrder(orderId) {
  return useOrderMutation(() => api.post(`/orders/${orderId}/cancel`))
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (patch) => api.patch('/me', patch),
    onSuccess: (me) => qc.setQueryData(keys.meta, (meta) => meta && { ...meta, me }),
  })
}
