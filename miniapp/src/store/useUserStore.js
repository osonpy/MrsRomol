// store/useUserStore.js — Zustand user/customer store
import { create } from 'zustand'

export const useUserStore = create((set, get) => ({
  customer: null,       // full customer object from DB
  telegramUser: null,   // Telegram WebApp user object
  isLoading: false,
  isRegistered: false,

  setTelegramUser: (user) => set({ telegramUser: user }),

  setCustomer: (customer) =>
    set({ customer, isRegistered: !!customer }),

  updateCustomer: (partial) =>
    set((state) => ({
      customer: state.customer ? { ...state.customer, ...partial } : partial,
    })),

  setLoading: (isLoading) => set({ isLoading }),

  // Helpers
  get telegramId() {
    return get().telegramUser?.id?.toString() ?? null
  },

  get language() {
    return get().customer?.language ?? get().telegramUser?.language_code ?? 'uz'
  },

  get isWholesale() {
    return get().customer?.is_wholesale ?? false
  },
}))
