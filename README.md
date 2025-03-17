# webBot
A customer service chatbot for a particular website, Works with a RAG architecture, with knowledge base from the FAQ page of the chatbot



supabase SQL codes

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector; -- For embeddings
CREATE EXTENSION IF NOT EXISTS pg_net; -- For HTTP requests (optional)
CREATE EXTENSION IF NOT EXISTS pg_cron; -- For scheduled tasks (optional)

-- Create FAQ table
CREATE TABLE faq_knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL, -- 384-dimension embeddings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster similarity search
CREATE INDEX ON faq_knowledge_base USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create conversations table
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    faq_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create vector search function
CREATE OR REPLACE FUNCTION match_faq (
    query_embedding VECTOR(384),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id BIGINT,
    question TEXT,
    answer TEXT,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        id,
        question,
        answer,
        1 - (faq_knowledge_base.embedding <=> query_embedding) AS similarity
    FROM faq_knowledge_base
    WHERE 1 - (faq_knowledge_base.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- Add update trigger for FAQ table
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER faq_update_timestamp
BEFORE UPDATE ON faq_knowledge_base
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();



-- FAQ read policy
CREATE POLICY "Enable read access for all" 
ON faq_knowledge_base
FOR SELECT
TO public
USING (true);

-- Conversations insert policy
CREATE POLICY "Enable insert for all" 
ON conversations
FOR INSERT
TO public
WITH CHECK (true);