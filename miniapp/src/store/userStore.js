import { create } from 'zustand'

export const useUserStore = create((set, get) => ({
  customer: null,
  telegramUser: null,
  isLoading: false,

  setTelegramUser: (user) => set({ telegramUser: user }),

  setCustomer: (customer) => set({ customer }),

  updateCustomer: (partial) =>
    set((state) => ({
      customer: state.customer ? { ...state.customer, ...partial } : partial,
    })),

  setLoading: (isLoading) => set({ isLoading }),
}))
