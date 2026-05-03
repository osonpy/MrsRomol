-- ══════════════════════════════════════════════════════════════════
-- migration_miniapp_v2.sql
-- Misr Romol — Mini App uchun DB yangilanishlari
-- Supabase Dashboard → SQL Editor → New Query → bu faylni joylashtir
-- ══════════════════════════════════════════════════════════════════

-- ── 1. products: image_file_id va metadata kolonkalari ────────────
-- image_file_id: mahsulotning Telegram file_id si (rasmni ko'rsatish uchun)
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS image_file_id TEXT DEFAULT NULL;

-- metadata: JSON (ranglar va boshqa variant ma'lumotlari)
-- Misol: {"colors": ["Qizil", "Ko'k", "Yashil"]}
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

-- ── 2. customers: is_wholesale kolonkasi ──────────────────────────
ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS is_wholesale BOOLEAN NOT NULL DEFAULT FALSE;

-- ── 3. orders: address kolonkasi ──────────────────────────────────
-- Yetkazib berish manzili (delivery_type='delivery' bo'lganda to'ldiriladi)
ALTER TABLE orders
  ADD COLUMN IF NOT EXISTS address TEXT DEFAULT '';

-- ── 4. payments: receipt_file_id kolonkasi ────────────────────────
-- Telegram file_id (chek rasmi). receipt_url o'rniga ishlatiladi.
ALTER TABLE payments
  ADD COLUMN IF NOT EXISTS receipt_file_id TEXT DEFAULT NULL;

-- ── 5. Mavjud mahsulotlarga rang misollari (ixtiyoriy) ────────────
-- Kerak bo'lsa, quyidagi UPDATE ni tahrir qilib ishga tushir:
-- UPDATE products
--   SET metadata = '{"colors": ["Qizil", "Ko''k", "Yashil", "Sariq"]}'
-- WHERE category = 'Ro''mollar';

-- ── Tekshirish: qo'shilgan kolonkalarni ko'rish ───────────────────
SELECT
  table_name,
  column_name,
  data_type,
  column_default
FROM information_schema.columns
WHERE table_name IN ('products', 'orders', 'payments', 'customers')
  AND column_name IN ('image_file_id', 'metadata', 'address', 'receipt_file_id', 'is_wholesale')
ORDER BY table_name, column_name;
