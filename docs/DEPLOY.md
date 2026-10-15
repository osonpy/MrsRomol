# Deploy — VPS (Contabo)

Server: `deploy@161.97.107.145` · Domen: `mrsromol.uz` (Eskiz)
Loyiha papkasi (VPS): `~/apps/mrsromol_market_miniapp/mrsromol`
Do'kon: `https://app.mrsromol.uz` · API: `https://api.mrsromol.uz`

Do'kon 3 ta Docker konteynerda ishlaydi: `api`, `bot`, `caddy` (HTTPS + Mini App). Baza va
rasmlar Supabase'da. VPS'dagi boshqa botlarga tegmaydi; faqat 80 va 443 portlarni egallaydi.

## Birinchi o'rnatish

**0. Oldindan:** Eskiz → DNS: `app` va `api` uchun A-yozuv → `161.97.107.145`.
Supabase'da barcha migratsiyalar bajarilgan bo'lsin (`db/migrations/`).

**1. Kodni yuklash** (VPS'da):
```bash
mkdir -p ~/apps/mrsromol_market_miniapp && cd ~/apps/mrsromol_market_miniapp
git clone https://github.com/osonpy/MrsRomol.git mrsromol
cd mrsromol
```

**2. Sozlamalar** (o'z kompyuteringizda, yangi terminalda):
```bash
scp ~/MsrRomol/.env.production deploy@161.97.107.145:~/apps/mrsromol_market_miniapp/mrsromol/.env
```
Keyin VPS'da: `chmod 600 ~/apps/mrsromol_market_miniapp/mrsromol/.env`

**3. Firewall** (VPS'da):
```bash
sudo ufw status
```
Agar `Status: active` bo'lsa:
```bash
sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 443/udp
```

**4. DNS tayyorligini tekshirish** (VPS'da):
```bash
getent hosts app.mrsromol.uz api.mrsromol.uz
```
Ikkalasida ham `161.97.107.145` chiqishi kerak. Chiqmasa — kuting (DNS bir necha soatgacha).
Tashqaridan: `dig +short app.mrsromol.uz @8.8.8.8` yoki dnschecker.org. `.uz` reyestri yangi domenni
o'z zonasiga bir necha soatda qo'shadi; tekshirish: `dig NS mrsromol.uz @ns1.uz +norecurse`.

**5. Ishga tushirish** (VPS'da, loyiha papkasi ichida; birinchi marta 3–5 daqiqa):
```bash
docker compose up -d --build
docker compose ps
```

**6. Tekshirish:**
```bash
docker compose logs caddy | grep -i "certificate obtained"   # HTTPS sertifikat olindi (Let's Encrypt, avtomatik yangilanadi)
curl -s https://api.mrsromol.uz/health                       # {"status":"ok",...}
docker compose logs bot | tail -5                             # "Mrs Romol bot starting..."
```
Telegram'da botga `/start` → "Do'konni ochish".

> Bot bir vaqtda faqat bitta joyda ishlay oladi. Kompyuterda `test_telegram.sh` ishlab
> turgan bo'lsa — to'xtating (Ctrl+C).

## Kundalik ishlar

| Nima | Buyruq (`~/apps/mrsromol_market_miniapp/mrsromol` ichida) |
|---|---|
| Yangi versiyani o'rnatish | `git pull && docker compose up -d --build` |
| Holat | `docker compose ps` |
| Loglar | `docker compose logs -f api` (yoki `bot`, `caddy`) |
| Qayta ishga tushirish | `docker compose restart` |
| To'xtatish | `docker compose down` |
| Sozlamani o'zgartirish | `nano .env`, keyin `docker compose up -d` |
| Eski image'larni tozalash | `docker image prune -f` |

Baza yangilanishi kerak bo'lsa (yangi fayl `db/migrations/` da), uni **avval** Supabase SQL
Editor'da Run qiling, keyin `git pull && docker compose up -d --build`.
