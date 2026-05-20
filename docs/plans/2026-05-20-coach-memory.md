# AI Sports Coach — Architecture mémoire 4 couches

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> **For subagents:** This is a Python 3.11 project with aiogram 3 + Supabase + DeepSeek V4.
> Every task uses TDD: write test → verify fail → implement → verify pass → commit.

**Goal:** Give the AI sports coach bot a multi-tier memory system — session memory, inter-session summaries, persistent facts with pgvector — so the coach remembers what was discussed and builds true personalized coaching over time.

**Architecture:**
- **Hot (Phase A):** Last 10 messages of current session injected directly into coach prompt
- **Warm (Phase B):** LLM-summarized session notes injected into next sessions
- **Warm (Phase C):** Structured facts extracted from conversations, stored with pgvector embeddings, top-5 semantically matched facts injected per message
- **Cold:** All facts in pgvector, queryable on demand

**Tech Stack:** Python 3.11, aiogram 3, Supabase (pgvector), DeepSeek V4 (coach) / DeepSeek Chat (cheap ops), Gemini Embedding 2 (768d)

---

## Phase A — Mémoire de session (hot)

The coach currently sees only the current user message. It needs the last 10 messages of the current session.

### Task A1: Add `get_session_messages()` to sessions.py

**Objective:** Create a function that returns full messages (not truncated) from the current session.

**Files:**
- Modify: `src/db/sessions.py` (add function)
- Test: `tests/db/test_sessions.py` (create)

**Spec:**
```python
def get_session_messages(session_id: str, limit: int = 10) -> list[dict]:
    """Returns full messages ordered chronologically, with role and content."""
```

Returns list of dicts with `{role, content, created_at}`. Uses `get_supabase_admin()`. SELECT role, content, created_at from chat_messages WHERE session_id = X ORDER BY created_at ASC LIMIT N.

No truncation. These will be injected into the prompt.

### Task A2: Inject session messages into coach prompt

**Objective:** Pass session messages to `build_system_prompt()` via the existing `coaching_context` parameter.

**Files:**
- Modify: `src/bot/handlers/chat.py` (around line 315)
- Modify: `src/engine/prompt_builder.py` (render messages block nicely)

**Spec:**
In `chat.py`, after step 4 (build_system_prompt), call `get_session_messages(session["id"], limit=10)` and format them into a string:
```
CONVERSATION EN COURS :
[user] J'ai fait 2h de Z2 hier
[assistant] Super, comment te sens-tu aujourd'hui ?
[user] Les jambes lourdes
```

Pass this string as `coaching_context` to `build_system_prompt()`.

In `prompt_builder.py`, the `coaching_context` parameter already exists. Replace the generic `HISTORIQUE DE COACHING` label with `CONTEXTE DE COACHING :` and place it between the profile and the knowledge blocks so the coach sees it early.

The message format in the prompt should be clear: `[user] message` / `[assistant] message`.

---

## Phase B — Résumés inter-sessions (warm)

At session end, cheap LLM summarizes. Next session injects last 3 summaries.

### Task B1: Add `session_summary` column to `chat_sessions`

**Objective:** DB migration to add the column.

**Files:**
- Create: `migrations/add_session_summary.sql`

**Spec:**
```sql
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS session_summary TEXT;
```

Execute via Supabase Management API (use curl pattern from skill).

### Task B2: Add `summarize_session()` to sessions.py

**Objective:** Generate a 300-500 char session summary using deepseek-chat.

**Files:**
- Modify: `src/db/sessions.py` (add function)
- Test: `tests/db/test_session_summary.py` (create)

**Spec:**
```python
def summarize_session(session_id: str) -> str:
    """
    Summarizes a session using deepseek-chat (cheap).
    Returns the summary string, saves to session_summary column.
    Called asynchronously at session end (no user waiting for it).
    """
```

Steps:
1. Fetch all messages from the session (or last 30)
2. Call deepseek-chat with a summarization prompt
3. Save summary to `chat_sessions.session_summary`
4. Return the summary string

