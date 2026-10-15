# Mrs Romol

Telegram Mini App orqali ishlaydigan onlayn do'kon. Reja va kelishuvlar: [docs/SPEC.md](docs/SPEC.md).

## Tuzilma

| Papka | Nima |
|---|---|
| `api/` | FastAPI backend — Mini App shu orqali ishlaydi |
| `bot/` + `main.py` | Telegram bot — `/start` va Mini App tugmasi |
| `miniapp/` | React Mini App (Vite + Tailwind) |
| `deploy/` | Caddy (HTTPS + Mini App + API proksi) |
| `db/` | Baza sxemasi (`schema.sql`), migratsiyalar va testlar |
| `tests/` | API testlari |
| `e2e/` | Demo do'kon (namuna mahsulotlar) va brauzerdagi to'liq xarid testi |
| `brand/` | Logotip va undan ikonkalar yasash skripti |

## Baza (Supabase)

1. supabase.com → yangi loyiha.
2. SQL Editor → `db/schema.sql` ni to'liq joylashtirib Run. Jadvallar, funksiyalar, xavfsizlik va bucketlar yaratiladi.
3. Project Settings → API Keys → **secret** kalitni `.env` dagi `SUPABASE_KEY` ga qo'ying. Publishable/anon kalit ishlamaydi: baza faqat backend'ga ochiq.

Mavjud bazani yangilash: `db/migrations/` dagi hali ishga tushirilmagan fayllarni tartib bilan SQL Editor'da Run qiling.

Testlar (Docker kerak):
- `bash db/tests/run.sh` — baza funksiyalari
- `bash tests/run.sh` — API boshdan-oxir (Postgres + PostgREST)
- `bash e2e/demo_stack.sh` — namuna mahsulotlar bilan lokal demo do'kon; keyin `node e2e/walk.mjs` (xaridor) va `node e2e/walk_admin.mjs` (admin) brauzerda butun yo'lni o'tib, har bir sahifani skrinshot qiladi

## Lokal ishga tushirish

```bash
cp .env.example .env            # qiymatlarni to'ldiring (DEV_MODE=true lokal uchun)
uv sync

uv run uvicorn api.main:app --reload --port 8000   # API  → http://localhost:8000/docs
uv run python main.py                              # bot

cd miniapp && npm install && npm run dev           # Mini App → http://localhost:5173
```

Telegram ichida sinash (domensiz, vaqtinchalik HTTPS tunnel bilan):
- `bash test_telegram.sh` — demo mahsulotlar bilan
- `bash test_telegram.sh real` — sizning Supabase bazangiz bilan

Keyin botga `/start` yozib, "Do'konni ochish" ni bosing. Ctrl+C — to'xtatish.

## VPS'ga deploy (Docker)

1. Domen DNS'ida ikkita A-yozuv VPS IP'siga: `APP_DOMAIN` (masalan `app.misrromol.uz`) va `API_DOMAIN` (`api.misrromol.uz`).
2. VPS'da Docker o'rnatilgan bo'lsin, proyektni ko'chiring va `.env` ni to'ldiring:
   - `APP_DOMAIN`, `API_DOMAIN`
   - `MINI_APP_URL=https://<APP_DOMAIN>`, `ALLOWED_ORIGINS=https://<APP_DOMAIN>`
   - `SUPER_ADMIN_IDS` — do'kon egasining Telegram ID'si (admin bo'limiga kirish uchun)
   - `DEV_MODE=false`
3. Ishga tushirish:
   ```bash
   docker compose up -d --build
   docker compose logs -f          # loglar
   ```
4. BotFather → `/mybots` → bot → *Bot Settings* → *Menu Button* / *Configure Mini App* → `https://<APP_DOMAIN>`.

Yangilash: `git pull && docker compose up -d --build`.
