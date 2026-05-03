import { api } from './client'

export const customersApi = {
  register: (data) => api.post('/customers/register', data),
  me: () => api.get('/customers/me'),
  updateMe: (data) => api.patch('/customers/me', data),
}
