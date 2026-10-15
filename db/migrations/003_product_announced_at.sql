-- 003 — remember when a product was announced to subscribers (sent once).
-- For databases created from an earlier db/schema.sql. (New installs: schema.sql already has it.)
alter table products add column if not exists announced_at timestamptz;
