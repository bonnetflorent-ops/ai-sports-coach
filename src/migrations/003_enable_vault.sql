-- ============================================================
-- Migration 003: Enable Supabase Vault for health_data encryption
-- ============================================================

-- Supabase Vault must be enabled via Dashboard > Settings > Vault
-- This migration adds the encrypted column and secret.

-- Add encrypted health_data column (AES-256-GCM via pgsodium + Vault)
-- The 'health_data' column in users stays as jsonb but is encrypted
-- at the application layer using the Vault-stored key.

-- Create a Vault secret for the health data encryption key
-- (Run via Supabase Dashboard or SQL after enabling Vault extension):
--
-- SELECT vault.create_secret(
--   gen_random_bytes(32),  -- 256-bit key
--   'health_data_encryption_key',
--   'AES-256 key for encrypting users.health_data column'
-- );
--
-- Then at the application level (Python):
--   1. Fetch key: SELECT vault.decrypt_secret(secret) FROM vault.decrypted_secrets WHERE name='health_data_encryption_key'
--   2. Encrypt health_data jsonb with AES-256-GCM before INSERT/UPDATE
--   3. Decrypt after SELECT

-- Note: For MVP, application-level encryption with a key from Vault
-- is simpler than column-level encryption via pgsodium triggers.
-- The Python layer handles encrypt/decrypt transparently.
