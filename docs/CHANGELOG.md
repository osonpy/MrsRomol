# O'zgarishlar jurnali

Har bir bosqichdan keyin shu yerga nima qilingani, nima tuzatilgani va nima qoldirilgani yoziladi.
Reja: [SPEC.md](SPEC.md) → 9-bo'lim.

---

## 1-bosqich — Yangi baza (2026-10-14)

Eski Supabase loyihasiga ulanib bo'lmadi (manzil DNS'da yo'q, to'xtatilgan yoki o'chirilgan).
Kelishuvga ko'ra **yangi loyiha** uchun toza sxema yozildi, eski ma'lumot ko'chirilmaydi.

### Yangi: `db/schema.sql`
Bitta fayl, yangi Supabase loyihasining SQL Editor'ida bir marta ishga tushiriladi.

**Jadvallar** (SPEC 7-bo'lim):
`customers` (rollar bilan), `categories`, `products`, `product_variants` (rang × o'lcham, har birining qoldig'i alohida),
`product_images`, `favorites`, `promo_codes`, `promo_usages`, `payment_cards`, `orders`, `order_items`,
`order_status_history`, `payments`, `settings`.

Asosiy qarorlar:
- Pul butun so'mda (`bigint`), kasr xatolari bo'lmaydi.
- Buyurtmaning odam o'qiy oladigan raqami bor: **#1001, #1002…**
- `order_items` nom, rang, o'lcham va narxni **nusxalab** saqlaydi: keyin mahsulot o'zgarsa yoki o'chsa ham eski buyurtma to'g'ri ko'rinadi.
- Mahsulot nomi va tavsifi o'zbek + rus tilida. Rang ham ikki tilda, swatch uchun `color_hex` bor.
- O'lcham jadvali `products.size_chart` da (JSON, sm): "O'lchamimni aniqlash" shundan foydalanadi.
- Nom bo'yicha tez qidiruv uchun trigram indekslar (`pg_trgm`).
- Ulgurji narx va `seller` roli uchun joy qoldirilgan.

**Funksiyalar** — qoldiq, buyurtma va to'lov faqat shular orqali o'zgaradi (har biri bitta tranzaksiya, qatorlar qulflanadi):

| Funksiya | Nima qiladi |
|---|---|
| `create_order` | Narxni bazadan oladi, qoldiqni tekshiradi va **band qiladi**, promokodni qo'llaydi, 30 daqiqalik taymerni boshlaydi |
| `promo_discount` | Promokodni tekshiradi (muddat, limit, bir mijozga necha marta, minimal summa) va chegirmani hisoblaydi |
| `submit_payment` | Chek keldi → `payment_review`, taymer to'xtaydi; summa buyurtmadan olinadi |
| `review_payment` | Admin ✅ → `confirmed`; ❌ → `cancelled` + qoldiq qaytadi. Ikki admin bir vaqtda bossa, ikkinchisi `ALREADY_REVIEWED` oladi |
| `advance_order` | `confirmed → shipped` (trek raqami bilan) `→ delivered`, sakrab o'tib bo'lmaydi |
| `cancel_order` | Admin yoki mijoz bekor qiladi (mijoz faqat to'lovgacha) → qoldiq va promokod qaytadi |
| `expire_orders` | 30 daqiqada to'lanmaganlarni bekor qiladi (har daqiqa chaqiriladi, 2-bosqichda ulanadi) |

Har bir holat o'zgarishi `order_status_history` ga **kim va qachon** bilan yoziladi.

### Tuzatilgan muammolar (0-bosqichdan qolganlar)
| Muammo | Tuzatish |
|---|---|
| Qoldiq "o'qib-keyin-yozish" bilan kamayardi: bir vaqtda ikki xaridor oxirgi donani olishi mumkin edi | `create_order` qatorni qulflaydi (`FOR UPDATE`); test bilan isbotlangan |
| RLS `using (true)`: anon kalitli har kim hamma jadvalni o'qiy/yoza olardi | RLS yoqilgan, ruxsat qoidasi yo'q; `anon`/`authenticated` dan barcha huquqlar (jadvallar **va funksiyalar**) olingan. Faqat backend (secret kalit) ishlaydi |
| Cheklar ochiq bucket'da edi (shaxsiy ma'lumot) | `receipts` bucket **yopiq**; adminlar vaqtinchalik havola bilan ko'radi (2-bosqich) |
| Bitta buyurtmaga ikki faol to'lov | Bazada unique indeks: bitta buyurtmada faqat bitta kutilayotgan/tasdiqlangan to'lov |

### Testlar: `db/tests/run.sh`
Docker'da vaqtinchalik Postgres 15 ochiladi, sxema o'rnatiladi va **47 ta test** ishlaydi. Hammasi o'tdi:
- Narx bazadan olinishi, takror qatorlar qo'shilishi, qoldiq band qilinishi, promokod qoidalari (6 xil holat).
- To'lovning to'liq yo'li: chek → tasdiqlash → yuborildi → yetkazildi, tarix yozilishi.
- Rad etish, muddat o'tishi, mijoz bekor qilishi: qoldiq va promokod qaytishi.
- Ruxsatlar: `anon`/`authenticated` hech narsani o'qiy olmaydi va chaqira olmaydi.
- **Raqobat testi:** 1 dona qolgan mahsulotni ikki xaridor bir vaqtda oladi → bitta buyurtma, bitta `OUT_OF_STOCK`, qoldiq 0.

### O'chirildi
`supabase_schema.sql`, `migration_miniapp.sql`, `migration_miniapp_v2.sql`, `migration_product_images.sql`,
`clear_users_and_orders.sql`, `db_sxema_erd.html`. Ular eski sxemaga tegishli, git tarixida qoladi.

### Muhim: hozirgi holat
- **API va bot hali eski sxema bilan yozilgan**: yangi bazada ishlamaydi. 2-bosqichda yangi sxemaga o'tkaziladi.
- `.env` da `SUPABASE_KEY` endi **secret** kalit bo'lishi kerak (publishable/anon ishlamaydi).

### Egasi qilishi kerak
1. supabase.com → yangi loyiha (region: Frankfurt yoki eng yaqini).
2. SQL Editor → `db/schema.sql` → Run.
3. URL va **secret** kalitni yuboring yoki `.env` ga qo'ying.

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
