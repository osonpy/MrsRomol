import axios from 'axios'

const tg = window.Telegram?.WebApp

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  if (tg?.initData) {
    config.headers['X-Telegram-Init-Data'] = tg.initData
  }
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err.response?.data ?? { error: 'Network error', code: 'NETWORK_ERROR' })
)
