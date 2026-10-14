# Mrs Romol — Texnik topshiriq (v1)

> Holat: **qoralama, tasdiqlash kutilmoqda** · Sana: 2026-10-14

## 1. Maqsad

Telegram Mini App orqali ishlaydigan zamonaviy, qulay onlayn do'kon. Mahsulotlar: ro'mol, sharf,
kiyim (o'lcham bilan), abaya ichidan kiyiladigan ishton, ro'mol ichidan kiyiladigan shapka va h.k.

Keyingi bosqichlarda (v1 ga kirmaydi): brauzer uchun veb-do'kon, ulgurji narxlar, sotuvchi roli,
Click/Payme.

## 2. Asosiy qarorlar

| Mavzu | Qaror |
|---|---|
| Kod | Backend (FastAPI + bot) saqlanadi va tuzatiladi; Mini App UI noldan qayta quriladi |
| Baza | Supabase (bepul tarif): PostgreSQL + Storage (rasmlar) |
| Server | Contabo VPS: Docker Compose + Caddy (avtomatik HTTPS) |
| Domen | Sotib olinadi. `app.<domen>` — Mini App, `api.<domen>` — API, `<domen>` — keyin veb-do'kon |
| Mijozlar | Hozircha faqat chakana (bitta narx). Ulgurji uchun joy qoldiriladi |
| Tillar | O'zbek (asosiy) + Rus |
| Dizayn | Nafis, och rangli; brend logotipi va ranglari asosida |
| To'lov | Faqat oldindan, kartaga o'tkazma + chek rasmi. Bir nechta karta |
| Yetkazish | Faqat yetkazib berish, narxini mijoz o'zi to'laydi. Toshkent — taksi; viloyatlar — pochta/BTS |
| Qaytarish | Yo'q. Buyurtmadan oldin aniq ko'rsatiladi; o'rniga aniq o'lcham tanlash yordamchisi |
| Admin | Mini App ichida admin bo'limi |

## 3. Rollar

| Rol | Kim | Huquqlar |
|---|---|---|
| `super_admin` | Egasi | Hammasi + adminlarni, kartalarni, sozlamalarni boshqarish |
| `admin` | Ayoli | Mahsulot, buyurtma, to'lov, promokod, xabar yuborish |
| `customer` | Xaridor | Xarid qilish |
| `seller` | (keyin) | Faqat buyurtmalarni ko'rish/yuritish — tizim rol qo'shishga tayyor bo'ladi |

Har bir admin harakati (to'lovni tasdiqlash, holat o'zgartirish) **kim qilgani** bilan yoziladi.

## 4. Xaridor funksiyalari (Mini App)

1. **Bosh sahifa / Katalog** — banner, kategoriyalar, yangi mahsulotlar, mahsulotlar to'ri.
2. **Qidiruv + filtr** — nom bo'yicha qidiruv; kategoriya, narx oralig'i, o'lcham, rang bo'yicha filtr; saralash (yangi, arzon, qimmat).
3. **Mahsulot sahifasi**
   - 5 tagacha rasm, surib ko'rish, kattalashtirish; rang tanlanganda o'sha rang rasmi.
   - Rang va o'lcham tanlash; tugagan variant o'chirilgan holda ko'rinadi.
   - **O'lcham jadvali** (ko'krak aylanasi, bel, uzunlik va h.k.).
   - **"O'lchamimni aniqlash"** — mijoz o'z o'lchamlarini kiritadi → mos o'lcham tavsiya qilinadi.
   - "Qaytarib bo'lmaydi" ogohlantirishi.
4. **Sevimlilar** (yurakcha).
5. **Savat** — miqdorni o'zgartirish, promokod kiritish, jami summa.
6. **Rasmiylashtirish**
   - Ism, telefon (Telegram orqali bir tugma bilan ulashish).
   - Hudud: Toshkent shahri → taksi; viloyat + tuman → pochta/BTS.
   - Manzil matni + xaritada nuqta (Toshkent uchun).
   - Izoh. "Yetkazish narxini o'zingiz to'laysiz" va "qaytarilmaydi" roziligi.
7. **To'lov** — kartalardan birini tanlash, raqamni nusxalash, chek rasmini yuklash.
   30 daqiqalik **taymer** ko'rinadi.
8. **Buyurtmalarim** — holat chizig'i (timeline), trek raqami, qayta buyurtma.
9. **Profil** — ism, telefon, til, yangi mahsulot xabarlariga obuna.

## 5. Admin funksiyalari (Mini App ichida)

1. **Panel** — bugungi buyurtmalar, tekshirilishi kerak bo'lgan to'lovlar, tugayotgan mahsulotlar.
2. **Mahsulotlar** — qo'shish/tahrirlash/yashirish; rasmlar (yuklashda avtomatik siqiladi → WebP);
   variantlar (rang × o'lcham) va har birining qoldig'i; o'lcham jadvali; kategoriya.
3. **Buyurtmalar** — ro'yxat va filtr (holat bo'yicha); chekni ko'rish; tasdiqlash/rad etish;
   "Yuborildi" (trek raqami yoki taksi izohi); "Yetkazildi"; bekor qilish.
