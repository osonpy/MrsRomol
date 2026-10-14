import { create } from 'zustand'
import { errorText } from '../i18n'

// Global toast: toast.show('Saved') / toast.error(apiError). Rendered by <Toaster />.
export const useToastStore = create((set) => {
  let timer
  return {
    message: null,
    tone: 'default',
    show: (message, tone = 'default') => {
      set({ message, tone })
      clearTimeout(timer)
      timer = setTimeout(() => set({ message: null }), 2600)
    },
  }
})

export const toast = {
  show: (msg) => useToastStore.getState().show(msg),
  error: (err) => useToastStore.getState().show(typeof err === 'string' ? err : errorText(err), 'error'),
}
