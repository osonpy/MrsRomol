# Misr Romol

Telegram Mini App orqali ishlaydigan onlayn do'kon. Reja va kelishuvlar: [docs/SPEC.md](docs/SPEC.md).

## Tuzilma

| Papka | Nima |
|---|---|
| `api/` | FastAPI backend — Mini App shu orqali ishlaydi |
| `bot/` + `main.py` | Telegram bot — `/start`, admin xabarnomalari va tasdiqlash tugmalari |
| `miniapp/` | React Mini App (Vite + Tailwind) |
| `deploy/` | Caddy (HTTPS + Mini App + API proksi) |
| `db/` | Baza sxemasi (`schema.sql`) va uning testlari |

## Baza (Supabase)

1. supabase.com → yangi loyiha.
2. SQL Editor → `db/schema.sql` ni to'liq joylashtirib Run. Jadvallar, funksiyalar, xavfsizlik va bucketlar yaratiladi.
3. Project Settings → API Keys → **secret** kalitni `.env` dagi `SUPABASE_KEY` ga qo'ying. Publishable/anon kalit ishlamaydi: baza faqat backend'ga ochiq.

Sxemani o'zgartirsangiz, testlarni ishga tushiring (Docker kerak): `bash db/tests/run.sh`

## Lokal ishga tushirish

```bash
cp .env.example .env            # qiymatlarni to'ldiring (DEV_MODE=true lokal uchun)
uv sync

uv run uvicorn api.main:app --reload --port 8000   # API  → http://localhost:8000/docs
uv run python main.py                              # bot

cd miniapp && npm install && npm run dev           # Mini App → http://localhost:5173
```

Telegram ichida sinash uchun: `bash test_telegram.sh` (Cloudflare tunnel ochadi).

## VPS'ga deploy (Docker)

1. Domen DNS'ida ikkita A-yozuv VPS IP'siga: `APP_DOMAIN` (masalan `app.misrromol.uz`) va `API_DOMAIN` (`api.misrromol.uz`).
2. VPS'da Docker o'rnatilgan bo'lsin, proyektni ko'chiring va `.env` ni to'ldiring:
   - `APP_DOMAIN`, `API_DOMAIN`
   - `MINI_APP_URL=https://<APP_DOMAIN>`, `ALLOWED_ORIGINS=https://<APP_DOMAIN>`
   - `ADMIN_SECRET_KEY` — kamida 32 belgili tasodifiy satr
   - `DEV_MODE=false`
3. Ishga tushirish:
   ```bash
   docker compose up -d --build
   docker compose logs -f          # loglar
   ```
4. BotFather → `/mybots` → bot → *Bot Settings* → *Menu Button* / *Configure Mini App* → `https://<APP_DOMAIN>`.

Yangilash: `git pull && docker compose up -d --build`.
