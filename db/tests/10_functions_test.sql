-- Behaviour tests for db/schema.sql. Each block raises on failure.
\set ON_ERROR_STOP on
set client_min_messages = warning;

-- helper: run SQL, return the error message (or null if it succeeded)
create function pg_temp.err(p_sql text) returns text language plpgsql as $$
begin
  execute p_sql;
  return null;
exception when others then
  return sqlerrm;
end $$;

create function pg_temp.check(p_ok boolean, p_name text) returns void language plpgsql as $$
begin
  if p_ok is not true then raise exception 'FAIL: %', p_name; end if;
  raise notice 'PASS: %', p_name;
end $$;
set client_min_messages = notice;

-- fixtures
insert into customers (id, telegram_id, full_name) values
  ('00000000-0000-0000-0000-00000000000a', 1, 'Ali'),
  ('00000000-0000-0000-0000-00000000000b', 2, 'Vali');
insert into customers (id, telegram_id, full_name, role) values
  ('00000000-0000-0000-0000-0000000000ad', 99, 'Admin', 'admin');
insert into products (id, name_uz, name_ru, price) values
  ('10000000-0000-0000-0000-000000000001', 'Ro''mol', 'Платок', 150000);
insert into product_variants (id, product_id, color_uz, size, stock, price_override) values
  ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Qora', 'M', 3, null),
  ('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 'Oq',   'L', 1, 170000);
insert into promo_codes (id, code, discount_type, discount_value, min_order_amount, max_uses) values
  ('30000000-0000-0000-0000-000000000001', 'BAHOR10', 'percent', 10, 200000, 2);
insert into payment_cards (id, card_number, holder_name, card_type) values
  ('40000000-0000-0000-0000-000000000001', '8600123412341234', 'ALI VALIYEV', 'uzcard');

create temp table t (k text primary key, v uuid);
create function pg_temp.d() returns jsonb language sql as $$
  select '{"contact_name":"Ali","contact_phone":"+998901234567","region":"tashkent_city",
           "address":"Chilonzor 1","delivery_method":"taxi"}'::jsonb $$;

-- 1. order: price from DB, merged duplicates, stock reserved, promo applied
do $$
declare o orders;
begin
  o := create_order('00000000-0000-0000-0000-00000000000a',
    '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1},
      {"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1},
      {"variant_id":"20000000-0000-0000-0000-000000000002","quantity":1}]',
    pg_temp.d(), ' bahor10 ');
  insert into t values ('o1', o.id);
  perform pg_temp.check(o.subtotal = 470000, 'subtotal from DB prices + price_override');
  perform pg_temp.check(o.discount = 47000 and o.total = 423000, 'percent promo applied');
  perform pg_temp.check(o.status = 'awaiting_payment' and o.expires_at > now() + interval '29 minutes', '30 min timer started');
  perform pg_temp.check(o.number >= 1001, 'human order number');
  perform pg_temp.check((select count(*) from order_items where order_id = o.id) = 2, 'duplicate lines merged');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 1, 'stock reserved (3-2)');
  perform pg_temp.check((select used_count from promo_codes where code = 'BAHOR10') = 1, 'promo used_count incremented');
end $$;