Use the direct client pattern from `llm.py` for the cheap model: `model="deepseek/deepseek-chat"`, `max_tokens=200`, prompt asking for a 3-5 bullet summary in French covering: what was discussed, decisions made, facts mentioned, follow-ups.

### Task B3: Add `get_recent_summaries()` to sessions.py

**Objective:** Fetch the last 3 session summaries for a user.

**Files:**
- Modify: `src/db/sessions.py` (add function)

**Spec:**
```python
def get_recent_summaries(telegram_id: int, limit: int = 3) -> list[str]:
    """Returns summaries of the last N completed sessions (excluding current)."""
```

Query `chat_sessions` WHERE user_id matches, ended_at IS NOT NULL, session_summary IS NOT NULL, ORDER BY ended_at DESC LIMIT N.

### Task B4: Inject summaries into coach prompt

**Objective:** At session start or new session creation, inject recent summaries.

**Files:**
- Modify: `src/bot/handlers/chat.py` (around the session/profile loading area)

**Spec:**
After loading the active session, fetch recent summaries and append them to the `coaching_context` string (before session messages):
```
SESSIONS PRÉCÉDENTES :
SESSION 19/05: Florent a rapporté une douleur au psoas droit...
SESSION 18/05: Discussion sur la planification de la semaine...
```

### Task B5: Call `summarize_session()` at session end

**Objective:** Auto-summarize when a session ends (24h timeout).

**Files:**
- Modify: `src/db/sessions.py` — `get_or_create_active_session()`

**Spec:**
When `get_or_create_active_session()` detects the previous session is expired (>24h), before creating a new one:
1. Check if the old session has no summary yet
2. If messages exist (message_count > 0), call `summarize_session(old_session["id"])` asynchronously.
3. Wrap in try/except so summarization failure doesn't block the bot.

Use `asyncio.to_thread()` for the blocking DB call + LLM call inside.

---

## Phase C — Faits persistants + pgvector (warm/cold)

Extract structured facts from conversations. Store with embeddings. Semantic retrieval.

### Task C1: Create `user_facts` table

**Objective:** DB migration for the facts table.

**Files:**
- Create: `migrations/create_user_facts.sql`

**Spec:**
```sql
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
CREATE INDEX idx_user_facts_user ON user_facts(user_id);
CREATE INDEX idx_user_facts_category ON user_facts(category);
-- Index IVFFlat for similarity search (created after data exists)
```

Execute via Supabase Management API.

Add RLS policy: user sees only their own facts.

### Task C2: Create `src/db/facts.py` — CRUD

**Objective:** Database layer for facts.

**Files:**
- Create: `src/db/facts.py`
- Test: `tests/db/test_facts.py` (create)

**Spec:**
```python
def add_fact(user_id: str, fact: str, category: str, importance: float = 0.5,
             source_session_id: str = None, embedding: list[float] = None) -> dict:
    """Insert a new fact."""

def get_facts_by_user(user_id: str, limit: int = 50) -> list[dict]:
    """Get all facts for a user, ordered by importance DESC."""

def get_relevant_facts(user_id: str, query_embedding: list[float], limit: int = 5) -> list[dict]:
    """Get top-N facts by cosine similarity. Uses pgvector <=> operator."""

def deduplicate_facts(user_id: str, new_fact: str, threshold: float = 0.85) -> bool:
    """Check if a similar fact already exists. Return True if duplicate found."""

def update_fact(fact_id: str, updates: dict) -> dict:
    """Update an existing fact (importance bump, etc.)."""
```

All functions use `get_supabase_admin()`. The similarity query uses: `embedding <=> query_embedding AS distance`.

### Task C3: Add `embed_fact()` to `src/engine/embeddings.py`

**Objective:** Create embeddings for facts using Gemini.

**Files:**
- Create: `src/engine/embeddings.py`
- Test: `tests/engine/test_embeddings.py` (create)

**Spec:**
```python
def embed_text(text: str) -> list[float]:
    """
    Generate a 768d embedding using Gemini Embedding 2.
    Returns a list of 768 floats.
    """
```

Use the OpenAI-compatible interface since Gemini Embedding is accessible via OpenRouter or direct Google API. Check if there's already a Google API key configured. If not, use OpenRouter's Gemini embedding endpoint.

