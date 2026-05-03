// store/useCartStore.js — Zustand cart store with localStorage persistence
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [], // [{ product, quantity, selectedColor }]

      addItem: (product, quantity = 1, selectedColor = null) => {
        const items = get().items
        const existing = items.find(
          (i) =>
            i.product.id === product.id &&
            i.selectedColor === selectedColor
        )
        if (existing) {
          // Increase quantity, respect stock limit
          const newQty = Math.min(
            existing.quantity + quantity,
            product.stock_qty
          )
          set({
            items: items.map((i) =>
              i === existing ? { ...i, quantity: newQty } : i
            ),
          })
        } else {
          set({ items: [...items, { product, quantity, selectedColor }] })
        }
      },

      removeItem: (productId, selectedColor = null) => {
        set({
          items: get().items.filter(
            (i) =>
              !(i.product.id === productId && i.selectedColor === selectedColor)
          ),
        })
      },

      updateQuantity: (productId, quantity, selectedColor = null) => {
        if (quantity <= 0) {
          get().removeItem(productId, selectedColor)
          return
        }
        set({
          items: get().items.map((i) =>
            i.product.id === productId && i.selectedColor === selectedColor
              ? { ...i, quantity }
              : i
          ),
        })
      },

      clearCart: () => set({ items: [] }),

      // Computed
      get totalItems() {
        return get().items.reduce((sum, i) => sum + i.quantity, 0)
      },

      get totalAmount() {
        return get().items.reduce(
          (sum, i) =>
            sum + parseFloat(i.product.sell_price) * i.quantity,
          0
        )
      },
    }),
    {
      name: 'misr-romol-cart',
      version: 1,
    }
  )
)
