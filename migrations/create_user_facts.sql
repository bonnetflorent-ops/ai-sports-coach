-- Migration: Create user_facts table
-- Stores facts about users extracted from conversations, with vector embeddings for semantic search

CREATE TABLE IF NOT EXISTS user_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fact TEXT NOT NULL,
    category TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    source_session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_facts_user ON user_facts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_facts_category ON user_facts(category);

-- RLS policies
ALTER TABLE user_facts ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_facts_self ON user_facts
    FOR ALL
    USING (user_id IN (
        SELECT id FROM users WHERE telegram_id = (current_setting('request.jwt.claims')::json->>'sub')::bigint
    ));
