-- ============================================================
-- Migration 002: Row Level Security
-- ============================================================

-- Helper: enable RLS on all new tables
ALTER TABLE athlete_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_rollups ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

-- athlete_models: user isolation
CREATE POLICY "user_isolation_athlete_models" ON athlete_models
  FOR ALL
  USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
  WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- daily_summaries: user isolation
CREATE POLICY "user_isolation_daily_summaries" ON daily_summaries
  FOR ALL
  USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
  WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- weekly_rollups: user isolation
CREATE POLICY "user_isolation_weekly_rollups" ON weekly_rollups
  FOR ALL
  USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
  WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- feedback: user can insert/read own, admin can read all
CREATE POLICY "user_manage_own_feedback" ON feedback
  FOR ALL
  USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
  WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- push_subscriptions: user isolation
CREATE POLICY "user_isolation_push_subscriptions" ON push_subscriptions
  FOR ALL
  USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid)
  WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- Cleanup function: delete expired messages (run nightly)
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
