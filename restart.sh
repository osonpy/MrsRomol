#!/bin/bash
# restart.sh — botni xavfsiz qayta ishga tushirish
# Foydalanish: bash restart.sh

echo "🛑 Eski bot instance'larini to'xtatmoqda..."
pkill -f "python main.py" 2>/dev/null
pkill -f "uv run python main.py" 2>/dev/null
sleep 1

echo "🤖 Bot ishga tushmoqda..."
cd "$(dirname "$0")"
uv run python main.py
