# O'zgarishlar jurnali

Har bir bosqichdan keyin shu yerga nima qilingani, nima tuzatilgani va nima qoldirilgani yoziladi.
Reja: [SPEC.md](SPEC.md) → 9-bo'lim.

---

## 3-bosqich — Mini App: xaridor qismi (2026-10-14)

Mini App **noldan qayta yozildi** (eski kod butunlay olib tashlandi). Brend nomi kelishuvga ko'ra **Mrs Romol**.

### Dizayn
- **Ranglar** logotipdan olindi (`brand/MrsRomol.png`): krem fon `#FAF9F5`, rose-gold `#986456` (asosiy), `#C29786`, `#E4B4A0` va pushti `#EED3C8`. Matn va tugmalar kontrasti WCAG AA talabiga javob beradi.
- **Shriftlar:** sarlavhalar uchun Cormorant Garamond (logotipga mos nafis serif), matn uchun Manrope. Ikkalasi lotin, o'zbek va kirill harflarini qo'llab-quvvatlaydi. Shriftlar ilova bilan birga yuklanadi, tashqi xizmatga bog'liq emas.
- **Logotip:** `brand/make_assets.py` skripti asl logotipdan fonsiz versiya, sarlavha logotipi (53 KB), 512px ikonka va favicon yasaydi. AI generator qoldirgan ✦ belgisi olib tashlangan.
- **Telegram bilan integratsiya:**
  - Sarlavha va fon ranglari ilovaga moslanadi.
  - Telegram'ning "Orqaga" tugmasi ishlaydi.
  - Bosganda tebranish (haptic) bor.
  - Pastga surilganda ilova yopilib ketmaydi.
  - Telefon raqamini bir bosishda olish va joylashuvni yuborish mumkin.
  - Bildirishnomadagi tugma kerakli buyurtmani to'g'ridan-to'g'ri ochadi (`startapp`).

### Sahifalar
| Sahifa | Imkoniyatlar |
|---|---|
| **Katalog** | Logotip, qidiruv (yozib bo'lgach avtomatik), kategoriyalar, filtr (saralash, o'lcham, narx), cheksiz aylantirish, "Yangi" va "Tugagan" belgilari, rang nuqtalari. Filtrlar manzilda saqlanadi, mahsulotdan qaytilganda ro'yxat joyida qoladi |
| **Mahsulot** | Surib ko'riladigan galereya va to'liq ekran; rang tanlanganda o'sha rang rasmi chiqadi; tugagan o'lchamlar o'chirilgan ko'rinadi; "Kam qoldi" belgisi; o'lchamlar jadvali; **"O'lchamimni aniqlash"** (o'lchovlar kiritiladi, mos o'lcham tavsiya qilinadi va bir bosishda tanlanadi); "qaytarilmaydi" ogohlantirishi |
| **Savat** | Narxlar serverdan qayta hisoblanadi; "Faqat N dona qoldi" ogohlantirishi va "N taga o'zgartirish" tugmasi; sotuvdan olingan mahsulot belgilanadi; promokod; yetkazish narxi alohida ekani eslatiladi |
| **Rasmiylashtirish** | Ism va telefon (Telegram'dan olish mumkin); viloyat (Toshkent bo'lsa taksi, viloyatlarga pochta yoki BTS avtomatik); manzil; joylashuv; izoh; ikki rozilik ("yetkazishni o'zim to'layman", "qaytarilmaydi"); 30 daqiqalik bron haqida eslatma. Oxirgi manzil keyingi xaridda avtomatik to'ldiriladi |
| **Buyurtma** | 5 bosqichli holat chizig'i; to'lov taymeri; summani va karta raqamini bir bosishda nusxalash; karta tanlash; chek rasmini oldindan ko'rish va yuborish; trek raqami; bekor qilish |
| **Buyurtmalarim, Sevimlilar, Profil** | Profilda til (o'zbekcha yoki ruscha, saqlanadi), yangi mahsulot xabarlariga obuna, qoidalar, admin uchun "Admin panel" kirish joyi (panelning o'zi 4-bosqichda) |

