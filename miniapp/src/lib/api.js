import { initData } from './telegram'

const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

// Errors from the API always look like { error, code, detail } (see api/errors.py).
export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error || `HTTP ${status}`)
    this.status = status
    this.code = body?.code || (status === 0 ? 'NETWORK_ERROR' : 'ERROR')
    this.detail = body?.detail || {}
  }
}

async function request(method, path, { body, query, form } = {}) {
  let url = BASE + path
  if (query) {
    const params = new URLSearchParams()
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') params.set(k, v)
    })
    const qs = params.toString()
    if (qs) url += `?${qs}`
  }

  const headers = { 'X-Telegram-Init-Data': initData }
  let payload
  if (form) {
    payload = form // browser sets the multipart boundary
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(url, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, null)
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

export const api = {
  get: (path, query) => request('GET', path, { query }),
  post: (path, body) => request('POST', path, { body }),
  patch: (path, body) => request('PATCH', path, { body }),
  put: (path, body) => request('PUT', path, { body }),
  delete: (path) => request('DELETE', path),
  upload: (path, form) => request('POST', path, { form }),
}
