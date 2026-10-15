-- 004 — delivery details the customer sees (taxi driver, car, Yandex tracking link…).
-- For databases created from an earlier db/schema.sql. (New installs: schema.sql already has it.)
alter table orders add column if not exists delivery_info text not null default '';