Har bir sahifada yuklanish (skeleton), bo'sh holat va xato holati (qayta urinish tugmasi bilan) bor. API xato kodlari foydalanuvchiga tushunarli tilda ko'rsatiladi.

### Brauzerdagi to'liq test (yangi)
- `e2e/demo_stack.sh` namunaviy do'kon ko'taradi: 4 kategoriya, 6 mahsulot, ranglar, o'lchamlar, rasmlar, kartalar va promokod.
- `e2e/walk.mjs` headless Chrome'da (telefon o'lchamida) xaridor yo'lini boshdan-oxir o'tadi: katalog → mahsulot → o'lcham yordamchisi → savat → promokod → rasmiylashtirish → buyurtma → chek yuklash → buyurtmalar → sevimlilar → profil → rus tili → qidiruv. Har bir qadamni skrinshot qiladi va konsol yoki tarmoq xatolarini tekshiradi.
- Natija: **17 ta qadam, muammo topilmadi.** Skrinshotlar ko'z bilan ham tekshirildi.

### Testlar paytida topilgan va tuzatilgan muammolar
| Muammo | Tuzatish |
|---|---|
| Filtr oynasidagi `useEffect` noto'g'ri qiymat qaytarib, katalogni buzardi | Tuzatildi; boshqa joylarda bunday holat qolmaganini tekshirdim |
| Saqlangan til ruscha bo'lsa ham pastki menyu o'zbekcha qolardi (birinchi til o'zgarishi yo'qolardi) | Profil tili sahifalar chizilishidan oldin o'rnatiladi. Brauzerda tekshirildi |
| "Buyurtma #1001" "#IOOI" bo'lib o'qilardi (serif shriftning eski uslubdagi raqamlari) | Raqamlar oddiy shriftda ko'rsatiladi |
| Yangi buyurtmadan keyin hech bir to'lov kartasi tanlanmagan bo'lardi | Kartalar buyurtma javobiga qo'shildi, birinchi karta avtomatik tanlanadi |
| Storage xatosi ishlov berilmagan 500'ga aylanardi; 500 javobida CORS sarlavhasi yo'qligi uchun ilova "internet yo'q" deb ko'rsatardi | Storage xatosi aniq `STORAGE_ERROR` (502) qaytaradi; oxirgi chiziqdagi xato ishlovchi CORS ichiga ko'chirildi. 2 ta yangi API testi qo'shildi |
| **ESLint 0-bosqichdan beri ishlamagan** (konfiguratsiya o'rnatilgan plagin versiyasiga mos emas edi). 0-bosqichda "lint xatosiz" deb yozganim noto'g'ri edi: chiqishni filtrlaganim uchun xato ko'rinmay qolgan | Konfiguratsiya tuzatildi, lint endi haqiqatan ishlaydi va toza |

### Boshqa
- Eski "Misr Romol" nomi hamma joyda **Mrs Romol** ga almashtirildi (bot salomlashuvi, API, hujjatlar).
- `axios` va `@twa-dev/sdk` olib tashlandi. TanStack Query va shriftlar qo'shildi.

### Tekshiruv
- API 26/26 (avval 24 edi, xato holatlari uchun 2 ta test qo'shildi), baza 47/47.
- Mini App: build va lint toza; asosiy JS 116 KB (gzip), sahifalar alohida yuklanadi.
- Brauzer testi: 17 qadam, muammo yo'q.

### Hozirgi holat
- Admin panel kirish joyi bor, lekin panelning o'zi hali yo'q, u **4-bosqich**da quriladi. Hozircha mahsulot qo'shish uchun API kerak (yoki 4-bosqichni kutish).
- Mini App hali internetga chiqarilmagan (deploy 6-bosqichda).

---

## 2-bosqich — Yangi API (2026-10-14)

API yangi bazaga moslab qayta yozildi. Eski endpointlar o'chirildi, chunki eski Mini App 3-bosqichda yangisi bilan almashtiriladi.

### Endpointlar

**Xaridor** (Telegram `initData` bilan, birinchi kirishda mijoz avtomatik yaratiladi):

| Endpoint | Vazifa |
|---|---|
| `GET /meta` | Ilova ochilganda kerak bo'ladigan hamma narsa: profil, kategoriyalar, hududlar, yetkazish usullari, bron muddati, qoidalar |
| `GET/PATCH /me` | Profil: ism, telefon, til, yangi mahsulot xabarlariga obuna |
| `GET /products` | Katalog: qidiruv, kategoriya, narx oralig'i, o'lcham, rang, saralash, sahifalash |
| `GET /products/{id}` | Mahsulot: rasmlar, variantlar, o'lcham jadvali |
| `GET/PUT/DELETE /favorites` | Sevimlilar |
| `POST /cart/quote` | Savat hisobi: joriy narxlar, qoldiq muammolari, promokod tekshiruvi |
| `POST /orders`, `GET /orders`, `GET /orders/{id}` | Buyurtma berish va ko'rish |
| `POST /orders/{id}/cancel` | To'lovgacha bekor qilish |
| `GET /payment-cards`, `POST /orders/{id}/payment` | Karta tanlash va chek yuklash |

**Admin** (`admin` yoki `super_admin` roli):

| Endpoint | Vazifa |
|---|---|
| `GET /admin/dashboard` | Bugungi buyurtmalar va tushum, tekshirilishi kerak bo'lgan to'lovlar, yuborilishi kerak bo'lgan buyurtmalar, tugayotgan mahsulotlar |
| `/admin/orders` | Ro'yxat (holat filtri, raqam yoki telefon bo'yicha qidiruv), batafsil ko'rinish (chek havolasi bilan), izoh |
| `POST /admin/payments/{id}/review` | To'lovni tasdiqlash yoki rad etish (rad etishda sabab majburiy) |
| `POST /admin/orders/{id}/advance` | Yuborildi (trek raqami bilan) va yetkazildi |
| `POST /admin/orders/{id}/cancel` | Bekor qilish |
| `/admin/categories`, `/admin/products`, `/admin/variants`, `/admin/images` | Katalogni to'liq boshqarish, 5 tagacha rasm, tartibini o'zgartirish |
| `/admin/promo-codes` | Promokodlar |
| `/admin/payment-cards`, `/admin/settings`, `/admin/staff` | **Faqat super admin**: kartalar, sozlamalar, adminlarni tayinlash |

### Asosiy o'zgarishlar
- **Rollar:** do'kon egasi `.env` dagi `SUPER_ADMIN_IDS` orqali aniqlanadi. Boshqa adminlarni super admin tayinlaydi. Admin API endi Telegram orqali shaxsga bog'langan, shuning uchun har bir harakat kim qilgani bilan yoziladi. Eski umumiy `ADMIN_SECRET_KEY` kerak emas, olib tashlandi.
- **Async baza klienti:** 0-bosqichdan qolgan muammo hal qilindi, endi baza so'rovlari serverni bloklamaydi.
- **Bazadagi funksiyalar:** buyurtma, to'lov va bekor qilish 1-bosqichdagi atomar funksiyalar orqali ishlaydi. API ularning xato kodlarini (`OUT_OF_STOCK`, `ALREADY_REVIEWED`…) aniq HTTP javobga aylantiradi.
- **Muddati o'tgan buyurtmalar** har daqiqada avtomatik bekor qilinadi va mijozga xabar boradi.
- **Mahsulot rasmlari** yuklanganda WebP formatiga o'tkaziladi va ikki o'lchamda saqlanadi: 1600px (mahsulot sahifasi) va 600px (katalog). EXIF ma'lumotlari, jumladan GPS joylashuvi, olib tashlanadi. Rasmlar 1 yil keshlanadi.
- **Cheklar** yopiq bucket'da saqlanadi. Admin faqat 1 soatlik vaqtinchalik havola bilan ko'radi. Fayl turi ichidagi baytlar bo'yicha ham tekshiriladi.
- **Xabarnomalar** o'zbek va rus tilida, har bir holat o'zgarishida yuboriladi. Xabarda "Buyurtmani ko'rish" tugmasi bor. Guruh chatlarida Mini App havolasi ishlatiladi (`MINI_APP_LINK`), chunki Telegram guruhlarda `web_app` tugmasiga ruxsat bermaydi.
- **Mijozga** aniq qoldiq va tannarx ko'rsatilmaydi, faqat "bor" va "kam qoldi" belgilari.
- **Validatsiya:** hudud va yetkazish usuli mosligi tekshiriladi (Toshkent shahri uchun taksi, viloyatlar uchun pochta yoki BTS). Telefon, karta raqami va promokod formatlari ham tekshiriladi.

### Testlar paytida topilgan va tuzatilgan muammolar
| Muammo | Tuzatish |
|---|---|
| "romol" deb qidirilsa "Ro'mol" topilmasdi (o'zbekcha tutuq belgisi `'`, `‘`, `ʻ`, `` ` ``) | Bazada `search_text` ustuni (kichik harf, tutuq belgisiz) + trigram indeks. Endi barcha yozilish shakllari topiladi |
| Telefon bo'shliqlar bilan saqlanardi: admin `12345` deb qidirsa topilmasdi | Telefon bitta formatda saqlanadi: `+998901234567` (9 xonali raqamga `+998` avtomatik qo'shiladi) |
| Kichik rasm (thumbnail) keshlanmasdi | Sabab: `storage3` kutubxonasi berilgan sozlamani o'zgartirib yuborardi. Har bir yuklashga alohida sozlama beriladi. Haqiqiy Supabase'da tekshirildi |

