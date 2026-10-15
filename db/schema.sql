-- ══════════════════════════════════════════════════════════════════════════════
-- Mrs Romol — database schema (v1)
--
-- For a NEW, empty Supabase project:
--   Dashboard → SQL Editor → New query → paste this whole file → Run.
--
-- Design rules:
--   • Money is stored in whole so'm (bigint).
--   • Every stock/order/payment change goes through the functions at the bottom.
--     They run in one transaction and lock rows, so two customers can never buy
--     the same last item, and two admins can't review one payment twice.
--   • Only the backend (secret / service_role key) can touch data: RLS is on with
--     no policies, and anon/authenticated have no grants.
-- ══════════════════════════════════════════════════════════════════════════════

create schema if not exists extensions;
create extension if not exists pg_trgm with schema extensions;


-- ── Helpers ───────────────────────────────────────────────────────────────────

create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;


-- ══════════════════════════════════════════════════════════════════════════════
-- TABLES
-- ══════════════════════════════════════════════════════════════════════════════

-- ── customers (every Telegram user, including admins) ────────────────────────
create table customers (
  id                  uuid primary key default gen_random_uuid(),
  telegram_id         bigint not null unique,
  full_name           text not null default '',
  phone               text not null default '',
  language            text not null default 'uz' check (language in ('uz', 'ru')),
  role                text not null default 'customer'
                      check (role in ('customer', 'seller', 'admin', 'super_admin')),
  notify_new_products boolean not null default true,
  is_wholesale        boolean not null default false,   -- reserved for wholesale prices
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create trigger customers_updated_at before update on customers
  for each row execute function set_updated_at();

-- ── categories ────────────────────────────────────────────────────────────────
create table categories (
  id          uuid primary key default gen_random_uuid(),
  slug        text not null unique check (slug ~ '^[a-z0-9-]+$'),
  name_uz     text not null,
  name_ru     text not null,
  sort_order  integer not null default 0,
  is_active   boolean not null default true,
  created_at  timestamptz not null default now()
);

-- ── products ──────────────────────────────────────────────────────────────────
-- size_chart example:
--   {"columns": ["chest", "length"],
--    "rows": [{"size": "M", "chest": [88, 92], "length": [140, 142]}, ...]}
-- Values are centimetres; a [min, max] pair is a range.
create table products (
  id               uuid primary key default gen_random_uuid(),
  category_id      uuid references categories(id) on delete set null,
  name_uz          text not null,
  name_ru          text not null default '',
  description_uz   text not null default '',
  description_ru   text not null default '',
  price            bigint not null check (price >= 0),
  wholesale_price  bigint check (wholesale_price >= 0),  -- reserved
  cost_price       bigint check (cost_price >= 0),       -- admin only
  size_chart       jsonb,
  is_active        boolean not null default true,
  announced_at     timestamptz,                          -- sent to subscribers (once)
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create trigger products_updated_at before update on products
  for each row execute function set_updated_at();
create index products_category_idx on products(category_id) where is_active;
create index products_created_idx  on products(created_at desc) where is_active;
-- Search text: both names, lower-case, without apostrophes, so that
-- "romol", "ro'mol", "ro‘mol" and "roʻmol" all find "Ro'mol".
alter table products add column search_text text generated always as (
  lower(translate(name_uz || ' ' || name_ru, $$'`ʻʼ‘’$$, ''))
) stored;
create index products_search_trgm on products using gin (search_text extensions.gin_trgm_ops);

-- ── product_variants (colour × size, each with its own stock) ────────────────
create table product_variants (
  id              uuid primary key default gen_random_uuid(),
  product_id      uuid not null references products(id) on delete cascade,
  color_uz        text,
  color_ru        text,
  color_hex       text check (color_hex ~ '^#[0-9A-Fa-f]{6}$'),
  size            text,
  sku             text unique,
  stock           integer not null default 0 check (stock >= 0),
  price_override  bigint check (price_override >= 0),  -- null = product price
  sort_order      integer not null default 0,
  is_active       boolean not null default true,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique nulls not distinct (product_id, color_uz, size)
);
create trigger product_variants_updated_at before update on product_variants
  for each row execute function set_updated_at();
create index product_variants_product_idx on product_variants(product_id);

-- ── product_images (max 5 per product, enforced by the API) ──────────────────
create table product_images (
  id            uuid primary key default gen_random_uuid(),
  product_id    uuid not null references products(id) on delete cascade,
  color_uz      text,              -- shown when this colour is selected; null = all
  storage_path  text not null,     -- path inside the "product-images" bucket
  sort_order    integer not null default 0,
  created_at    timestamptz not null default now()
);
create index product_images_product_idx on product_images(product_id, sort_order);

-- ── favorites ─────────────────────────────────────────────────────────────────
create table favorites (
  customer_id  uuid not null references customers(id) on delete cascade,
  product_id   uuid not null references products(id) on delete cascade,
  created_at   timestamptz not null default now(),
  primary key (customer_id, product_id)
);

-- ── promo codes ───────────────────────────────────────────────────────────────
create table promo_codes (
  id                  uuid primary key default gen_random_uuid(),
  code                text not null unique check (code = upper(code) and code ~ '^[A-Z0-9_-]{3,32}$'),
  discount_type       text not null check (discount_type in ('percent', 'fixed')),
  discount_value      bigint not null check (discount_value > 0),
  min_order_amount    bigint not null default 0 check (min_order_amount >= 0),
  max_uses            integer check (max_uses > 0),        -- null = unlimited
  used_count          integer not null default 0 check (used_count >= 0),
  per_customer_limit  integer not null default 1 check (per_customer_limit > 0),
  starts_at           timestamptz,
  ends_at             timestamptz,
  is_active           boolean not null default true,
  created_at          timestamptz not null default now(),
  check (discount_type <> 'percent' or discount_value <= 100)
);

-- ── payment cards shown at checkout ───────────────────────────────────────────
create table payment_cards (
  id           uuid primary key default gen_random_uuid(),
  card_number  text not null check (card_number ~ '^[0-9]{16}$'),
  holder_name  text not null,
  card_type    text not null check (card_type in ('uzcard', 'humo', 'visa', 'mastercard')),
  sort_order   integer not null default 0,
  is_active    boolean not null default true,
  created_at   timestamptz not null default now()
);

-- ── orders ────────────────────────────────────────────────────────────────────
create table orders (
  id               uuid primary key default gen_random_uuid(),
  number           bigint generated always as identity (start with 1001) unique,  -- "#1001"
  customer_id      uuid not null references customers(id) on delete restrict,
  status           text not null default 'awaiting_payment' check (status in (
                     'awaiting_payment', 'payment_review', 'confirmed',
                     'shipped', 'delivered', 'cancelled')),
  cancel_reason    text check (cancel_reason in (
                     'expired', 'payment_rejected', 'by_admin', 'by_customer')),
  -- delivery
  contact_name     text not null check (length(btrim(contact_name)) > 0),
  contact_phone    text not null check (length(btrim(contact_phone)) > 0),
  region           text not null,            -- region code, e.g. 'tashkent_city'
  district         text not null default '',
  address          text not null check (length(btrim(address)) > 0),
  location_lat     double precision check (location_lat between -90 and 90),
  location_lng     double precision check (location_lng between -180 and 180),
  delivery_method  text not null check (delivery_method in ('taxi', 'post', 'bts')),
  tracking_number  text,
  customer_note    text not null default '',
  admin_note       text not null default '',
  -- money
  subtotal         bigint not null default 0 check (subtotal >= 0),
  discount         bigint not null default 0 check (discount >= 0),
  total            bigint not null default 0 check (total >= 0),
  promo_code_id    uuid references promo_codes(id) on delete set null,
  -- timing
  expires_at       timestamptz,              -- payment deadline while awaiting_payment
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  check ((status = 'cancelled') = (cancel_reason is not null))
);
create trigger orders_updated_at before update on orders
  for each row execute function set_updated_at();
create index orders_customer_idx on orders(customer_id, created_at desc);
create index orders_status_idx   on orders(status, created_at desc);
create index orders_expiry_idx   on orders(expires_at) where status = 'awaiting_payment';

-- ── order_items (name/colour/size/price are copied: history never changes) ───
create table order_items (
  id              uuid primary key default gen_random_uuid(),
  order_id        uuid not null references orders(id) on delete cascade,
  variant_id      uuid references product_variants(id) on delete set null,
  product_id      uuid references products(id) on delete set null,
  product_name_uz text not null,
  product_name_ru text not null,
  color_uz        text,
  color_ru        text,
  size            text,
  unit_price      bigint not null check (unit_price >= 0),
  quantity        integer not null check (quantity > 0),
  unique (order_id, variant_id)
);
create index order_items_order_idx on order_items(order_id);

-- ── promo_usages (one row per order that used a code) ─────────────────────────
create table promo_usages (
  promo_id     uuid not null references promo_codes(id) on delete cascade,
  customer_id  uuid not null references customers(id) on delete cascade,
  order_id     uuid not null unique references orders(id) on delete cascade,
  created_at   timestamptz not null default now()
);
create index promo_usages_customer_idx on promo_usages(promo_id, customer_id);

-- ── order_status_history (who changed what, when) ────────────────────────────
create table order_status_history (
  id           bigint generated always as identity primary key,
  order_id     uuid not null references orders(id) on delete cascade,
  from_status  text,
  to_status    text not null,
  changed_by   uuid references customers(id) on delete set null,  -- null = system
  note         text not null default '',
  created_at   timestamptz not null default now()
);
create index order_status_history_order_idx on order_status_history(order_id, id);

-- ── payments ──────────────────────────────────────────────────────────────────
create table payments (
  id             uuid primary key default gen_random_uuid(),
  order_id       uuid not null references orders(id) on delete cascade,
  card_id        uuid references payment_cards(id) on delete set null,
  amount         bigint not null check (amount >= 0),
  receipt_path   text not null,     -- path inside the private "receipts" bucket
  status         text not null default 'pending_verification'
                 check (status in ('pending_verification', 'verified', 'rejected')),
  reviewed_by    uuid references customers(id) on delete set null,
  reviewed_at    timestamptz,
  reject_reason  text,
  created_at     timestamptz not null default now()
);
create index payments_order_idx on payments(order_id);
create index payments_pending_idx on payments(created_at) where status = 'pending_verification';
-- At most one payment per order that is waiting or accepted.
create unique index payments_one_active_per_order
  on payments(order_id) where status in ('pending_verification', 'verified');

-- ── settings (key → JSON value, edited by super_admin) ───────────────────────
create table settings (
  key         text primary key,
  value       jsonb not null,
  updated_at  timestamptz not null default now()
);
insert into settings (key, value) values
  ('reservation_minutes', '30'),
  ('rules_uz', '""'),
  ('rules_ru', '""');


-- ══════════════════════════════════════════════════════════════════════════════
-- FUNCTIONS — the only way stock, orders and payments change
--
-- Errors are raised as  P0001 with message = machine code (e.g. 'OUT_OF_STOCK')
-- and an optional JSON detail. The API maps the code to an HTTP response.
-- ══════════════════════════════════════════════════════════════════════════════

-- Internal: append to order_status_history.
create or replace function _log_status(
  p_order_id uuid, p_from text, p_to text, p_actor uuid, p_note text default ''
) returns void
language sql as $$
  insert into order_status_history (order_id, from_status, to_status, changed_by, note)
  values (p_order_id, p_from, p_to, p_actor, coalesce(p_note, ''));
$$;


-- Validate a promo code for a customer and subtotal; returns its id and the
-- discount in so'm. Locks the promo row (callers commit or roll back quickly).
create or replace function promo_discount(
  p_code text, p_customer_id uuid, p_subtotal bigint
) returns table (promo_id uuid, discount bigint)
language plpgsql as $$
declare
  v_promo promo_codes%rowtype;
  v_used  integer;
begin
  select * into v_promo from promo_codes
   where code = upper(btrim(p_code))
   for update;

  if not found or not v_promo.is_active
     or (v_promo.starts_at is not null and v_promo.starts_at > now())
     or (v_promo.ends_at   is not null and v_promo.ends_at   < now()) then
    raise exception 'PROMO_INVALID';
  end if;
  if v_promo.max_uses is not null and v_promo.used_count >= v_promo.max_uses then
    raise exception 'PROMO_EXHAUSTED';
  end if;

  select count(*) into v_used from promo_usages u
   where u.promo_id = v_promo.id and u.customer_id = p_customer_id;
  if v_used >= v_promo.per_customer_limit then
    raise exception 'PROMO_ALREADY_USED';
  end if;

  if p_subtotal < v_promo.min_order_amount then
    raise exception 'PROMO_MIN_AMOUNT'
      using detail = json_build_object('min_order_amount', v_promo.min_order_amount)::text;
  end if;

  promo_id := v_promo.id;
  discount := case v_promo.discount_type
                when 'percent' then (p_subtotal * v_promo.discount_value) / 100
                else least(v_promo.discount_value, p_subtotal)
              end;
  return next;
end $$;


-- Create an order: lock variants, check stock, take prices from the DB,
-- reserve stock, apply promo, start the payment timer.
--   p_items    : [{"variant_id": "<uuid>", "quantity": 2}, ...]
--   p_delivery : {"contact_name", "contact_phone", "region", "district", "address",
--                 "location_lat", "location_lng", "delivery_method", "customer_note"}
create or replace function create_order(
  p_customer_id uuid,
  p_items       jsonb,
  p_delivery    jsonb,
  p_promo_code  text default null
) returns orders
language plpgsql as $$
declare
  v_order    orders%rowtype;
  v_line     record;
  v_variant  record;
  v_price    bigint;
  v_subtotal bigint := 0;
  v_discount bigint := 0;
  v_promo_id uuid;
  v_minutes  integer;
begin
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception 'EMPTY_ORDER';
  end if;
  if jsonb_array_length(p_items) > 50 then
    raise exception 'TOO_MANY_ITEMS';
  end if;

  select coalesce((value #>> '{}')::integer, 30) into v_minutes
    from settings where key = 'reservation_minutes';

  insert into orders (
    customer_id, contact_name, contact_phone, region, district, address,
    location_lat, location_lng, delivery_method, customer_note, expires_at
  ) values (
    p_customer_id,
    p_delivery->>'contact_name',
    p_delivery->>'contact_phone',
    p_delivery->>'region',
    coalesce(p_delivery->>'district', ''),
    p_delivery->>'address',
    (p_delivery->>'location_lat')::double precision,
    (p_delivery->>'location_lng')::double precision,
    p_delivery->>'delivery_method',
    coalesce(p_delivery->>'customer_note', ''),
    now() + make_interval(mins => coalesce(v_minutes, 30))
  ) returning * into v_order;

  -- Merge duplicate variants; lock in a fixed order (by id) to avoid deadlocks.
  for v_line in
    select (e->>'variant_id')::uuid as variant_id, sum((e->>'quantity')::integer) as quantity
      from jsonb_array_elements(p_items) e
     group by 1
     order by 1
  loop
    if v_line.quantity is null or v_line.quantity < 1 or v_line.quantity > 100 then
      raise exception 'INVALID_QUANTITY'
        using detail = json_build_object('variant_id', v_line.variant_id)::text;
    end if;

    select v.id, v.product_id, v.color_uz, v.color_ru, v.size, v.stock,
           v.price_override, v.is_active as variant_active,
           p.price, p.name_uz, p.name_ru, p.is_active as product_active
      into v_variant
      from product_variants v
      join products p on p.id = v.product_id
     where v.id = v_line.variant_id
       for update of v;

    if not found then
      raise exception 'VARIANT_NOT_FOUND'
        using detail = json_build_object('variant_id', v_line.variant_id)::text;
    end if;
    if not (v_variant.variant_active and v_variant.product_active) then
      raise exception 'PRODUCT_INACTIVE'
        using detail = json_build_object('variant_id', v_line.variant_id)::text;
    end if;
    if v_variant.stock < v_line.quantity then
      raise exception 'OUT_OF_STOCK'
        using detail = json_build_object(
          'variant_id', v_line.variant_id, 'available', v_variant.stock)::text;
    end if;

    update product_variants set stock = stock - v_line.quantity where id = v_variant.id;

    v_price := coalesce(v_variant.price_override, v_variant.price);
    v_subtotal := v_subtotal + v_price * v_line.quantity;

    insert into order_items (
      order_id, variant_id, product_id, product_name_uz, product_name_ru,
      color_uz, color_ru, size, unit_price, quantity
    ) values (
      v_order.id, v_variant.id, v_variant.product_id, v_variant.name_uz, v_variant.name_ru,
      v_variant.color_uz, v_variant.color_ru, v_variant.size, v_price, v_line.quantity
    );
  end loop;

  if nullif(btrim(p_promo_code), '') is not null then
    select d.promo_id, d.discount into v_promo_id, v_discount
      from promo_discount(p_promo_code, p_customer_id, v_subtotal) d;
    insert into promo_usages (promo_id, customer_id, order_id)
      values (v_promo_id, p_customer_id, v_order.id);
    update promo_codes set used_count = used_count + 1 where id = v_promo_id;
  end if;

  update orders
     set subtotal = v_subtotal,
         discount = v_discount,
         total = v_subtotal - v_discount,
         promo_code_id = v_promo_id
   where id = v_order.id
   returning * into v_order;

  perform _log_status(v_order.id, null, 'awaiting_payment', p_customer_id);
  return v_order;
end $$;


-- Internal: cancel a locked order — return stock, release the promo use,
-- reject a pending payment.
create or replace function _cancel_order(
  p_order orders, p_reason text, p_actor uuid, p_note text default ''
) returns orders
language plpgsql as $$
declare
  v_order orders%rowtype;
begin
  if p_order.status not in ('awaiting_payment', 'payment_review', 'confirmed') then
    raise exception 'INVALID_TRANSITION'
      using detail = json_build_object('from', p_order.status, 'to', 'cancelled')::text;
  end if;

  -- Lock variants in id order, then return the stock.
  perform 1 from product_variants
   where id in (select variant_id from order_items where order_id = p_order.id)
   order by id
     for update;
  update product_variants v
     set stock = v.stock + oi.quantity
    from order_items oi
   where oi.order_id = p_order.id and v.id = oi.variant_id;

  if p_order.promo_code_id is not null then
    delete from promo_usages where order_id = p_order.id;
    update promo_codes set used_count = greatest(used_count - 1, 0)
     where id = p_order.promo_code_id;
  end if;

  update payments
     set status = 'rejected', reviewed_by = p_actor, reviewed_at = now(),
         reject_reason = coalesce(reject_reason, 'order cancelled')
   where order_id = p_order.id and status = 'pending_verification';

  update orders set status = 'cancelled', cancel_reason = p_reason, expires_at = null
   where id = p_order.id
   returning * into v_order;

  perform _log_status(p_order.id, p_order.status, 'cancelled', p_actor,
                      p_reason || coalesce(': ' || nullif(p_note, ''), ''));
  return v_order;
end $$;


-- Cancel an order. Customers may only cancel while it still awaits payment.
create or replace function cancel_order(
  p_order_id uuid, p_actor uuid, p_reason text, p_note text default ''
) returns orders
language plpgsql as $$
declare
  v_order orders%rowtype;
begin
  if p_reason not in ('by_admin', 'by_customer') then
    raise exception 'INVALID_REASON';
  end if;

  select * into v_order from orders where id = p_order_id for update;
  if not found then
    raise exception 'ORDER_NOT_FOUND';
  end if;
  if p_reason = 'by_customer' then
    if v_order.customer_id <> p_actor then
      raise exception 'FORBIDDEN';
    end if;
    if v_order.status <> 'awaiting_payment' then
      raise exception 'INVALID_TRANSITION'
        using detail = json_build_object('from', v_order.status, 'to', 'cancelled')::text;
    end if;
  end if;

  return _cancel_order(v_order, p_reason, p_actor, p_note);
end $$;


-- Cancel every order whose payment timer ran out. Run every minute.
-- Returns the cancelled orders so the caller can notify customers.
create or replace function expire_orders() returns setof orders
language plpgsql as $$
declare
  v_order orders%rowtype;
begin
  for v_order in
    select * from orders
     where status = 'awaiting_payment' and expires_at < now()
     order by expires_at
       for update skip locked
  loop
    return next _cancel_order(v_order, 'expired', null);
  end loop;
end $$;


-- Customer uploaded a receipt: stop the timer and send the order to review.
create or replace function submit_payment(
  p_order_id uuid, p_customer_id uuid, p_card_id uuid, p_receipt_path text
) returns payments
language plpgsql as $$
declare
  v_order   orders%rowtype;
  v_payment payments%rowtype;
begin
  select * into v_order from orders where id = p_order_id for update;
  if not found then
    raise exception 'ORDER_NOT_FOUND';
  end if;
  if v_order.customer_id <> p_customer_id then
    raise exception 'FORBIDDEN';
  end if;
  if v_order.status <> 'awaiting_payment' then
    raise exception 'INVALID_TRANSITION'
      using detail = json_build_object('from', v_order.status, 'to', 'payment_review')::text;
  end if;
  if v_order.expires_at < now() then
    raise exception 'ORDER_EXPIRED';
  end if;
  if p_card_id is not null
     and not exists (select 1 from payment_cards where id = p_card_id and is_active) then
    raise exception 'CARD_NOT_FOUND';
  end if;
  if nullif(btrim(p_receipt_path), '') is null then
    raise exception 'RECEIPT_REQUIRED';
  end if;

  insert into payments (order_id, card_id, amount, receipt_path)
  values (p_order_id, p_card_id, v_order.total, p_receipt_path)
  returning * into v_payment;

  update orders set status = 'payment_review', expires_at = null where id = p_order_id;
  perform _log_status(p_order_id, 'awaiting_payment', 'payment_review', p_customer_id);
  return v_payment;
end $$;


-- Admin approves or rejects a payment. Safe against double taps: the second
-- reviewer gets ALREADY_REVIEWED.
create or replace function review_payment(
  p_payment_id uuid, p_admin_id uuid, p_approve boolean, p_reason text default null
) returns orders
language plpgsql as $$
declare
  v_payment payments%rowtype;
  v_order   orders%rowtype;
begin
  select * into v_payment from payments where id = p_payment_id;
  if not found then
    raise exception 'PAYMENT_NOT_FOUND';
  end if;
  -- Lock order first (same order as the other functions), then the payment.
  select * into v_order from orders where id = v_payment.order_id for update;
  select * into v_payment from payments where id = p_payment_id for update;

  if v_payment.status <> 'pending_verification' then
    raise exception 'ALREADY_REVIEWED'
      using detail = json_build_object('status', v_payment.status)::text;
  end if;

  if p_approve then
    update payments set status = 'verified', reviewed_by = p_admin_id, reviewed_at = now()
     where id = p_payment_id;
    update orders set status = 'confirmed' where id = v_order.id returning * into v_order;
    perform _log_status(v_order.id, 'payment_review', 'confirmed', p_admin_id);
    return v_order;
  end if;

  update payments
     set status = 'rejected', reviewed_by = p_admin_id, reviewed_at = now(),
         reject_reason = nullif(btrim(p_reason), '')
   where id = p_payment_id;
  return _cancel_order(v_order, 'payment_rejected', p_admin_id, coalesce(p_reason, ''));
end $$;


-- Move a paid order forward: confirmed → shipped → delivered.
create or replace function advance_order(
  p_order_id uuid, p_admin_id uuid, p_to text,
  p_tracking_number text default null, p_note text default ''
) returns orders
language plpgsql as $$
declare
  v_order orders%rowtype;
  v_from  text;
begin
  select * into v_order from orders where id = p_order_id for update;
  if not found then
    raise exception 'ORDER_NOT_FOUND';
  end if;
  v_from := v_order.status;

  if not ((v_from = 'confirmed' and p_to = 'shipped')
       or (v_from = 'shipped'   and p_to = 'delivered')) then
    raise exception 'INVALID_TRANSITION'
      using detail = json_build_object('from', v_from, 'to', p_to)::text;
  end if;

  update orders
     set status = p_to,
         tracking_number = coalesce(nullif(btrim(p_tracking_number), ''), tracking_number)
   where id = p_order_id
   returning * into v_order;
  perform _log_status(p_order_id, v_from, p_to, p_admin_id, p_note);
  return v_order;
end $$;


-- ══════════════════════════════════════════════════════════════════════════════
-- ACCESS — backend only
-- ══════════════════════════════════════════════════════════════════════════════

do $$
declare t text;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t);
  end loop;
end $$;

-- Supabase exposes tables and functions to anon/authenticated through its REST
-- API by default. Nothing here is meant for direct client access.
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;
grant  all on all tables    in schema public to service_role;
grant  all on all sequences in schema public to service_role;
grant  execute on all functions in schema public to service_role;

alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke execute on functions from public, anon, authenticated;


-- ══════════════════════════════════════════════════════════════════════════════
-- STORAGE BUCKETS
-- ══════════════════════════════════════════════════════════════════════════════

-- Product photos: public read (shop pages), written only by the backend.
-- Receipts: private — the backend hands admins short-lived signed URLs.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types) values
  ('product-images', 'product-images', true,  5 * 1024 * 1024,
   array['image/jpeg', 'image/png', 'image/webp']),
  ('receipts',       'receipts',       false, 10 * 1024 * 1024,
   array['image/jpeg', 'image/png', 'image/webp', 'image/heic'])
on conflict (id) do nothing;
