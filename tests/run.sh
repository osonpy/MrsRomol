#!/usr/bin/env bash
# End-to-end API tests: throwaway Postgres + PostgREST (the REST layer Supabase
# runs) behind nginx at /rest/v1, then pytest. Needs Docker.
#   bash tests/run.sh [pytest args]
set -euo pipefail
cd "$(dirname "$0")/.."
NET=msrromol-test
JWT_SECRET=test-jwt-secret-that-is-at-least-32-chars
cleanup() { docker rm -f msr-pg msr-rest msr-gw >/dev/null 2>&1 || true; docker network rm "$NET" >/dev/null 2>&1 || true; }
cleanup; trap cleanup EXIT
docker network create "$NET" >/dev/null

docker run -d --name msr-pg --network "$NET" -e POSTGRES_PASSWORD=test postgres:15-alpine >/dev/null
until docker exec msr-pg pg_isready -U postgres -q; do sleep 0.5; done; sleep 1
psql() { docker exec -i msr-pg psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql < db/tests/00_supabase_stub.sql
psql < db/schema.sql
psql -c "create role authenticator login password 'test' noinherit; grant anon, service_role to authenticator;"

docker run -d --name msr-rest --network "$NET" \
  -e PGRST_DB_URI=postgres://authenticator:test@msr-pg:5432/postgres \
  -e PGRST_DB_SCHEMAS=public -e PGRST_DB_ANON_ROLE=anon -e PGRST_JWT_SECRET="$JWT_SECRET" \
  postgrest/postgrest:v12.2.3 >/dev/null
docker run -d --name msr-gw --network "$NET" -p 54329:80 \
  -v "$PWD/tests/nginx.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine >/dev/null
until curl -sf -o /dev/null http://localhost:54329/rest/v1/; do sleep 0.5; done

export TEST_JWT_SECRET="$JWT_SECRET" TEST_DB_CONTAINER=msr-pg
uv run pytest tests "$@"
