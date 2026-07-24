# HireHawk – Complete Technical Architecture & Application Flow

This document provides a comprehensive, step-by-step breakdown of the HireHawk technical architecture, component responsibilities, data flow, and exact technology stack used at each step.

---

## 🏛 System Architecture & Service Topology

HireHawk is composed of four primary system tiers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    1. Frontend Tier (Next.js 15 App Router)              │
│  • React 19, TypeScript, Tailwind CSS 4                                 │
│  • Client-side State: React Context (UserContext)                        │
│  • Local Persistent Cache: IndexedDB (jobStorage.ts)                     │
│  • Real-time Stream Client: SSEManager (EventSource API)                 │
│  • Auth Framework: NextAuth / Supabase Auth                              │
│  • DB Access Layer: Prisma ORM (queries PostgreSQL User & sessions)     │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
               ┌───────────────────┴───────────────────┐
               ▼                                       ▼
┌─────────────────────────────┐        ┌───────────────────────────────────┐
│  2. Remote Webcast Server   │        │ 3. Control Plane API (Python)     │
│  (Node.js / Express / WS)   │        │ (FastAPI + Uvicorn)               │
│  • Playwright Stealth + CDP │        │ • /api/jobs/* (Orchestration)    │
│  • Canvas JPEG Screencast   │        │ • /api/linkedin/connect-token     │
│  • Mouse/Touch/Keyboard WS  │        │ • /tailor (LaTeX Resume Engine)   │
│  • Saves session context    │        │ • /portfolio (HTML Generator)     │
│    to PostgreSQL            │        │ • Redis Queue & SSE Producer      │
└─────────────────────────────┘        └───────────────────────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               4. Asynchronous Worker Tier (worker.py)                   │
│  • Infrastructure: GCP Cloud Run Jobs (Prod) / Subprocess (Dev)         │
│  • Heartbeat Monitor: 10s Redis TTL Keep-alive                          │
│  • Queue Locks: dummy_account_lock (1800s) + Upstash QStash (25-45s)    │
│  • AI Execution Engine:                                                 │
│     - Parser Agent: PyMuPDF + pytesseract + Gemini 2.5 Flash Lite       │
│     - Scraper Agent: Playwright + Gemini 2.5 Flash / 3 Flash Preview     │
│     - Apply Agent: Playwright Stealth + Groq (gpt-oss-120b)              │
│     - Tailor Agent: Jinja2 LaTeX Templates + Gemini AI                  │
│     - Portfolio Agent: Groq (gpt-oss-120b) HTML/CSS Generator           │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   5. Data & Message Infrastructure                      │
│  • Database: PostgreSQL (Supabase) – Users, workflow_sessions           │
│  • Cache & Streams: Redis (Upstash) – SSE logs, queues, locks           │
│  • Delay Trigger: QStash – Webhook worker queue auto-dispatch          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Application Flow (Step-by-Step)

### 1. User Authentication & Credit Verification

- **Tech Used**: Next.js 15, NextAuth / Supabase Auth, Prisma ORM, PostgreSQL.
- **Process**:
1. User accesses the HireHawk dashboard.
2. Next.js verifies the JWT session via `middleware.ts` and `UserContext`.
3. Before triggering any task, Next.js queries PostgreSQL via Prisma to verify user credits:
- `fetch_jobs_credits` (Free tier default: 2 per reset window).
- `shared_generation_credits` (Free tier default: 5 per reset window).
- `tier` (`FREE` vs `PRO`).

---

### 2. Jobs Server Webcast Connection Flow (PRO Tier Dedicated Session)

- **Tech Used**: Next.js, Node.js (`auth-server`), Playwright Stealth, Chrome DevTools Protocol (CDP), WebSockets (`ws`), ioredis, PostgreSQL.
- **Process**:
1. User clicks "Connect Account" in the frontend.
2. Next.js calls `POST /connect-token` on the Python FastAPI backend.
3. Python API stores a short-lived stream token in Redis (`stream_token:{token}`) with 5-minute TTL and returns the Auth Server WebSocket URL.
4. Frontend navigates to `/connect?token=...` and opens a WebSocket connection to the Node.js Auth Server.
5. The Node.js Auth Server:
- Validates the token against Redis.
- Spawns an isolated Playwright Chromium instance with `stealth` plugin enabled.
- Attaches a CDP session (`Page.startScreencast`) to stream JPEG frames over the WebSocket to the HTML5 Canvas in the browser.
- Captures mouse clicks, touch taps, keyboard presses, and scroll events from the Canvas and dispatches them as native CDP input events.
- Dynamically intercepts OAuth popups when user logs in via third-party providers.
6. Upon detecting successful login (redirection to platform home/feed page):
- Saves the session JSON into PostgreSQL and updates `isConnected = true`.
- Deletes Redis stream tokens and safely terminates the browser instance.

---

### 3. Job Search & Scraping Pipeline (`fetch_jobs`)

- **Tech Used**: Python FastAPI, `worker.py`, `parse_agent.py`, `scraper_agent.py`, Shared PDF Utility (`pdf_utils.py` using PyMuPDF `fitz` + built-in Tesseract OCR `get_textpage_ocr`), Google Gemini AI (`2.5-flash-lite`, `2.5-flash`, `3-flash-preview`), Playwright Async, Redis Stream, IndexedDB.
- **Process**:
1. User initiates job discovery from the dashboard (providing resume URL / keywords).
2. Next.js sends `POST /api/jobs/start` with `workflow_type: "fetch_jobs"`.
3. Python FastAPI creates a `workflow_sessions` entry in PostgreSQL with status `pending`.
4. **Dispatch & Queue Lock Logic**:
- **PRO Tier**: Instantly triggers GCP Cloud Run Job (or subprocess in dev) with `JOB_ID`. Uses user's own connected context.
- **FREE Tier**: Pushes `job_id` to Redis `free_users_queue`. Uses a shared dummy search account protected by a Redis `dummy_account_lock` with an **1800-second (30-minute) TTL** to prevent concurrent access. Upon completion, `worker.py` releases the lock and schedules an Upstash **QStash** delayed webhook (`/api/jobs/trigger-next-queue`) with a **25-45 second random delay** for the next job in line.
5. **Worker Execution (`worker.py`)**:
- Spawns background thread emitting worker heartbeats (`worker_heartbeat:{job_id}`) to Redis every 10s.
- **Step 3A (Parse Agent)**: Uses shared `pdf_utils.extract_pdf_text_from_url()` to extract text and spatial hyperlinks via PyMuPDF (`fitz`), utilizing PyMuPDF's built-in Tesseract OCR (`get_textpage_ocr`) if no raw text layer is present. Sends text to Gemini `gemini-2.5-flash-lite` to extract candidate name, job titles, experience, skills, location, and notice period.
- **Step 3B (Scraper Agent)**: Launches Playwright browser (using user's session state if PRO, or shared account if FREE). Searches job platform using extracted titles and location filters. Extracts job cards, normalizes job URLs, fetches full job descriptions, and uses Gemini `gemini-2.5-flash` / `gemini-3-flash-preview` to rank and parse requirements.
6. As jobs are discovered, worker pushes events to Redis stream `stream:{job_id}` and updates PostgreSQL `workflow_sessions.output_data`.
7. Next.js frontend consumes SSE stream via `/api/jobs/stream?job_id=...` and saves fetched jobs into local **IndexedDB** (`jobStorage.ts`).

---

### 4. Automated Job Application Pipeline (`apply_jobs`)

- **Tech Used**: Python FastAPI, `worker.py`, `apply_agent.py`, `tailor.py`, Playwright Stealth, Groq AI (`openai/gpt-oss-120b`), Redis Stream, IndexedDB.
- **Access Restrictions**:
  - **FREE Tier Users are Prohibited**: Auto-applying is strictly restricted to **PRO** users with an active connected session (`tier == "PRO"` and `isConnected == true`). FREE tier users are blocked at the API level (`/api/jobs/start`) and cannot invoke this route.
- **Process**:
1. PRO User selects target jobs on the frontend dashboard and clicks "Apply".
2. Next.js initializes local IndexedDB progress tracking (`initApplyProgress`) and calls `POST /api/jobs/start` with `workflow_type: "apply_jobs"`.
3. **Phase 1: In-Line Resume Tailoring Producer (`tailor_producer`)**:
   - Before applying, `apply_agent.py` launches a background producer task (`tailor_producer()`).
   - It calls `agents.tailor.process_batch()` to generate custom, job-specific tailored resumes in batches for the target jobs using Gemini AI and Jinja2 LaTeX templates.
4. **Phase 2: Automated Form Submission (`EasyApplyAgent`)**:
   - Playwright opens target job page using the user's dedicated session context.
   - Detects "Easy Apply" button and uploads the job-specific tailored resume generated in Phase 1.
   - Iterates through multi-step application forms (contact info, screening questions).
   - Custom screening questions (e.g. "How many years of experience do you have with React?", "Are you comfortable working in Hyderabad?") are passed to **Groq LLM (`openai/gpt-oss-120b`)** which computes exact numerical/text answers based on candidate profile data.
   - Form is submitted, and status (`applied` or `failed`) is appended to `workflow_sessions.output_data` in PostgreSQL.
5. Real-time updates are streamed via SSE to Next.js, updating UI progress bars and IndexedDB records.

---

### 5. Resume Tailoring Engine (`/tailor`)

- **Tech Used**: Python FastAPI, `tailor.py`, PyMuPDF, Google Gemini AI, Jinja2 LaTeX Templates (`Resume0.tex.jinja` – `Resume3.tex.jinja`), External LaTeX Compiler (`pdflatex`).
- **Process**:
1. User requests tailored resume for a specific job description.
2. Next.js calls `POST /tailor` with `job_desc`, `resume_url`, and selected `template` ID (0 to 3).
3. Python backend downloads candidate PDF, extracts text, and sends job description + candidate experience to Gemini AI.
4. Gemini rewrites bullet points, highlights matching tech keywords, and outputs structured LaTeX-escaped JSON.
5. Jinja2 renders the LaTeX template (`ResumeX.tex.jinja`) with tailored data.
6. Backend compiles LaTeX into a clean PDF document, encodes it to base64, and returns it to Next.js for instant preview and download.

---

### 6. AI Portfolio Generator (`/portfolio`)

- **Tech Used**: Python FastAPI, `portfolio_agent.py`, Groq AI (`openai/gpt-oss-120b`).
- **Process**:
1. User requests AI portfolio generation from candidate profile.
2. Next.js calls `POST /portfolio` with `resume_url` and selected portfolio format ID.
3. Python backend parses candidate profile and invokes **Groq (`openai/gpt-oss-120b`)** with explicit system instructions to generate pure, responsive, production-ready HTML/CSS (no external dependencies, pure CSS grid/flexbox styling).
4. Returns raw HTML string to frontend for live iframe preview or one-click export.

---

## 🛠 Tech Stack Matrix by Application Step

| Application Step | Primary Technologies | Purpose |
| --- | --- | --- |
| **1. UI & State** | Next.js 15, React 19, Tailwind CSS, TypeScript, IndexedDB | Responsive dashboard, job selection, local result caching |
| **2. Auth & Credits** | NextAuth / Supabase Auth, Prisma ORM, PostgreSQL | User identity, session JWTs, credit enforcement |
| **3. Webcast Connection** | Node.js, Express, WebSockets (`ws`), Playwright Stealth, CDP | High-fidelity remote browser login stream & session extraction |
| **4. Orchestration** | FastAPI, Redis Streams, sse-starlette, Upstash QStash | API control plane, SSE events, queue delay triggers |
| **5. Async Worker** | GCP Cloud Run Jobs, Python `worker.py`, Redis Heartbeats | Multi-tier worker dispatch, state tracking |
| **6. Resume Parser** | PyMuPDF (`fitz`), pdf2image, pytesseract, Gemini 2.5 Flash Lite | Text extraction & structured candidate schema generation |
| **7. Job Scraper** | Playwright Async, Gemini 2.5 Flash / 3 Flash Preview | Web scraping, job card extraction, requirement ranking |
| **8. Auto-Applier** | Playwright Stealth, Groq (`openai/gpt-oss-120b`) | Form navigation, AI question answering, submission |
| **9. Resume Tailor** | Jinja2, LaTeX (`pdflatex`), PyMuPDF, Gemini AI | AI-driven resume bullet tailoring & PDF compilation |
| **10. Portfolio Generator** | Groq (`openai/gpt-oss-120b`) | Automatic single-file responsive HTML/CSS website generation |