### Bot
- Botning admin qismi (`/pending`, `/setphotos`, tasdiqlash tugmalari) **olib tashlandi**, chunki u eski sxema bilan ishlardi va yangi bazada xato berardi. Admin ishlari endi Mini App'da bajariladi, botdagi tezkor tugmalar esa 5-bosqichda yangidan qo'shiladi.
- `/start` va Mini App tugmasi ishlaydi.

### Testlar
- **`tests/run.sh`**: Docker'da Postgres va PostgREST (Supabase ichidagi REST qatlami) ko'tariladi, API'ga **24 ta boshdan-oxir test** yuboriladi. Hammasi o'tdi:
  - Rollar va ruxsatlar.
  - Katalog va filtrlar (6 xil yozilishdagi qidiruv).
  - Rasm yuklash va WebP.
  - Savat va promokod.
  - Buyurtma, chek, tasdiqlash, yuborish, yetkazish.
  - Ikki marta tasdiqlashni bloklash.
  - Muddat o'tishi va qoldiq qaytishi.
  - Rad etish.
  - Begona buyurtmani ko'ra olmaslik.
  - Mahsulot o'chirilsa ham eski buyurtma saqlanishi.
- **Haqiqiy Supabase Storage**: rasm yuklash, ochiq havola, keshlash, chekning faqat vaqtinchalik havola bilan ochilishi tekshirildi. Test fayllari o'chirildi.
- `db/tests/run.sh`: 47 ta baza testi `search_text` qo'shilgandan keyin ham o'tdi.
- Docker image Pillow (WebP) bilan yig'iladi.

### Muhim: hozirgi holat
- **Eski Mini App yangi API bilan ishlamaydi.** 3-bosqichda yangisi quriladi.

### Egasi qilishi kerak
1. Supabase → SQL Editor → `db/migrations/002_product_search_text.sql` → Run.
2. `.env` ga `SUPER_ADMIN_IDS=<sizning Telegram ID>` qo'shing, aks holda admin bo'limiga hech kim kira olmaydi.
3. `.env` dagi `ADMIN_SECRET_KEY`, `INTERNAL_SECRET`, `ADMIN_USER_IDS`, `PAYMENT_CARD`, `RECEIPTS_BUCKET` endi ishlatilmaydi, ularni o'chirsa bo'ladi.

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
