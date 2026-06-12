-- ============================================================
-- Migration 004: Colonnes manquantes pour l'onboarding PWA
-- ============================================================
-- La table users du schéma initial n'avait pas les colonnes
-- nécessaires pour stocker les données de l'onboarding PWA.

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS equipment TEXT,
  ADD COLUMN IF NOT EXISTS weekly_slots TEXT,
  ADD COLUMN IF NOT EXISTS onboarding_phase SMALLINT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS parq_responses JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS parq_any_yes BOOLEAN DEFAULT false;
