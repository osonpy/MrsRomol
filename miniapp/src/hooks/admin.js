// Server state for the admin section (/admin/* API endpoints).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useMeta } from './queries'

export const adminKeys = {
  dashboard: ['admin', 'dashboard'],
  orders: (filters) => ['admin', 'orders', filters],
  order: (id) => ['admin', 'order', id],
  products: (filters) => ['admin', 'products', filters],
  product: (id) => ['admin', 'product', id],
  categories: ['admin', 'categories'],
  promos: ['admin', 'promos'],
  cards: ['admin', 'cards'],
  settings: ['admin', 'settings'],
  staff: ['admin', 'staff'],
  customers: (q) => ['admin', 'customers', q],
}

export function useIsSuperAdmin() {
  return useMeta().data?.me?.role === 'super_admin'
}

// ── dashboard & orders ────────────────────────────────────────────────────────

export function useDashboard() {
  return useQuery({ queryKey: adminKeys.dashboard, queryFn: () => api.get('/admin/dashboard'), refetchInterval: 60_000 })
}

export function useAdminOrders(filters) {
  return useQuery({
    queryKey: adminKeys.orders(filters),
    queryFn: () => api.get('/admin/orders', { ...filters, limit: 50 }),
    placeholderData: (prev) => prev,
  })
}

export function useAdminOrder(id) {
  return useQuery({ queryKey: adminKeys.order(id), queryFn: () => api.get(`/admin/orders/${id}`) })
}

// Every order action returns the updated order.
function useOrderAction(id, fn) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (order) => {
      qc.setQueryData(adminKeys.order(id), order)
      qc.invalidateQueries({ queryKey: ['admin', 'orders'] })
      qc.invalidateQueries({ queryKey: adminKeys.dashboard })
    },
  })
}

export const useReviewPayment = (orderId) =>
  useOrderAction(orderId, ({ paymentId, approve, reason }) =>
    api.post(`/admin/payments/${paymentId}/review`, { approve, reason: reason || '' }),
  )
export const useAdvanceOrder = (orderId) =>
  useOrderAction(orderId, (body) => api.post(`/admin/orders/${orderId}/advance`, body))
export const useAdminCancelOrder = (orderId) =>
  useOrderAction(orderId, (note) => api.post(`/admin/orders/${orderId}/cancel`, { note }))
export const useOrderNote = (orderId) =>
  useOrderAction(orderId, (admin_note) => api.patch(`/admin/orders/${orderId}`, { admin_note }))

// ── catalogue ─────────────────────────────────────────────────────────────────

export function useAdminProducts(filters) {
  return useQuery({
    queryKey: adminKeys.products(filters),
    queryFn: () => api.get('/admin/products', { ...filters, limit: 100 }),
    placeholderData: (prev) => prev,
  })
}

export function useAdminProduct(id) {
  return useQuery({ queryKey: adminKeys.product(id), queryFn: () => api.get(`/admin/products/${id}`), enabled: Boolean(id) })
}

// Mutations that return the whole product: keep the editor in sync and make
// the shop catalogue reload.
export function useProductMutation(productId, fn) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (product) => {
      if (product?.id) qc.setQueryData(adminKeys.product(product.id), product)
      else qc.invalidateQueries({ queryKey: adminKeys.product(productId) })
      qc.invalidateQueries({ queryKey: ['admin', 'products'] })
      qc.invalidateQueries({ queryKey: adminKeys.dashboard })
      qc.invalidateQueries({ queryKey: ['products'] })
      qc.invalidateQueries({ queryKey: ['product'] })
    },
  })
}

export function useCategories() {
  return useQuery({ queryKey: adminKeys.categories, queryFn: () => api.get('/admin/categories') })
}

// ── generic list resources (categories, promo codes, cards) ──────────────────

export function useListMutation(key, fn, { refreshMeta = false } = {}) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key })
      if (refreshMeta) qc.invalidateQueries({ queryKey: ['meta'] })
    },
  })
}

export function usePromos() {
  return useQuery({ queryKey: adminKeys.promos, queryFn: () => api.get('/admin/promo-codes') })
}

export function useCards() {
  return useQuery({ queryKey: adminKeys.cards, queryFn: () => api.get('/admin/payment-cards') })
}

export function useSettings() {
  return useQuery({ queryKey: adminKeys.settings, queryFn: () => api.get('/admin/settings') })
}

export function useStaff() {
  return useQuery({ queryKey: adminKeys.staff, queryFn: () => api.get('/admin/staff') })
}

export function useCustomerSearch(q) {
  return useQuery({
    queryKey: adminKeys.customers(q),
    queryFn: () => api.get('/admin/customers', { q }),
    enabled: q.trim().length >= 2,
    placeholderData: (prev) => prev,
  })
}
