-- pgvector similarity search function for user_facts
CREATE OR REPLACE FUNCTION match_user_facts(
    query_embedding VECTOR(768),
    match_user_id UUID,
    match_limit INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    fact TEXT,
    category TEXT,
    importance REAL,
    source_session_id UUID,
    created_at TIMESTAMPTZ,
    distance FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        uf.id,
        uf.user_id,
        uf.fact,
        uf.category,
        uf.importance,
        uf.source_session_id,
        uf.created_at,
        uf.embedding <=> query_embedding AS distance
    FROM user_facts uf
    WHERE uf.user_id = match_user_id
    ORDER BY uf.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$;
