-- AI Sports Coach — Schéma initial
-- À exécuter dans le SQL Editor de Supabase (https://qorxhwpoxcdxbnnlfjpp.supabase.co)

-- Activer pgvector (pour embeddings Gemini + recherche sémantique future)
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- ============================================================
-- 1. USERS — Profils utilisateurs
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id   BIGINT UNIQUE NOT NULL,            -- ID Telegram unique
    first_name    TEXT,
    username      TEXT,                               -- @telegram_handle
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Profil sportif (onboarding)
    sport         TEXT,                               -- 'cycling', 'running', 'triathlon', 'fitness'
    level         SMALLINT DEFAULT 1,                 -- 1=débutant, 2=intermédiaire, 3=expert
    goal          TEXT,                               -- 'performance', 'perte_poids', 'sante', 'preparation_course'
    experience_years SMALLINT DEFAULT 0,

    -- Métriques d'entraînement (WKO-style)
    ftp_watts     INTEGER,                            -- Functional Threshold Power (cyclisme)
    vdot          REAL,                               -- VDOT (running)
    weight_kg     REAL,
    height_cm     REAL,
    age           SMALLINT,
    resting_hr    SMALLINT,                           -- FC repos

    -- Métriques de charge calculées (mises à jour périodiquement)
    ctl           REAL DEFAULT 0,                     -- Chronic Training Load
    atl           REAL DEFAULT 0,                     -- Acute Training Load
    tsb           REAL DEFAULT 0,                     -- Training Stress Balance

    -- Blessures / limitations
    injuries      TEXT,                               -- JSON: [{"type":"genou","date":"2024-01","status":"gueri"},...]
    limitations   TEXT,                               -- Texte libre

    -- Statut
    is_active     BOOLEAN NOT NULL DEFAULT true,
    is_premium    BOOLEAN NOT NULL DEFAULT false,     -- Abonnement payant
    premium_until TIMESTAMPTZ
);

CREATE INDEX idx_users_telegram ON users(telegram_id);
CREATE INDEX idx_users_sport   ON users(sport);
CREATE INDEX idx_users_active  ON users(is_active);

-- ============================================================
-- 2. CHAT_SESSIONS — Sessions de conversation
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at      TIMESTAMPTZ,
    topic         TEXT,                               -- Sujet principal détecté
    message_count INTEGER DEFAULT 0
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);

-- ============================================================
-- 3. CHAT_MESSAGES — Messages individuels
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content       TEXT NOT NULL,
    tokens_in     INTEGER DEFAULT 0,
    tokens_out    INTEGER DEFAULT 0,
    cost_eur      REAL DEFAULT 0,
    concepts_used TEXT[],                             -- IDs concepts injectés (ex: 'planification/gestion-charge')
    level_used    SMALLINT,                           -- Niveau de couche utilisé (1/2/3)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);

-- ============================================================
-- 4. KNOWLEDGE_BASE — Base de connaissances vectorielle (pgvector)
--    Pour le futur RAG — pas utilisé en MVP
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain        TEXT NOT NULL,                      -- 'physiologie', 'nutrition', etc.
    concept_id    TEXT NOT NULL UNIQUE,               -- 'domaine/slug-concept' (cf index.yaml)
    title         TEXT NOT NULL,
    level         SMALLINT NOT NULL CHECK (level BETWEEN 1 AND 3),
    content       TEXT NOT NULL,                      -- Markdown brut de la couche
    embedding     VECTOR(768),                        -- Gemini embedding 2 (768 dimensions)
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_kb_domain_level ON knowledge_base(domain, level);
CREATE INDEX idx_kb_concept ON knowledge_base(concept_id);
-- L'index vectoriel sera créé au moment de l'ingestion des données

-- ============================================================
-- ROW LEVEL SECURITY — Règles de base
-- ============================================================

-- Users : un utilisateur voit/modifie UNIQUEMENT son propre profil
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_self ON users
    FOR ALL
    USING (telegram_id = (current_setting('request.jwt.claims')::json->>'sub')::bigint)
    WITH CHECK (telegram_id = (current_setting('request.jwt.claims')::json->>'sub')::bigint);

-- Chat sessions : l'utilisateur voit UNIQUEMENT ses sessions
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY chat_sessions_self ON chat_sessions
    FOR ALL
    USING (user_id IN (
        SELECT id FROM users WHERE telegram_id = (current_setting('request.jwt.claims')::json->>'sub')::bigint
    ));

-- Chat messages : filtré via la session parente
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY chat_messages_self ON chat_messages
    FOR ALL
    USING (session_id IN (
        SELECT cs.id FROM chat_sessions cs
        JOIN users u ON cs.user_id = u.id
        WHERE u.telegram_id = (current_setting('request.jwt.claims')::json->>'sub')::bigint
    ));

-- Knowledge base : lecture publique, écriture admin uniquement
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
CREATE POLICY kb_read_all ON knowledge_base FOR SELECT USING (true);
