import { api } from './client'

export const ordersApi = {
  create: (data) => api.post('/orders', data),
  mine: () => api.get('/orders/mine'),
}
