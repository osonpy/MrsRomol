#!/usr/bin/env bash
# Local demo shop: Postgres + PostgREST + a tiny Storage stand-in, seeded with
# demo products. Then run the API and Mini App against it (commands printed at
# the end) and, optionally, the browser walk-through:  node e2e/walk.mjs
# Needs Docker. Stop with:  docker rm -f -v msr-pg msr-rest msr-gw; kill $(cat .demo/storage.pid)
set -euo pipefail
cd "$(dirname "$0")/.."
WORK=.demo
NET=msrromol-test
SECRET=test-jwt-secret-that-is-at-least-32-chars
mkdir -p "$WORK/storage"

docker rm -f -v msr-pg msr-rest msr-gw >/dev/null 2>&1 || true
docker network rm "$NET" >/dev/null 2>&1 || true
docker network create "$NET" >/dev/null

docker run -d --name msr-pg --network "$NET" -e POSTGRES_PASSWORD=test postgres:15-alpine >/dev/null
wait_for() { for _ in $(seq 1 120); do "$@" && return 0; sleep 0.5; done; echo "timeout: $*" >&2; exit 1; }
wait_for docker exec msr-pg pg_isready -U postgres -q; sleep 1
psql() { docker exec -i msr-pg psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql < db/tests/00_supabase_stub.sql
psql < db/schema.sql
psql -c "create role authenticator login password 'test' noinherit; grant anon, service_role to authenticator;"
psql < e2e/seed.sql

uv run python e2e/make_demo_images.py "$WORK/storage"
docker run -d --name msr-rest --network "$NET" \
  -e PGRST_DB_URI=postgres://authenticator:test@msr-pg:5432/postgres \
  -e PGRST_DB_SCHEMAS=public -e PGRST_DB_ANON_ROLE=anon -e PGRST_JWT_SECRET="$SECRET" \
  postgrest/postgrest:v12.2.3 >/dev/null
# Storage stand-in runs on the host; restart it if a previous run left one.
if [ -f "$WORK/storage.pid" ]; then kill "$(cat "$WORK/storage.pid")" 2>/dev/null || true; fi
nohup uv run python e2e/fake_storage.py > "$WORK/storage.log" 2>&1 &
echo $! > "$WORK/storage.pid"
docker run -d --name msr-gw --network "$NET" -p 54329:80 --add-host host.docker.internal:host-gateway \
  -v "$PWD/e2e/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:alpine >/dev/null
wait_for curl -sf -o /dev/null http://localhost:54329/rest/v1/
wait_for curl -s -o /dev/null http://localhost:54330/

KEY=$(cd tests && TEST_JWT_SECRET="$SECRET" uv run python -c "import os, conftest; print(os.environ['SUPABASE_KEY'])")
cat > "$WORK/api.env" <<ENV
BOT_TOKEN=123456:DEMO
ADMIN_GROUP_ID=-100500
ADMIN_NOTIFY_IDS=-100500
SUPER_ADMIN_IDS=123456789
SUPABASE_URL=http://localhost:54329
SUPABASE_KEY=$KEY
MINI_APP_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173
DEV_MODE=true
ENV

cat <<MSG
Demo stack is up. In two terminals:
  set -a; . $WORK/api.env; set +a; uv run uvicorn api.main:app --port 8000
  cd miniapp && VITE_API_URL=http://localhost:8000 npm run dev
Open http://localhost:5173 (you are the demo super admin), or run the walk-through:
  cd e2e && npm install && node walk.mjs ../.demo/shots
MSG
