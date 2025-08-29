
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE uploaded_resume (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_url TEXT,
    experience INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    users_id UUID REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE parsed_title (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titles TEXT[],
    resume_id UUID REFERENCES uploaded_resume(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE scraped_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT,
    company TEXT,
    location TEXT,
    platform TEXT,
    job_url TEXT,
    job_desc TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parsed_title_has_scraped_jobs (
    title_id UUID REFERENCES parsed_title(id) ON DELETE CASCADE ON UPDATE CASCADE,
    jobs_id UUID REFERENCES scraped_jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (title_id, jobs_id)
);

CREATE TABLE tailored_resume (
    tailored_resume_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_url TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    jobs_id UUID REFERENCES scraped_jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    resume_id UUID REFERENCES uploaded_resume(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE job_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(45),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    jobs_id UUID REFERENCES scraped_jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    tailored_resume_id UUID REFERENCES tailored_resume(tailored_resume_id) ON DELETE CASCADE ON UPDATE CASCADE,
    users_id UUID REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    uploaded_resume_id UUID REFERENCES uploaded_resume(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE pipeline_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    current_stage VARCHAR(45),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_resume_id UUID REFERENCES uploaded_resume(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Optimized indexes based on expected query filters and joins
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_uploaded_resume_users_id ON uploaded_resume(users_id);
CREATE INDEX idx_uploaded_resume_created_at ON uploaded_resume(created_at);
CREATE INDEX idx_parsed_title_resume_id ON parsed_title(resume_id);
CREATE INDEX idx_parsed_title_titles ON parsed_title(titles);
CREATE INDEX idx_scraped_jobs_title_company ON scraped_jobs(title, company);
CREATE INDEX idx_scraped_jobs_created_at ON scraped_jobs(created_at);
CREATE INDEX idx_tailored_resume_jobs_id ON tailored_resume(jobs_id);
CREATE INDEX idx_tailored_resume_resume_id ON tailored_resume(resume_id);
CREATE INDEX idx_tailored_resume_generated_at ON tailored_resume(generated_at);
CREATE INDEX idx_job_applications_user_id ON job_applications(users_id);
CREATE INDEX idx_job_applications_resume_id ON job_applications(uploaded_resume_id);
CREATE INDEX idx_job_applications_status ON job_applications(status);
CREATE INDEX idx_job_applications_applied_at ON job_applications(applied_at);
CREATE INDEX idx_pipeline_uploaded_resume_id ON pipeline_progress(uploaded_resume_id);
CREATE INDEX idx_pipeline_stage ON pipeline_progress(current_stage);
