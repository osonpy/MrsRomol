-- ══════════════════════════════════════════════════════════════════
-- DIQQAT: Bu script barcha mijozlar va buyurtmalarni o'chiradi!
-- Mahsulotlar (products) va rasmlar (product_images) saqlanib qoladi.
-- Faqat Supabase SQL Editor da ishlatish!
-- ══════════════════════════════════════════════════════════════════

-- Barcha ma'lumotlarni o'chirish (CASCADE FK larni ham hal qiladi)
TRUNCATE TABLE
    payments,
    order_items,
    orders,
    customers
CASCADE;

-- Tekshirish: jadvallar bo'sh ekanligini ko'rish
SELECT 'customers'   AS table_name, COUNT(*) AS rows FROM customers
UNION ALL
SELECT 'orders',       COUNT(*) FROM orders
UNION ALL
SELECT 'order_items',  COUNT(*) FROM order_items
UNION ALL
SELECT 'payments',     COUNT(*) FROM payments;

-- products va product_images saqlanib qoladi (o'chirilmaydi)
