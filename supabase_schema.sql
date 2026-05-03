-- ══════════════════════════════════════════════════════════════════
-- Misr Romol — Supabase PostgreSQL Schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ══════════════════════════════════════════════════════════════════

-- Enable UUID extension (already enabled on Supabase by default)
create extension if not exists "pgcrypto";

-- ── customers ──────────────────────────────────────────────────────
create table if not exists customers (
  id           uuid primary key default gen_random_uuid(),
  full_name    text not null,
  phone        text default '',
  telegram_id  text not null unique,
  language     text not null default 'uz',
  created_at   timestamptz not null default now()
);

-- ── products ───────────────────────────────────────────────────────
create table if not exists products (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  category         text,
  description      text,
  stock_qty        integer not null default 0,
  cost_price       numeric(12, 2) not null default 0,
  sell_price       numeric(12, 2) not null default 0,
  wholesale_price  numeric(12, 2) not null default 0,
  is_active        boolean not null default true
);

-- ── orders ─────────────────────────────────────────────────────────
create table if not exists orders (
  id            uuid primary key default gen_random_uuid(),
  customer_id   uuid not null references customers(id) on delete cascade,
  source        text not null default 'telegram',
  status        text not null default 'pending',
  delivery_type text not null default 'pickup',
  notes         text default '',
  total_amount  numeric(14, 2) not null default 0,
  created_at    timestamptz not null default now()
);

-- ── product_images ────────────────────────────────────────────────
-- Stores up to 3 Telegram file_ids per product.
-- file_id is reused directly when sending photos — no re-upload needed.
create table if not exists product_images (
  id          uuid primary key default gen_random_uuid(),
  product_id  uuid not null references products(id) on delete cascade,
  file_id     text not null,          -- Telegram file_id string
  sort_order  integer not null default 0,  -- 0 = primary photo
  created_at  timestamptz not null default now()
);

-- ── order_items ────────────────────────────────────────────────────
create table if not exists order_items (
  id          uuid primary key default gen_random_uuid(),
  order_id    uuid not null references orders(id) on delete cascade,
  product_id  uuid not null references products(id),
  quantity    integer not null default 1,
  unit_price  numeric(12, 2) not null default 0
);

-- ── payments ───────────────────────────────────────────────────────
create table if not exists payments (
  id          uuid primary key default gen_random_uuid(),
  order_id    uuid not null references orders(id) on delete cascade,
  method      text not null default 'card',
  status      text not null default 'pending_verification',
  receipt_url text default '',
  amount      numeric(14, 2) not null default 0,
  paid_at     timestamptz not null default now()
);

-- ── Indexes for common query patterns ─────────────────────────────
create index if not exists idx_customers_telegram_id on customers(telegram_id);
create index if not exists idx_orders_customer_id    on orders(customer_id);
create index if not exists idx_orders_status         on orders(status);
create index if not exists idx_order_items_order_id  on order_items(order_id);
create index if not exists idx_payments_order_id     on payments(order_id);
create index if not exists idx_product_images_product_id on product_images(product_id);

-- ── Row Level Security (RLS) ──────────────────────────────────────
-- Enable RLS on all tables so only the service_role key can write.
-- The bot uses the anon key for reads; service_role for writes is
-- handled automatically when SUPABASE_KEY is the service_role key.
alter table customers       enable row level security;
alter table products        enable row level security;
alter table orders          enable row level security;
alter table order_items     enable row level security;
alter table payments        enable row level security;
alter table product_images  enable row level security;

-- Allow full access for the service_role (used by the bot backend)
create policy "service_role_all" on customers       for all using (true);
create policy "service_role_all" on products        for all using (true);
create policy "service_role_all" on orders          for all using (true);
create policy "service_role_all" on order_items     for all using (true);
create policy "service_role_all" on payments        for all using (true);
create policy "service_role_all" on product_images  for all using (true);

-- ── Sample products ────────────────────────────────────────────────
insert into products (name, category, description, stock_qty, cost_price, sell_price, wholesale_price, is_active)
values
  ('Misr Zarbob Ro''mol', 'Ro''mollar', 'Misrning an''anaviy zarbob ro''moli. 100% ipak.', 50, 80000, 150000, 120000, true),
  ('Paxta Gaz Mato', 'Gazlamalar', 'Yumshoq va nafis paxta gaz matosi. Kiyim tikish uchun ideal.', 200, 25000, 55000, 42000, true),
  ('Misr Ketan Mato', 'Gazlamalar', 'Sifatli ketan matosi. Dag''al va chidamli.', 150, 35000, 70000, 55000, true),
  ('Ipak Kaftan Ro''mol', 'Ro''mollar', 'Eng yuqori sifatli ipak kaftan ro''mol. Turli ranglarda.', 30, 120000, 220000, 180000, true),
  ('Misr Terri Sochiq', 'Sochiqlar', 'Qalin va yumshoq terri sochiq. Tez quritadi.', 100, 40000, 85000, 65000, true);
