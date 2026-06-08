-- ============================================================
-- Migration 001: Tables PWA + ajustements existantes
-- ============================================================

-- 1. Ajout colonnes à la table users existante
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS password_hash text,
  ADD COLUMN IF NOT EXISTS onboarding_completed boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS badge_count int DEFAULT 0;

-- 2. Ajout colonne à chat_sessions (remplace session_summary text par summary_json jsonb)
ALTER TABLE chat_sessions
  ADD COLUMN IF NOT EXISTS summary_json jsonb,
  ADD COLUMN IF NOT EXISTS date date DEFAULT CURRENT_DATE;

-- 3. Ajout colonne à chat_messages (le défaut est géré par l'application)
ALTER TABLE chat_messages
  ADD COLUMN IF NOT EXISTS expires_at timestamptz;

-- 4. Nouvelle table: athlete_models
CREATE TABLE IF NOT EXISTS athlete_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  model_json jsonb NOT NULL DEFAULT '{}',
  version int NOT NULL DEFAULT 1,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT unique_version UNIQUE(user_id, version)
);

CREATE INDEX idx_athlete_models_user ON athlete_models(user_id, created_at DESC);

-- 5. Nouvelle table: daily_summaries
CREATE TABLE IF NOT EXISTS daily_summaries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date date NOT NULL,
  summary_json jsonb NOT NULL DEFAULT '{}',
  nb_messages int DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT unique_day UNIQUE(user_id, date)
);

CREATE INDEX idx_daily_summaries_user_date ON daily_summaries(user_id, date DESC);

-- 6. Nouvelle table: weekly_rollups
CREATE TABLE IF NOT EXISTS weekly_rollups (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  week varchar(8) NOT NULL,
  rollup_json jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  CONSTRAINT unique_week UNIQUE(user_id, week)
);

-- 7. Nouvelle table: feedback
CREATE TABLE IF NOT EXISTS feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message_id uuid REFERENCES chat_messages(id) ON DELETE SET NULL,
  type varchar(20) NOT NULL CHECK (type IN ('like', 'dislike', 'bug')),
  detail text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_feedback_message ON feedback(message_id);
CREATE INDEX idx_feedback_type ON feedback(type);

-- 8. Nouvelle table: push_subscriptions
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint text NOT NULL,
  p256dh text NOT NULL,
  auth text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_push_subscriptions_user ON push_subscriptions(user_id);

-- 9. Vérification pgvector (doit déjà exister)
-- CREATE EXTENSION IF NOT EXISTS vector;
-- La table user_facts existe déjà avec colonne embedding vector(1536)

-- 10. Index pour la cleanup RGPD
CREATE INDEX idx_chat_messages_expires ON chat_messages(expires_at)
  WHERE expires_at IS NOT NULL;