-- 2. rejections
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000002","quantity":1}]', pg_temp.d())$$) = 'OUT_OF_STOCK', 'out of stock');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":0}]', pg_temp.d())$$) = 'INVALID_QUANTITY', 'quantity 0');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":-3}]', pg_temp.d())$$) = 'INVALID_QUANTITY', 'negative quantity');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b', '[]', pg_temp.d())$$) = 'EMPTY_ORDER', 'empty order');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000a',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d(), 'BAHOR10')$$) = 'PROMO_ALREADY_USED', 'promo once per customer');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d(), 'BAHOR10')$$) = 'PROMO_MIN_AMOUNT', 'promo min amount');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d(), 'YOQKOD')$$) = 'PROMO_INVALID', 'unknown promo');
select pg_temp.check(pg_temp.err($$select create_order('00000000-0000-0000-0000-00000000000b',
  '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d() - 'address')$$) like '%address%', 'address required');
select pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 1, 'failed orders left stock untouched');
select pg_temp.check((select count(*) from orders) = 1, 'failed orders rolled back');

-- 3. payment flow: submit → double review guarded → confirmed → shipped → delivered
do $$
declare o uuid := (select v from t where k = 'o1'); p payments; r orders;
begin
  perform pg_temp.check(pg_temp.err(format($f$select submit_payment(%L, '00000000-0000-0000-0000-00000000000b', null, 'x.jpg')$f$, o)) = 'FORBIDDEN', 'other customer cannot pay');
  p := submit_payment(o, '00000000-0000-0000-0000-00000000000a', '40000000-0000-0000-0000-000000000001', '2026/abc.jpg');
  perform pg_temp.check(p.amount = 423000, 'payment amount = order total');
  perform pg_temp.check((select status from orders where id = o) = 'payment_review', 'order in review');
  perform pg_temp.check(pg_temp.err(format($f$select submit_payment(%L, '00000000-0000-0000-0000-00000000000a', null, 'y.jpg')$f$, o)) = 'INVALID_TRANSITION', 'second receipt rejected');
  r := review_payment(p.id, '00000000-0000-0000-0000-0000000000ad', true);
  perform pg_temp.check(r.status = 'confirmed', 'approve → confirmed');
  perform pg_temp.check(pg_temp.err(format($f$select review_payment(%L, '00000000-0000-0000-0000-0000000000ad', false)$f$, p.id)) = 'ALREADY_REVIEWED', 'double review blocked');
  perform pg_temp.check(pg_temp.err(format($f$select advance_order(%L, '00000000-0000-0000-0000-0000000000ad', 'delivered')$f$, o)) = 'INVALID_TRANSITION', 'cannot skip shipped');
  r := advance_order(o, '00000000-0000-0000-0000-0000000000ad', 'shipped', 'BTS-123');
  perform pg_temp.check(r.status = 'shipped' and r.tracking_number = 'BTS-123', 'shipped with tracking');
  r := advance_order(o, '00000000-0000-0000-0000-0000000000ad', 'delivered');
  perform pg_temp.check(r.status = 'delivered', 'delivered');
  perform pg_temp.check(pg_temp.err(format($f$select cancel_order(%L, '00000000-0000-0000-0000-0000000000ad', 'by_admin')$f$, o)) = 'INVALID_TRANSITION', 'delivered cannot be cancelled');
  perform pg_temp.check((select array_agg(to_status order by id) from order_status_history where order_id = o)
    = array['awaiting_payment','payment_review','confirmed','shipped','delivered'], 'full status history logged');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000002') = 0, 'stock stays sold after delivery');
end $$;

-- 4. reject payment → cancelled, stock and promo returned
do $$
declare o orders; p payments; r orders;
begin
  update promo_codes set min_order_amount = 0 where code = 'BAHOR10';
  o := create_order('00000000-0000-0000-0000-00000000000b',
    '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d(), 'BAHOR10');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 0, 'last unit reserved');
  p := submit_payment(o.id, '00000000-0000-0000-0000-00000000000b', null, 'z.jpg');
  r := review_payment(p.id, '00000000-0000-0000-0000-0000000000ad', false, 'Chek o''qilmaydi');
  perform pg_temp.check(r.status = 'cancelled' and r.cancel_reason = 'payment_rejected', 'reject → cancelled');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 1, 'stock returned on reject');
  perform pg_temp.check((select used_count from promo_codes where code = 'BAHOR10') = 1, 'promo use released');
  perform pg_temp.check((select reject_reason from payments where id = p.id) = 'Chek o''qilmaydi', 'reject reason stored');
end $$;

-- 5. expiry + customer cancel rules
do $$
declare o1 orders; o2 orders; n int;
begin
  o1 := create_order('00000000-0000-0000-0000-00000000000b',
    '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d());
  update orders set expires_at = now() - interval '1 second' where id = o1.id;
  perform pg_temp.check(pg_temp.err(format($f$select submit_payment(%L, '00000000-0000-0000-0000-00000000000b', null, 'late.jpg')$f$, o1.id)) = 'ORDER_EXPIRED', 'late receipt rejected');
  select count(*) into n from expire_orders();
  perform pg_temp.check(n = 1, 'expire_orders cancelled 1');
  perform pg_temp.check((select cancel_reason from orders where id = o1.id) = 'expired', 'reason expired');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 1, 'stock returned on expiry');
  select count(*) into n from expire_orders();
  perform pg_temp.check(n = 0, 'expire_orders idempotent');

  o2 := create_order('00000000-0000-0000-0000-00000000000b',
    '[{"variant_id":"20000000-0000-0000-0000-000000000001","quantity":1}]', pg_temp.d());
  perform pg_temp.check(pg_temp.err(format($f$select cancel_order(%L, '00000000-0000-0000-0000-00000000000a', 'by_customer')$f$, o2.id)) = 'FORBIDDEN', 'customer cannot cancel others order');
  perform cancel_order(o2.id, '00000000-0000-0000-0000-00000000000b', 'by_customer');
  perform pg_temp.check((select stock from product_variants where id = '20000000-0000-0000-0000-000000000001') = 1, 'stock returned on customer cancel');
end $$;

-- 6. access: anon / authenticated can't read tables or call functions
set role anon;
select pg_temp.check(pg_temp.err('select * from customers') like 'permission denied%', 'anon cannot read customers');
select pg_temp.check(pg_temp.err('select * from expire_orders()') like 'permission denied%', 'anon cannot call functions');
reset role;
set role authenticated;
select pg_temp.check(pg_temp.err('select * from orders') like 'permission denied%', 'authenticated cannot read orders');
reset role;
set role service_role;
select pg_temp.check(pg_temp.err('select * from customers') is null, 'service_role can read');
reset role;
select pg_temp.check((select count(*) from storage.buckets where id = 'receipts' and not public) = 1, 'receipts bucket is private');