### Task C4: Add `extract_facts()` to `src/engine/fact_extractor.py`

**Objective:** Extract structured facts from conversation using deepseek-chat.

**Files:**
- Create: `src/engine/fact_extractor.py`
- Test: `tests/engine/test_fact_extractor.py` (create)

**Spec:**
```python
def extract_facts_from_messages(messages: list[dict]) -> list[dict]:
    """
    Extract structured facts from a batch of chat messages.
    Uses deepseek-chat (cheap). Returns list of {fact, category, importance}.
    
    Categories: entraînement, blessure, objectif, préférence, nutrition, 
                historique, équipement, récupération, autre
    
    Called every 5-10 messages, batched.
    """
```

The LLM prompt asks to extract 3-7 distinct facts in JSON format. Each fact has:
- `fact`: concise statement (max 150 chars) — "Florent court 3×/semaine (~35km/semaine)"
- `category`: one of the categories above
- `importance`: 0.1-1.0 (1.0 = critical like injury, goal, FTP; 0.3 = minor like preference)

The function should handle the JSON parsing and validation.

### Task C5: Integrate fact extraction into chat flow

**Objective:** Trigger fact extraction in the background after each message batch.

**Files:**
- Modify: `src/bot/handlers/chat.py`

**Spec:**
After saving messages (step 6 in the flow), if message_count % 5 == 0:
1. Fetch the session messages (last 10-20)
2. Call `extract_facts_from_messages()` asynchronously (in a background task)
3. For each extracted fact:
   a. Generate embedding with `embed_text()`
   b. Check for duplicates with `deduplicate_facts()`
   c. If not duplicate, `add_fact()`
   d. If duplicate (score > 0.85), bump importance of existing fact

Wrap in try/except — fact extraction failure should NEVER block the bot.

### Task C6: Inject relevant facts into coach prompt

**Objective:** At each message, find the top-5 semantically matching facts and inject them.

**Files:**
- Modify: `src/bot/handlers/chat.py` (after loading profile, before building prompt)

**Spec:**
After selecting concepts, before building the system prompt:
1. Get user message text
2. Generate embedding for the message using `embed_text()`
3. Call `get_relevant_facts(user_id, embedding, limit=5)`
4. Format facts as a string:
```
FAITS CONNUS SUR L'ATHLÈTE :
- Court 3×/semaine, ~35 km au total   [entraînement]
- Douleur psoas droit depuis 15 mai, en amélioration   [blessure]
- Objectif : semi-marathon Paris, octobre 2026   [objectif]
```
5. Append to `coaching_context`

If no facts exist yet, skip (empty string).

---

## Phase D — Assemblage final

### Task D1: Update `build_system_prompt` to merge all context layers

**Objective:** Refactor prompt builder to cleanly assemble all memory layers.

**Files:**
- Modify: `src/engine/prompt_builder.py`

**Spec:**
Update `build_system_prompt()` to accept a single `coaching_context` string that already contains all layers (session messages + summaries + facts) properly formatted. The caller (`chat.py`) is responsible for assembling them in the right order:

1. SESSIONS PRÉCÉDENTES (summaries)
2. FAITS CONNUS (relevant facts)
3. CONVERSATION EN COURS (session messages)

The prompt builder should render this block right after the profile and before knowledge:
```
{profile_block}

CONTEXTE DE COACHING :
{coaching_context}

CONNAISSANCES SCIENTIFIQUES PERTINENTES :
{knowledge_blocks}
```

This ensures the coach sees who they're coaching → what they know about them → then the scientific knowledge.

### Task D2: Run full test suite and verify

**Objective:** Ensure everything works together.

Run: `cd /root/ai-sports-coach && python3.11 -m pytest tests/ -v --tb=short`

All existing tests must pass. New tests must pass.

### Task D3: Deploy and verify

**Objective:** Rebuild Docker and verify the bot starts.

Run: `docker compose up -d --build`
Check: `docker logs ai-sports-coach-bot-1 --tail 20`
Verify: `bot_started` log entry.
