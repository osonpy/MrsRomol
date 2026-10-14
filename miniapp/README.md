# Mrs Romol — Mini App

Telegram Mini App: React 18 + Vite + Tailwind, TanStack Query, Zustand, i18next (uz/ru).

| Papka | Nima |
|---|---|
| `src/pages/` | Sahifalar: katalog, mahsulot, savat, rasmiylashtirish, buyurtma(lar), sevimlilar, profil |
| `src/components/` | Umumiy UI: tugma, sheet, toast, mahsulot kartochkasi, buyurtma holati |
| `src/hooks/queries.js` | API so'rovlari (TanStack Query) |
| `src/lib/` | Telegram SDK, API klient, formatlash, o'lcham tavsiyasi |
| `src/store/cart.js` | Savat (qurilmada saqlanadi) |
| `src/i18n/` | Tarjimalar |
| `tailwind.config.js` | Brend ranglari va shriftlar |

```bash
npm install
VITE_API_URL=http://localhost:8000 npm run dev   # brauzerda: API DEV_MODE=true bo'lishi kerak
npm run build && npm run lint
```

Logotip va ikonkalar `brand/make_assets.py` bilan yasaladi.
