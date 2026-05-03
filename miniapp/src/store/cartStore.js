import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],

      addItem: (product, qty = 1) => {
        const items = get().items
        const existing = items.find((i) => i.product.id === product.id)
        if (existing) {
          set({
            items: items.map((i) =>
              i.product.id === product.id
                ? { ...i, qty: Math.min(i.qty + qty, product.stock_qty) }
                : i
            ),
          })
        } else {
          set({ items: [...items, { product, qty }] })
        }
      },

      removeItem: (productId) => {
        set({ items: get().items.filter((i) => i.product.id !== productId) })
      },

      updateQty: (productId, qty) => {
        if (qty <= 0) {
          get().removeItem(productId)
          return
        }
        set({
          items: get().items.map((i) =>
            i.product.id === productId ? { ...i, qty } : i
          ),
        })
      },

      clear: () => set({ items: [] }),

      total: () =>
        get().items.reduce(
          (sum, i) => sum + parseFloat(i.product.sell_price) * i.qty,
          0
        ),

      count: () => get().items.reduce((sum, i) => sum + i.qty, 0),
    }),
    { name: 'cart' }
  )
)
