import { api } from './client'

export const productsApi = {
  list: () => api.get('/products'),
  get: (id) => api.get(`/products/${id}`),
  imageUrl: (productId, sortOrder = 0) =>
    `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/products/${productId}/image/${sortOrder}`,
}
