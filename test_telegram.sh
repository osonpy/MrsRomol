#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# test_telegram.sh — Mini App ni Telegram'da test qilish uchun
# ══════════════════════════════════════════════════════════════
set -e

CLOUDFLARED="$HOME/.local/bin/cloudflared"
LOG_DIR="$(dirname "$0")/.tunnel_logs"
mkdir -p "$LOG_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Misr Romol — Telegram Test Rejimi                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. FastAPI serverni background'da ishga tushir ────────────
echo "▶ FastAPI (port 8000) ishga tushmoqda..."
pkill -f "uvicorn api.main" 2>/dev/null || true
sleep 1
DEV_MODE=false uv run uvicorn api.main:app --port 8000 \
  > "$LOG_DIR/fastapi.log" 2>&1 &
FASTAPI_PID=$!
echo "  PID: $FASTAPI_PID"
sleep 2

# Health check
if ! curl -sf http://localhost:8000/health > /dev/null; then
  echo "❌ FastAPI ishga tushmadi! Log:"
  tail -20 "$LOG_DIR/fastapi.log"
  exit 1
fi
echo "  ✅ FastAPI OK → http://localhost:8000"

# ── 2. React dev serverni background'da ishga tushir ─────────
echo ""
echo "▶ React dev server (port 5173) ishga tushmoqda..."
pkill -f "vite --port 5173" 2>/dev/null || true
sleep 1
cd "$(dirname "$0")/miniapp"
source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
npm run dev -- --port 5173 \
  > "$LOG_DIR/react.log" 2>&1 &
REACT_PID=$!
cd "$(dirname "$0")"
sleep 3

if ! curl -sf http://localhost:5173 > /dev/null; then
  echo "❌ React server ishga tushmadi! Log:"
  tail -10 "$LOG_DIR/react.log"
  exit 1
fi
echo "  ✅ React OK → http://localhost:5173"

# ── 3. Cloudflared tunnellar (ikkita: API + Frontend) ─────────
echo ""
echo "▶ Cloudflare tunnel'lar ochilmoqda..."

# Frontend tunnel
$CLOUDFLARED tunnel --url http://localhost:5173 \
  --logfile "$LOG_DIR/tunnel_frontend.log" \
  --no-autoupdate \
  > "$LOG_DIR/tunnel_frontend_out.log" 2>&1 &
TUNNEL_FRONTEND_PID=$!

# API tunnel
$CLOUDFLARED tunnel --url http://localhost:8000 \
  --logfile "$LOG_DIR/tunnel_api.log" \
  --no-autoupdate \
  > "$LOG_DIR/tunnel_api_out.log" 2>&1 &
TUNNEL_API_PID=$!

echo "  Tunnel URL'lar yuklanmoqda (15 soniya)..."
sleep 15

# Extract tunnel URLs
FRONTEND_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_DIR/tunnel_frontend.log" 2>/dev/null | head -1)
API_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_DIR/tunnel_api.log" 2>/dev/null | head -1)

# Fallback: check stdout logs
if [ -z "$FRONTEND_URL" ]; then
  FRONTEND_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_DIR/tunnel_frontend_out.log" 2>/dev/null | head -1)
fi
if [ -z "$API_URL" ]; then
  API_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_DIR/tunnel_api_out.log" 2>/dev/null | head -1)
fi

if [ -z "$FRONTEND_URL" ] || [ -z "$API_URL" ]; then
  echo "❌ Tunnel URL topilmadi! Loglarni tekshiring:"
  echo "   cat $LOG_DIR/tunnel_frontend.log"
  echo "   cat $LOG_DIR/tunnel_api.log"
  echo ""
  echo "Qo'lda ishga tushirish:"
  echo "   $CLOUDFLARED tunnel --url http://localhost:5173"
  echo "   $CLOUDFLARED tunnel --url http://localhost:8000"
  # Don't exit — keep processes running
else
  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║  ✅ TUNNEL'LAR TAYYOR                                        ║"
  echo "╠══════════════════════════════════════════════════════════════╣"
  echo "║  🌐 Frontend: $FRONTEND_URL"
  echo "║  🔌 API:      $API_URL"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Keyin qo'lda .env yangilash kerak:"
  echo ""
  echo "  1. miniapp/.env:"
  echo "     VITE_API_URL=$API_URL"
  echo ""
  echo "  2. .env (FastAPI):"
  echo "     MINI_APP_URL=$FRONTEND_URL"
  echo "     ALLOWED_ORIGINS=$FRONTEND_URL"
  echo ""
  echo "  3. React'ni rebuild qiling:"
  echo "     cd miniapp && npm run build"
  echo ""
  echo "  4. BotFather'da Mini App URL:"
  echo "     /newapp → $FRONTEND_URL"
  echo "     yoki: /setmenubutton → $FRONTEND_URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo "  Barcha serverlarni to'xtatish uchun: Ctrl+C"
echo "  PIDs: FastAPI=$FASTAPI_PID React=$REACT_PID"
echo ""

# Keep running until Ctrl+C
trap "echo ''; echo 'Barcha serverlar to'xtatilmoqda...'; kill $FASTAPI_PID $REACT_PID $TUNNEL_FRONTEND_PID $TUNNEL_API_PID 2>/dev/null; exit 0" INT TERM
wait
