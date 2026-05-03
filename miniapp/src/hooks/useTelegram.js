import { useEffect, useState } from 'react'

export function useTelegram() {
  const [tg] = useState(() => window.Telegram?.WebApp)

  useEffect(() => {
    if (!tg) return
    tg.ready()
    tg.expand()
    tg.setHeaderColor?.('#3E2723')
  }, [tg])

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    initData: tg?.initData,
    colorScheme: tg?.colorScheme ?? 'light',
    mainButton: tg?.MainButton,
    backButton: tg?.BackButton,
  }
}
