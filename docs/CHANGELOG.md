# O'zgarishlar jurnali

Har bir bosqichdan keyin shu yerga nima qilingani, nima tuzatilgani va nima qoldirilgani yoziladi.
Reja: [SPEC.md](SPEC.md) → 9-bo'lim.

---

## 0-bosqich — Tozalash va xavfsizlik (2026-10-14)

### Xavfsizlik tuzatishlari

| # | Muammo | Xavfi | Tuzatish |
|---|---|---|---|
| 1 | Botdagi admin tugmalari (to'lov/buyurtma tasdiqlash, rasm o'chirish) admin tekshiruvisiz edi | **Jiddiy**: callback ma'lumotini soxtalashtirgan har qanday foydalanuvchi o'z to'lovini "tasdiqlay" olardi | `bot/handlers/admin.py` routeriga to'liq `IsAdmin` filtri (xabarlar + callbacklar) |
| 2 | Buyurtmada miqdor tekshirilmasdi | Manfiy miqdor → manfiy summa va ombor **ko'payishi** | `quantity` 1–100, 1–50 qator; bir xil mahsulot qatorlari qo'shilib tekshiriladi |
| 3 | To'lov summasi mijozdan olinardi | Mijoz istalgan summani yozishi mumkin edi | Summa buyurtmadan olinadi; ikkinchi to'lov taqiqlangan; chek URL faqat bizning bucketdan |
| 4 | `ADMIN_SECRET_KEY` standart qiymati `"change-me"` | Admin API'ni taxmin bilan ochish | Kalit majburiy, ≥32 belgi; `hmac.compare_digest` bilan solishtirish |
| 5 | Telegram `initData` muddati tekshirilmasdi | O'g'irlangan imzo abadiy ishlardi | `auth_date` 24 soatdan eski bo'lsa rad etiladi (`INIT_DATA_MAX_AGE`) |
| 6 | Admin xabarlarida mijoz matni ekranlanmasdi | Ism/manzil orqali HTML kiritish, xabar buzilishi | `html.escape` (API va bot) |
| 7 | Chek fayli mijoz bergan nom bilan saqlanardi | Yo'l manipulyatsiyasi, URL'ni taxmin qilish | Tasodifiy UUID nom, `YYYYMMDD/` papka |
| 8 | DB xato matni mijozga qaytarilardi | Ichki tuzilma oshkor bo'lishi | Umumiy xabar + 500 |
| 9 | `/docs` production'da ochiq | API xaritasi oshkor | Faqat `DEV_MODE=true` da |
| 10 | Mijoz tili va ism uzunligi tekshirilmasdi | Noto'g'ri ma'lumot | `uz/ru/en`, uzunlik chegaralari |

### Mantiqiy tuzatishlar
- To'lov holati nomlari bir xil qilindi: API `confirmed` deb yozardi, bot va Mini App esa boshqacha nom ishlatardi. Endi hamma joyda `verified`.
- Botda to'lov tasdiqlanganda buyurtma `shipped` emas, **`confirmed`** holatiga o'tadi (SPEC bo'yicha).

### O'chirilgan eski kod (git tarixida saqlanadi)
- Bot: `handlers/{catalog,orders,payments,my_orders}.py`, `keyboards/{catalog,orders}.py`, `utils/cache.py`. Ularning o'rnini Mini App egallagan. `bot/database.py` dan ishlatilmaydigan funksiyalar olib tashlandi.
- API: `utils/notifications.py`, `utils/telegram.py`, `models/` (takror va ishlatilmagan).
- Mini App: 13 ta ishlatilmagan fayl (takror store, i18n, komponentlar, rasmlar).
- Railway `Procfile`, `Procfile.bot`. `PAYMENT_CARD` o'zgaruvchisi olib tashlandi, kartalar 1-bosqichda bazaga o'tadi.

### Yangi
- `Dockerfile`, `docker-compose.yml`, `deploy/Caddyfile`, `deploy/Caddy.Dockerfile`: VPS'da `docker compose up -d --build` bilan API, bot va Caddy (avtomatik HTTPS) ishga tushadi.
- `README.md`: ishga tushirish va deploy yo'riqnomasi.
- Python bog'liqliklari `pyproject.toml` ga birlashtirildi (`uv.lock`); `requirements.txt` lock'dan yaratiladi.

### Tuzatilgan oldingi muammo
- `miniapp/package-lock.json` `package.json` ga mos emas edi (lock'da React 19/Vite 8, `i18next` yo'q), shuning uchun Mini App toza holatdan build bo'lmasdi. Lock qayta yaratildi.

### Tekshiruv
- API: 14 ta xavfsizlik testi (auth, validatsiya, to'lov qoidalari) o'tdi.
- Bot: admin filtri (admin o'tadi, begona bloklanadi) o'tdi.
- Mini App: `npm run build` va `eslint` xatosiz.
- Docker: 3 ta image build bo'ldi, importlar ishlaydi.

### Keyingi bosqichga qoldirildi
- Ombor qoldig'ini **atomar** kamaytirish (hozir bir vaqtda kelgan ikki buyurtma oxirgi donani olishi mumkin) → 1-bosqich, Postgres funksiyasi.
- Supabase RLS `using (true)` qoidalari → 1-bosqich.
- Cheklar uchun yopiq bucket + vaqtinchalik havolalar → 1-bosqich.
- Supabase Python klienti sinxron (event loop'ni bloklaydi) → 2-bosqich.

### Deploy uchun eslatma
`.env` da `ADMIN_SECRET_KEY` ni yangilang, aks holda API ishga tushmaydi:
`python -c "import secrets; print(secrets.token_urlsafe(32))"`
