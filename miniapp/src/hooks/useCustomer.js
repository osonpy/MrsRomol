import { useUserStore } from '../store/userStore'
import { customersApi } from '../api/customers'

export function useCustomer() {
  const customer = useUserStore((s) => s.customer)
  const setCustomer = useUserStore((s) => s.setCustomer)

  const refresh = async () => {
    try {
      const updated = await customersApi.me()
      setCustomer(updated)
      return updated
    } catch {
      return null
    }
  }

  return { customer, refresh }
}
