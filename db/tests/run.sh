#!/usr/bin/env bash
# Tests db/schema.sql on a throwaway Postgres 15 container (needs Docker).
#   bash db/tests/run.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
NAME=msrromol-dbtest
docker rm -f -v "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" -e POSTGRES_PASSWORD=test postgres:15-alpine >/dev/null
trap 'docker rm -f -v "$NAME" >/dev/null' EXIT
wait_for() { for _ in $(seq 1 120); do "$@" && return 0; sleep 0.5; done; echo "timeout: $*" >&2; exit 1; }
wait_for docker exec "$NAME" pg_isready -U postgres -q
sleep 1

psql() { docker exec -i "$NAME" psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql < db/tests/00_supabase_stub.sql
psql < db/schema.sql
OUT=$(psql -t < db/tests/10_functions_test.sql 2>&1) || { echo "$OUT" | grep -vE '^\s*$'; exit 1; }
echo "$OUT" | grep -oE '(PASS|FAIL): .*'

# Concurrency: two customers race for the last unit of one variant.
psql <<'SQL'
insert into customers (id, telegram_id) values
  ('00000000-0000-0000-0000-0000000000c1', 501), ('00000000-0000-0000-0000-0000000000c2', 502);
insert into products (id, name_uz, price) values ('10000000-0000-0000-0000-0000000000ff', 'Shapka', 50000);
insert into product_variants (id, product_id, size, stock) values
  ('20000000-0000-0000-0000-0000000000ff', '10000000-0000-0000-0000-0000000000ff', 'S', 1);
SQL
race() {
  psql -t -A <<SQL 2>&1 | grep -oE 'OUT_OF_STOCK|^[0-9a-f-]{36}' | head -1
begin;
select id from create_order('$1',
  '[{"variant_id":"20000000-0000-0000-0000-0000000000ff","quantity":1}]',
  '{"contact_name":"x","contact_phone":"1","region":"r","address":"a","delivery_method":"taxi"}');
select pg_sleep(2);
commit;
SQL
}
race 00000000-0000-0000-0000-0000000000c1 > /tmp/msr_race1 &
sleep 0.3
race 00000000-0000-0000-0000-0000000000c2 > /tmp/msr_race2 &
wait
R="$(cat /tmp/msr_race1) $(cat /tmp/msr_race2)"; rm -f /tmp/msr_race1 /tmp/msr_race2
STOCK=$(psql -t -A -c "select stock from product_variants where id = '20000000-0000-0000-0000-0000000000ff'")
if [[ "$R" == *OUT_OF_STOCK* && "$STOCK" == 0 ]]; then
  echo "PASS: concurrent buyers — one order, one OUT_OF_STOCK, stock 0"
  echo "── $(( $(echo "$OUT" | grep -c 'PASS:') + 1 )) tests passed"
else
  echo "FAIL: concurrency ($R, stock=$STOCK)"; exit 1
fi
