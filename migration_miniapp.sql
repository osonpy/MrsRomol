-- ══════════════════════════════════════════════════════════════════
-- migration_miniapp.sql
-- Run in Supabase SQL Editor before deploying Mini App
-- ══════════════════════════════════════════════════════════════════

-- Add metadata column for product colors/variants
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

-- Add is_wholesale flag for customers
ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS is_wholesale BOOLEAN NOT NULL DEFAULT FALSE;

-- Add address column to orders (separate from notes for cleaner querying)
-- Note: We store address inside notes as "address:...\n" prefix for backward compat.
-- This migration keeps schema minimal.

-- Example: set colors for existing products
-- UPDATE products SET metadata = '{"colors": ["Qizil", "Ko''k", "Yashil"]}' WHERE category = 'Ro''mollar';

-- Create Supabase Storage bucket for receipts
-- (Run this separately in Supabase Dashboard > Storage > New Bucket)
-- Bucket name: receipts
-- Public: true

COMMENT ON COLUMN products.metadata IS 'JSON metadata: {"colors": ["red", "blue"]}';
COMMENT ON COLUMN customers.is_wholesale IS 'If true, customer sees wholesale_price instead of sell_price';
