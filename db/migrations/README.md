# Migrations

`db/schema.sql` is always the full, current schema — use it for a new database.

Files here bring an **existing** database up to date. Run each one you haven't
run yet, in number order (Supabase → SQL Editor → paste → Run).
001 is the original `schema.sql` itself.

| # | What |
|---|---|
| 002 | Apostrophe-insensitive product search (`products.search_text`) |
