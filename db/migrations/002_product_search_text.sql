-- 002 — apostrophe-insensitive product search.
-- For databases created from an earlier db/schema.sql. (New installs: schema.sql already has it.)
-- Supabase Dashboard → SQL Editor → paste → Run.

alter table products add column if not exists search_text text generated always as (
  lower(translate(name_uz || ' ' || name_ru, $$'`ʻʼ‘’$$, ''))
) stored;
create index if not exists products_search_trgm on products using gin (search_text extensions.gin_trgm_ops);
drop index if exists products_name_uz_trgm;
drop index if exists products_name_ru_trgm;