4. **Promokodlar** — foiz yoki summa; muddat; foydalanish limiti; minimal buyurtma summasi.
5. **Xabar yuborish** — yangi mahsulot haqida obunachilarga (rasm + tugma bilan).
6. **Sozlamalar** (`super_admin`) — to'lov kartalari, adminlar ro'yxati, bron muddati, qoidalar matni.

Bot ham parallel xabar beradi: yangi buyurtma / yangi chek → admin(lar)ga, tugmalar bilan tezkor tasdiqlash.

## 6. Buyurtma hayot sikli

```
awaiting_payment ──(chek yuklandi)──► payment_review ──(admin ✅)──► confirmed
       │                                    │                          │
  (30 daq. o'tdi)                      (admin ❌)                 (yuborildi)
       ▼                                    ▼                          ▼
   cancelled                            cancelled                   shipped ──► delivered
```

| Holat | Ma'nosi | Mijozga xabar |
|---|---|---|
| `awaiting_payment` | Yaratildi, qoldiq **band qilindi**, 30 daqiqa taymer | ✅ to'lov ma'lumotlari |
| `payment_review` | Chek yuklandi, admin tekshiradi (taymer to'xtaydi) | ✅ |
| `confirmed` | To'lov tasdiqlandi, tayyorlanmoqda | ✅ |
| `shipped` | Yuborildi (trek raqami / izoh) | ✅ |
| `delivered` | Yetkazildi | ✅ |
| `cancelled` | Muddat o'tdi / rad etildi / qo'lda — qoldiq qaytariladi | ✅ sababi bilan |

Muddat o'tgan bronlar har daqiqada avtomatik bekor qilinadi. Qoldiqni band qilish va qaytarish
bazada **atomar** (bitta tranzaksiya) bajariladi — oxirgi donani ikki kishi ololmaydi.

## 7. Ma'lumotlar modeli (asosiy jadvallar)

- `customers` — telegram_id, ism, telefon, til, **role**, obuna, is_wholesale (keyin uchun)
- `categories` — nom (uz/ru), tartib
- `products` — nom/tavsif (uz/ru), kategoriya, asosiy narx, aktiv, o'lcham jadvali (JSON)
- `product_variants` — mahsulot, rang, o'lcham, SKU, **qoldiq**, **band qilingan**, narx (ixtiyoriy)
- `product_images` — mahsulot, rang (ixtiyoriy), URL, tartib (≤5)
- `favorites` — mijoz × mahsulot
- `promo_codes`, `promo_usages`
- `orders` — mijoz, holat, hudud/tuman, manzil, lokatsiya, yetkazish usuli, trek raqami,
  summa, chegirma, promokod, **expires_at**
- `order_items` — variant, nom/rang/o'lcham/narx **nusxasi** (keyin narx o'zgarsa ham saqlanadi)
- `order_status_history` — holat, kim o'zgartirdi, qachon, izoh
- `payment_cards` — raqam, egasi, turi (Uzcard/Humo), aktiv
- `payments` — buyurtma, karta, chek URL, summa, holat, tekshirgan admin
- `settings` — bron muddati, qoidalar matni va h.k.

Narxlar har doim **serverda** hisoblanadi (mijoz yuborgan summa ishlatilmaydi).

## 8. Texnologiyalar

| Qism | Texnologiya |
|---|---|
| Mini App | React 18, Vite, Tailwind, Zustand, TanStack Query, i18next, Telegram WebApp SDK |
| API | FastAPI, Pydantic v2, Supabase (Postgres funksiyalari — atomar amallar uchun) |
| Bot | aiogram 3 — xabarnomalar, tezkor admin tugmalari, /start |
| Deploy | Docker Compose (api, bot, caddy) VPS'da; Mini App statik build Caddy orqali |

## 9. Bosqichlar

| # | Bosqich | Natija |
|---|---|---|
| 0 | Tozalash | Eski/takror kod olib tashlanadi, xavfsizlik xatolari tuzatiladi, Docker |
| 1 | Baza | Yangi sxema + migratsiya, atomar bron funksiyalari |
| 2 | API | Katalog, variantlar, savat/promokod, buyurtma, to'lov, admin endpointlar, rollar |
| 3 | Mini App — xaridor | Yangi dizayn tizimi, barcha xaridor sahifalari |
| 4 | Mini App — admin | Admin bo'limi |
| 5 | Bot | Xabarnomalar, tezkor tasdiqlash, yangi mahsulot xabari |
| 6 | Deploy | Domen, VPS, HTTPS, BotFather'da Mini App ulanishi |
| — | Keyin | Veb-do'kon, ulgurji, sotuvchi roli, Click/Payme |

## 10. Egasidan kerak bo'ladigan narsalar

- [ ] Logotip (SVG yoki PNG) va brend ranglari → `brand/` papkasiga
- [ ] Domen (sotib olingach DNS'ni VPS IP'ga yo'naltirish)
- [ ] To'lov kartalari: raqam, egasi, turi
- [ ] Kategoriyalar ro'yxati va har bir tur uchun o'lcham jadvali (qaysi o'lchovlar: ko'krak, bel, uzunlik…)
- [ ] Yetkazish va "qaytarilmaydi" qoidalari matni
- [ ] Super admin va admin Telegram ID'lari
