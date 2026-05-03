import { api } from './client'

export const paymentsApi = {
  uploadReceipt: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/payments/upload-receipt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  create: (data) => api.post('/payments', data),
}
