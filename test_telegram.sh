#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# test_telegram.sh — try the shop inside real Telegram, before having a domain.
#
#   bash test_telegram.sh          demo mode: local database with sample products
#   bash test_telegram.sh real     your Supabase project (from .env)
#
# Opens two temporary HTTPS tunnels (Cloudflare), starts the API, the Mini App
# and the bot wired to them. Then send /start to your bot in Telegram and tap
# "Do'konni ochish". Ctrl+C stops everything.
#
# Needs: .env (BOT_TOKEN, SUPER_ADMIN_IDS), Docker (demo mode), cloudflared.
# NO_BOT=1 skips starting the bot (if it already runs with the same MINI_APP_URL).
# The bot must not be running anywhere else at the same time (one bot = one
# running copy; otherwise Telegram reports a conflict).
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-demo}"
CLOUDFLARED="${CLOUDFLARED:-$(command -v cloudflared || echo "$HOME/.local/bin/cloudflared")}"
LOGS=.demo/telegram
mkdir -p "$LOGS"

env_value() { grep -E "^$1=" .env | tail -1 | cut -d= -f2- | tr -d '"' ; }
BOT_TOKEN=$(env_value BOT_TOKEN)
SUPER_ADMIN_IDS=$(env_value SUPER_ADMIN_IDS)
[ -n "$BOT_TOKEN" ] || { echo "❌ .env da BOT_TOKEN yo'q"; exit 1; }
[ -x "$CLOUDFLARED" ] || { echo "❌ cloudflared topilmadi"; exit 1; }

PIDS=()
cleanup() {
  echo; echo "🛑 To'xtatilmoqda..."
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── 1. Database ───────────────────────────────────────────────────────────────
if [ "$MODE" = demo ]; then
  echo "▶ Demo baza (namuna mahsulotlar)..."
  bash e2e/demo_stack.sh > "$LOGS/demo_stack.log" 2>&1
  set -a; . .demo/api.env; set +a
  export BOT_TOKEN SUPER_ADMIN_IDS
  # Demo orders notify only the shop owner, not the admin group.
  export ADMIN_NOTIFY_IDS="$SUPER_ADMIN_IDS" ADMIN_GROUP_ID="${SUPER_ADMIN_IDS%%,*}"
elif [ "$MODE" = real ]; then
  echo "▶ Haqiqiy Supabase (.env)"
else
  echo "Foydalanish: bash test_telegram.sh [demo|real]"; exit 1
fi
export DEV_MODE=false

# ── 2. Tunnels ────────────────────────────────────────────────────────────────
tunnel() {  # $1 = local port, $2 = name
  "$CLOUDFLARED" tunnel --no-autoupdate --url "http://localhost:$1" > "$LOGS/tunnel_$2.log" 2>&1 &
  PIDS+=($!)
}
tunnel 5173 app
tunnel 8000 api
echo "▶ Tunnellar ochilmoqda..."
url_of() { grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOGS/tunnel_$1.log" 2>/dev/null | head -1 || true; }
for _ in $(seq 1 60); do
  APP_URL=$(url_of app); API_URL=$(url_of api)
  [ -n "$APP_URL" ] && [ -n "$API_URL" ] && break
  sleep 0.5
done
[ -n "${APP_URL:-}" ] && [ -n "${API_URL:-}" ] || { echo "❌ Tunnel ochilmadi. Loglar: $LOGS/"; exit 1; }

export MINI_APP_URL="$APP_URL" ALLOWED_ORIGINS="$APP_URL"

# ── 3. API, Mini App, bot ─────────────────────────────────────────────────────
echo "▶ API..."
uv run uvicorn api.main:app --port 8000 > "$LOGS/api.log" 2>&1 &
PIDS+=($!)
echo "▶ Mini App..."
(cd miniapp && VITE_API_URL="$API_URL" exec npx vite --port 5173 --strictPort > "../$LOGS/miniapp.log" 2>&1) &
PIDS+=($!)
for _ in $(seq 1 60); do
  curl -sf -o /dev/null http://localhost:8000/health && curl -sf -o /dev/null http://localhost:5173 && break
  sleep 0.5
done
if [ "${NO_BOT:-0}" != 1 ]; then  # NO_BOT=1: the bot already runs elsewhere
  echo "▶ Bot..."
  uv run python main.py > "$LOGS/bot.log" 2>&1 &
  PIDS+=($!)
fi

# Tunnels need a few seconds before they serve traffic.
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "$API_URL/health" && curl -sf -o /dev/null "$APP_URL" && break
  sleep 1
done

cat <<MSG

╔══════════════════════════════════════════════════════════════╗
║  ✅ Tayyor! ($MODE rejimi)                                    
╚══════════════════════════════════════════════════════════════╝
  1. Telegram'da botingizga /start yozing
  2. "🛍️ Do'konni ochish" tugmasini bosing

  Mini App: $APP_URL
  API:      $API_URL
  Loglar:   $LOGS/   (bot.log, api.log, miniapp.log)

  Eslatma: tunnel manzillari har safar yangi bo'ladi — eski /start
  xabaridagi tugma ishlamaydi, /start ni qayta yuboring.
  To'xtatish: Ctrl+C
MSG
wait
