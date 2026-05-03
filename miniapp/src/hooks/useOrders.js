import { useState, useEffect, useCallback } from 'react'
import { ordersApi } from '../api/orders'

export function useOrders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchOrders = useCallback(() => {
    setLoading(true)
    setError(null)
    ordersApi
      .mine()
      .then((data) => setOrders(data.orders ?? data ?? []))
      .catch((err) => setError(err))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchOrders()
  }, [fetchOrders])

  return { orders, loading, error, refetch: fetchOrders }
}
