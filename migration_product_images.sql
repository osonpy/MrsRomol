-- ══════════════════════════════════════════════════════════════════
-- MIGRATION: product_images jadvali qo'shish
-- Faqat shu faylni SQL Editor'ga ko'chiring va ishga tushiring.
-- ══════════════════════════════════════════════════════════════════

-- 1. Jadval yaratish (allaqachon mavjud bo'lsa — xato chiqarmaydi)
create table if not exists product_images (
  id          uuid primary key default gen_random_uuid(),
  product_id  uuid not null references products(id) on delete cascade,
  file_id     text not null,
  sort_order  integer not null default 0,
  created_at  timestamptz not null default now()
);

-- 2. Index
create index if not exists idx_product_images_product_id
  on product_images(product_id);

-- 3. RLS yoqish
alter table product_images enable row level security;

-- 4. Policy — faqat mavjud bo'lmasa qo'shadi (xato bermaydi)
do $$
begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'product_images'
      and policyname = 'service_role_all'
  ) then
    execute 'create policy "service_role_all" on product_images for all using (true)';
  end if;
end
$$;
