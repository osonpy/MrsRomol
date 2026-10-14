import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// The cart lives on the device. Prices shown here are a snapshot for instant
// rendering; the cart page always re-prices through POST /cart/quote.
export const useCart = create(
  persist(
    (set, get) => ({
      items: [], // [{ variant_id, product_id, quantity, name_uz, name_ru, color_uz, color_ru, size, price, image }]
      promoCode: '',

      add(line, quantity = 1) {
        const items = get().items
        const existing = items.find((i) => i.variant_id === line.variant_id)
        set({
          items: existing
            ? items.map((i) =>
                i.variant_id === line.variant_id ? { ...i, quantity: Math.min(i.quantity + quantity, 100) } : i,
              )
            : [...items, { ...line, quantity }],
        })
      },
      setQuantity(variantId, quantity) {
        set({
          items: get()
            .items.map((i) => (i.variant_id === variantId ? { ...i, quantity } : i))
            .filter((i) => i.quantity > 0),
        })
      },
      remove(variantId) {
        set({ items: get().items.filter((i) => i.variant_id !== variantId) })
      },
      setPromo(promoCode) {
        set({ promoCode })
      },
      clear() {
        set({ items: [], promoCode: '' })
      },
    }),
    { name: 'mrs-romol-cart', version: 1 },
  ),
)

export const useCartCount = () => useCart((s) => s.items.reduce((n, i) => n + i.quantity, 0))
