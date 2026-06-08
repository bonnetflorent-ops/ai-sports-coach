-- ============================================================
-- AI Sports Coach — Migrations combinées 001+002+003
-- À exécuter dans le SQL Editor de Supabase :
-- https://supabase.com/dashboard/project/qorxhwpoxcdxbnnlfjpp/sql
-- ============================================================

-- ════════════════════════════════════════════════════════════
-- PARTIE 1 : Tables PWA + ajustements existantes
-- ════════════════════════════════════════════════════════════

-- 1. Ajout colonnes à la table users existante
ALTER TABLE IF EXISTS users
  ADD COLUMN IF NOT EXISTS password_hash text,
  ADD COLUMN IF NOT EXISTS onboarding_completed boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS badge_count int DEFAULT 0;

-- 2. Ajout colonne à chat_sessions
ALTER TABLE IF EXISTS chat_sessions
  ADD COLUMN IF NOT EXISTS summary_json jsonb,
  ADD COLUMN IF NOT EXISTS date date DEFAULT CURRENT_DATE;

-- 3. Ajout colonne à chat_messages (le défaut est géré par l'application)
ALTER TABLE IF EXISTS chat_messages
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
CREATE INDEX IF NOT EXISTS idx_athlete_models_user ON athlete_models(user_id, created_at DESC);

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
CREATE INDEX IF NOT EXISTS idx_daily_summaries_user_date ON daily_summaries(user_id, date DESC);

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
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_message ON feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(type);

-- 8. Nouvelle table: push_subscriptions
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint text NOT NULL,
  p256dh text NOT NULL,
  auth text NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);

-- 9. Index pour la cleanup RGPD
CREATE INDEX IF NOT EXISTS idx_chat_messages_expires ON chat_messages(expires_at)
  WHERE expires_at IS NOT NULL;

-- ════════════════════════════════════════════════════════════
-- PARTIE 2 : Row Level Security
-- ════════════════════════════════════════════════════════════

ALTER TABLE IF EXISTS athlete_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS daily_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS weekly_rollups ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS push_subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS policies (IF NOT EXISTS n'existe pas pour les policies, on les drop d'abord)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_isolation_athlete_models') THEN
    CREATE POLICY "user_isolation_athlete_models" ON athlete_models
      FOR ALL USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
      WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_isolation_daily_summaries') THEN
    CREATE POLICY "user_isolation_daily_summaries" ON daily_summaries
      FOR ALL USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
      WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_isolation_weekly_rollups') THEN
    CREATE POLICY "user_isolation_weekly_rollups" ON weekly_rollups
      FOR ALL USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
      WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_manage_own_feedback') THEN
    CREATE POLICY "user_manage_own_feedback" ON feedback
      FOR ALL USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
      WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'user_isolation_push_subscriptions') THEN
    CREATE POLICY "user_isolation_push_subscriptions" ON push_subscriptions
      FOR ALL USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
      WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
  END IF;
END $$;

-- Cleanup function
CREATE OR REPLACE FUNCTION cleanup_expired_messages()
RETURNS integer AS $$
DECLARE
  deleted_count integer;
BEGIN
  DELETE FROM chat_messages WHERE expires_at < now();
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
