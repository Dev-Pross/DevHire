-- Add missing columns to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_data JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS "isConnected" BOOLEAN DEFAULT false;

-- Note: resume_url already exists in the production schema.
-- applied_jobs (ARRAY), linkedin_context (json), and context_updated_at also exist.

-- Create table for tracking background jobs (Worker state)
CREATE TABLE workflow_sessions (
  id               UUID PRIMARY KEY,  -- Client-generated idempotency key
  user_id          UUID NOT NULL REFERENCES users(id),
  workflow_type    VARCHAR(20) NOT NULL 
    CHECK (workflow_type IN ('fetch_jobs', 'apply_jobs')),
  status           VARCHAR(20) NOT NULL DEFAULT 'pending' 
    CHECK (status IN ('pending', 'running', 'scraper_raw', 'completed', 'failed')),
  input_data       JSONB,       -- Request payload
  output_data      JSONB,       -- Pipeline state (overwritten by agents)
  last_active_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RATE LIMIT: 1 active job per user. Returns 429 if violated.
CREATE UNIQUE INDEX one_active_job_per_user 
ON workflow_sessions (user_id) 
WHERE status IN ('pending', 'running', 'scraper_raw');
