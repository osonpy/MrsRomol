#!/usr/bin/env bash
# End-to-end API tests: throwaway Postgres + PostgREST (the REST layer Supabase
# runs) behind nginx at /rest/v1, then pytest. Needs Docker.
#   bash tests/run.sh [pytest args]
set -euo pipefail
cd "$(dirname "$0")/.."
NET=msrromol-pytest
JWT_SECRET=test-jwt-secret-that-is-at-least-32-chars
cleanup() { docker rm -f -v msrt-pg msrt-rest msrt-gw >/dev/null 2>&1 || true; docker network rm "$NET" >/dev/null 2>&1 || true; }
cleanup; trap cleanup EXIT
docker network create "$NET" >/dev/null

docker run -d --name msrt-pg --network "$NET" -e POSTGRES_PASSWORD=test postgres:15-alpine >/dev/null
wait_for() { for _ in $(seq 1 120); do "$@" && return 0; sleep 0.5; done; echo "timeout: $*" >&2; exit 1; }
wait_for docker exec msrt-pg pg_isready -U postgres -q; sleep 1
psql() { docker exec -i msrt-pg psql -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql < db/tests/00_supabase_stub.sql
psql < db/schema.sql
psql -c "create role authenticator login password 'test' noinherit; grant anon, service_role to authenticator;"

docker run -d --name msrt-rest --network "$NET" \
  -e PGRST_DB_URI=postgres://authenticator:test@msrt-pg:5432/postgres \
  -e PGRST_DB_SCHEMAS=public -e PGRST_DB_ANON_ROLE=anon -e PGRST_JWT_SECRET="$JWT_SECRET" \
  postgrest/postgrest:v12.2.3 >/dev/null
docker run -d --name msrt-gw --network "$NET" -p 54331:80 \
  -v "$PWD/tests/nginx.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine >/dev/null
wait_for curl -sf -o /dev/null http://localhost:54331/rest/v1/

export TEST_JWT_SECRET="$JWT_SECRET" TEST_DB_CONTAINER=msrt-pg
uv run pytest tests "$@"
