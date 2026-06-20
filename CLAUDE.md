# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

DevHire automates LinkedIn job applications: parse a resume, scrape matching jobs, tailor a resume per
job (LaTeX→PDF), auto-apply via headless browser, and generate portfolio sites. Three deployables +
a Chrome extension, coordinated through one Postgres DB and Redis.

## Repository layout

- `my-fe/` — Next.js 15 (App Router) + React 19 + Tailwind v4 frontend. The user-facing app.
- `backend_python/` — Python FastAPI backend **and** the worker (same code, same Docker image).
- `extension/` — Chrome Manifest V3 extension that captures LinkedIn cookies/localStorage and POSTs them to the backend.
- `schema.sql` — canonical DDL for the `workflow_sessions` table + the per-user rate-limit index.
- Root `package.json` / `package-lock.json` are vestigial (axios, react-hot-toast). Real frontend deps live in `my-fe/`.

## Commands

**Frontend** (`cd my-fe`):
- `npm run dev` — dev server on :3000
- `npm run build` — runs `npx prisma generate` then `next build`
- `npm run lint` — eslint (`next lint`)
- `npx prisma generate` — regenerate Prisma client (required after editing `prisma/schema.prisma`)

**Backend** (`cd backend_python`):
- First-time setup: `bash run.sh` (Linux; creates `myenv`, installs deps + Playwright Chromium) or `run.bat` (Windows). README's manual path uses a `venv` instead — both are gitignored.
- Run the API: `python -m uvicorn main.main:app --reload --host 0.0.0.0 --port 8000`
- Run the worker by hand: `JOB_ID=<uuid> python worker.py` (needs a matching `workflow_sessions` row already in the DB).
- Docker entrypoint switches mode by env: `MODE=WORKER` runs `worker.py`, otherwise runs uvicorn.

**No test suite exists** in this repo — there is nothing to run for tests, and no test command.

## The core architecture: async job pattern

The single most important thing to understand. The FastAPI **API is stateless and short-lived**; all
long work (Playwright scraping, LLM calls, auto-apply) runs in a **separate Worker container**. They
never share memory — they coordinate through **Postgres (source of truth)** + **Redis (live progress)**.

Job lifecycle (`backend_python/main/routes/jobs_api.py` ↔ `backend_python/worker.py`):

1. Frontend `POST /api/jobs/start` with `{ user_id, workflow_type, input_data, job_id? }`. `workflow_type` ∈ `fetch_jobs` | `apply_jobs`. `user_id` may be an **email or a UUID** — the API resolves it to the internal `User.id`.
2. API inserts a `workflow_sessions` row (`status="pending"`) and calls `_trigger_worker(job_id)`:
   - `DEV_MODE=true` → spawns `python worker.py` as a **local subprocess** (use this for local dev — there is no Cloud Run locally).
   - production → triggers a **Cloud Run Job** (`WORKER_JOB_NAME`) passing `JOB_ID` as an env override.
3. API then **blocks up to 30s on a Redis "latch"**, waiting for the worker to push a `"started"` event into `stream:{job_id}`. Timeout → marks the row `failed`, returns 504.
4. Worker boots, reads its row by `JOB_ID`, flips `pending`→`running`, runs the pipeline, and pushes progress events to the Redis list `stream:{job_id}` while refreshing `worker_heartbeat:{job_id}` (60s TTL) on a background thread.
5. Frontend opens an SSE stream `GET /api/jobs/stream?job_id=` which tails the Redis list. `GET /api/jobs/status?job_id=` is the **DB fallback** when SSE drops or the user returns later.

`status` state machine: `pending → running → scraper_raw → completed | failed`. **`scraper_raw` is a
resumable checkpoint** — a worker can reattach and continue from it.

**Rate limit & reconnection:** the partial unique index `one_active_job_per_user` (see `schema.sql`)
enforces **one active job per user**; a second insert raises → API returns 429. `jobs_api.py` has
substantial reconnect/resume logic: if a client retries with an existing `job_id`, it decides between
*reattach* (worker still alive — heartbeat fresh) vs *resume* (heartbeat stale past `SESSION_STALE_SECONDS`,
re-trigger the worker). Touch this logic carefully.

**Redis is optional but degrading:** with no `REDIS_URL`, `redis_client` is `None` and **SSE progress
streaming silently no-ops** — only DB status polling works. The API still functions.

## Agents (`backend_python/agents/`)

Each agent picks its own LLM and model inline at the top of its file (model names drift — check the file).

