-- Minimal stand-in for what a Supabase project already has, so schema.sql
-- can be tested on plain Postgres (see db/tests/run.sh).
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema storage;
create table storage.buckets (
  id text primary key, name text not null, public boolean default false,
  file_size_limit bigint, allowed_mime_types text[]
);
