-- Migration: Add session_summary column to chat_sessions
-- Enables storing AI-generated session summaries for memory/personalization

ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS session_summary TEXT;