- `scraper_agent.py` (`run_scraper_pipeline`) — **Gemini** + Playwright. Logs into LinkedIn, scrapes job listings, then bulk-parses raw HTML into structured jobs via batched LLM calls.
- `parse_agent.py` — **Gemini**. Resume PDF → job titles + skills (with OCR fallback for image PDFs).
- `tailor.py` (`process_batch`) — **Gemini** generates structured resume content → rendered into LaTeX via the Jinja templates in `agents/data_samples/Resume{0-3}.tex.jinja` → compiled to PDF. **LaTeX is compiled by remote HTTP LaTeX-as-a-service endpoints** (the `ENGINES` list / `compile_tex`), **not** a local `pdflatex` — no TeX install required.
- `apply_agent.py` (`run_apply_pipeline`) — **Groq** (`openai/gpt-oss-120b`) + Playwright. Fills and submits LinkedIn Easy Apply forms with the tailored resume.
- `portfolio_agent.py` (`generate_portfolio_main`) — **Groq**. Resume → HTML/CSS portfolio site (5 templates).

The worker routes `fetch_jobs`→scraper, `apply_jobs`→apply. Tailoring and portfolio generation are
**stateless synchronous routes** (`/tailor`, `/portfolio`), not part of the async worker pipeline.

**LinkedIn session persistence:** the extension's captured cookies/localStorage are stored as
`User.linkedin_context` (JSON) via `database/linkedin_context.py`, and reused by Playwright to skip
re-login. `config.LINKEDIN_CONTEXT_OPTIONS` pins user-agent/locale/timezone identical across contexts —
LinkedIn force-logs-out on mismatch, so keep these consistent.

## Data layer — one DB, two clients

A single Postgres database (Supabase-hosted), accessed two different ways:
- **Frontend → Prisma** (`my-fe/app/utiles/database.ts`, `prisma.user.*`) plus some raw `pg`.
- **Backend Python → supabase-py** (`supabase.table("User")`, `supabase.table("workflow_sessions")`).

The users table is named **`"User"`** (capitalized — Prisma `@@map("User")`). Schema source of truth is
split: `my-fe/prisma/schema.prisma` defines `User` + `workflow_sessions`; `schema.sql` holds the
hand-written `workflow_sessions` DDL and the rate-limit index. There is no tracked Prisma migrations dir.

## Frontend specifics (`my-fe/`)

- App Router under `app/`; path alias `@/` → `my-fe/` root. Components in `app/Components/`, shared logic in `app/utiles/`.
- **`UserContext`** (`app/utiles/UserContext.tsx`, `useUser()` hook) is the single source of truth for the logged-in user. Fetched **once** on app load via `/api/User`, backed up to `sessionStorage`. Components read from context — they do not re-fetch. Don't reintroduce polling.
- Backend base URL: `API_URL` from `app/utiles/api.ts` (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).
- **Live job flow uses `/api/jobs/start` + `/api/jobs/stream` + `/api/jobs/status`** (see `app/Components/Jobs.tsx`, `app/Components/Apply.tsx`). ⚠️ `app/utiles/agentsCall.ts` (which posts to `/get-jobs` and `/apply-jobs`) is **legacy/dead** — those endpoints no longer exist on the backend. Don't follow it.
- Auth: Supabase (`createPagesBrowserClient`, cookie `sb-*-auth-token`). `middleware.ts` gates `/Jobs/*` and `/apply` on the presence of that cookie only.

## Environment variables

**Backend** (`config.py`, loaded from `backend_python/.env` via dotenv — the README's "create a
`config.py` with hardcoded keys" instruction is **outdated**, config is env-driven):
`PROJECT_URL`, `SUPABASE_API`, `DATABASE_URL`, `GOOGLE_API`, `GROQ_API`, `LINKEDIN_ID`,
`LINKEDIN_PASSWORD`, `REDIS_URL`, `GCP_PROJECT_ID`, `GCP_REGION` (default `asia-south1`),
`WORKER_JOB_NAME` (default `devhire-worker`), `DEV_MODE`, `SESSION_STALE_SECONDS` (default 45).

**Frontend** (`.env.local`): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_PROJECT_URL`,
`NEXT_PUBLIC_SUPABASE_ANON_KEY`, `DATABASE_URL`, `JWT_SECRET`. ⚠️ The code reads
`NEXT_PUBLIC_PROJECT_URL` for the Supabase URL even though the README says `NEXT_PUBLIC_SUPABASE_URL` —
trust the code.
