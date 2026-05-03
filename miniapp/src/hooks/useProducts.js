import { useState, useEffect, useCallback } from 'react'
import { productsApi } from '../api/products'

export function useProducts() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProducts = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    productsApi
      .list()
      .then((data) => {
        if (!cancelled) setProducts(data.products ?? data ?? [])
      })
      .catch((err) => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const cancel = fetchProducts()
    return cancel
  }, [fetchProducts])

  return { products, loading, error, refetch: fetchProducts }
}
