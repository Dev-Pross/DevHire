# HireHawk – AI-Powered Job Application Automation & Interactive Resume Studio

HireHawk is an advanced enterprise-grade platform designed to automate and personalize the end-to-end job search, resume engineering, and application process. Combining multi-agent LLM pipelines, stealth headless browser automation, and a real-time interactive LaTeX resume tailoring studio, HireHawk empowers candidates to apply smarter, faster, and with mathematically optimized ATS relevance.

---

## Technical Architecture & Core Subsystems

```
                                      +---------------------------------------------+
                                      |         Next.js 14+ Frontend (my-fe)        |
                                      |  (Tailwind CSS, App Router, Lucide, SSE)    |
                                      +----------------------+----------------------+
                                                             |
                                           HTTPS / WSS / SSE |
                                                             v
+---------------------------------------+   +----------------+----------------------+
|       Node.js Session Server          |   |       FastAPI Python Backend          |
|  (Headless Playwright Stealth Canvas, |   |   (Stateless Routes, LangGraph/Agents,|
|   Webcast Remote Auth, Cookie Vault)  |   |    Multi-Provider LLM Gateway)        |
+-------------------+-------------------+   +--------------------+------------------+
                    |                                            |
                    +--------------------+-----------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           Data & Distributed Infrastructure                       |
|   - Supabase PostgreSQL (Prisma ORM, JSONB Contexts, Workflow Sessions)           |
|   - Upstash Redis (SSE Event Streaming, Mutex Locks, Session Caching, Queues)     |
|   - Upstash QStash (Delayed Execution Queue for Free-Tier Throttling)             |
|   - Cloud Run (Stateless Container Workers for Instant Pro Execution)             |
|   - LLM Gateway (Gemini Multi-Key Pool, Groq Qwen/GPT Cascades, Strict JSON)      |
+-----------------------------------------------------------------------------------+
```

---

## How HireHawk Works (End-to-End Application Flow)

HireHawk operates through four coordinated subsystems:

### 1. User Onboarding & Authentication
- Secure authentication via **NextAuth / Supabase Auth** with PostgreSQL identity management.
- Dynamic tier calculation (**FREE** vs. **PRO**) and automated daily/periodic credit resets for job discovery, tailoring, and applications.

### 2. Stealth Connection Engine (Node.js Session Server)
- For automated job applications, users connect their LinkedIn / job board account securely.
- **PRO Users**: Spins up an isolated headless browser via Playwright stealth. The user interacts directly with the browser via a remote webcast canvas stream to authenticate.
- Session authentication state (`linkedin_context`) is safely stored in Supabase PostgreSQL as encrypted `JSONB` for background worker reuse.

### 3. Agentic Execution & Job Application (`worker.py` & `apply_agent.py`)
When a user launches a job search or application workflow, execution adapts to their subscription tier:
- **PRO Tier (Instant Execution)**: Dispatched immediately to dedicated **GCP Cloud Run** worker containers using their saved `linkedin_context`.
- **FREE Tier (Queued Execution)**: Enqueued in **Redis** with **QStash** delayed triggers (25–45s jitter between submissions). Shared execution accounts use a 30-minute Redis mutex lock to strictly respect platform rate limits and soft daily caps (`daily_apply_count`).
- **Resilient Multi-Agent Pipeline**: Automatically answers application form fields, selects work authorizations, matches technologies via a local skills ontology, and uploads tailored vector PDFs with fallback to master resumes on provider timeouts.

### 4. Interactive Section-Level Tailor Studio (Tailor V2)
Unlike one-shot resume generators that rewrite entire documents and hallucinate dates or titles, **Tailor V2** provides an interactive, section-level workbench:
- **Interactive Section Tagging**: Hover over or click any resume section to tag root areas (`summary`, `skills`, `projects`, `experience`, `education`, `certifications`) or individual items (`projects.0`, `experience.1`).
- **Whole-Section Collection Re-Ranking**: Tagging the complete `projects` section allows re-ranking projects dynamically (e.g. prioritizing GenAI / RAG architectures first for an AI role) while preserving all verified metadata and live project links.
- **Inviolable Frozen Anchors**: Employer titles, company names, employment dates, and degree institutions are locked and 100% immutable.
- **Atomic Concurrency & Quotas**: Redis distributed locks (`SET NX EX`) prevent race conditions, and a 3-revision quota is strictly enforced per session.
- **Exact Vector Sync**: Live HTML preview is synchronized with 4 hardened single-page LaTeX templates (`Resume0` to `Resume3`).

---

## API Reference

### 1. Interactive Tailor V2 (`/tailor/v2/*`)

| Endpoint | Method | Description |
|---|---|---|
| `/tailor/v2/init` | `POST` | Initialize an interactive session. Parses master resume facts, calculates target JD relevance scores, assigns deterministic slug IDs, and saves session state to Redis. |
| `/tailor/v2/revise` | `POST` | Execute targeted section-level revisions via LLM agent. Enforces frozen anchors, whole-collection re-ranking, atomic Redis locking, and returns updated JSON instantly. |
| `/tailor/v2/session` | `GET` | Recover session state on page reload or reconnect with version tracking and remaining revision credits. |
| `/tailor/v2/export/pdf` | `POST` | Export tailored vector PDF. Primary: LaTeX compilation cascade via ytotech/pdflatex; Fallback: Browser vector html2pdf. |

#### Example: Initialize V2 Session
```bash
curl -X POST http://localhost:8000/tailor/v2/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "resume_url": "https://storage.example.com/resume.pdf",
    "job_desc": "Senior Full Stack Engineer specializing in React, TypeScript, and FastAPI.",
    "template": 0
  }'
```

#### Example: Revise & Re-Rank Projects
```bash
curl -X POST http://localhost:8000/tailor/v2/revise \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "session_id": "tailor_v2_sess_hash",
    "comments": [
      {
        "section_key": "projects",
        "instruction": "re rank for gen ai RAG first based order"
      }
    ]
  }'
```

---

### 2. Workflow Orchestration (`/api/jobs/*`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/jobs/start` | `POST` | Start a new workflow (`fetch_jobs` or `apply_jobs`). |
| `/api/jobs/active` | `GET` | Get the user's active session state and active worker status. |
| `/api/jobs/stream` | `GET` | Server-Sent Events (SSE) stream for real-time progress events. |
| `/api/jobs/status` | `GET` | Polling fallback for workflow status. |
| `/api/jobs/cleanup` | `POST` | Clean up completed or failed session records. |
| `/api/jobs/trigger-next-queue` | `POST` | QStash webhook callback to process the next job in the FREE tier queue. |

---

### 3. Remote Webcast & Session Context (`/api/jobs-server/*`, `/api/*`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/jobs-server/connect-token` | `POST` | Generate secure one-time token for remote Webcast canvas connection. |
| `/api/store-cookie` | `POST` | Store authenticated session context payload into PostgreSQL. |
| `/logout` | `DELETE` | Invalidate and disconnect saved session context. |

---

### 4. Direct Tailoring & Generation (V1 & Portfolio)

| Endpoint | Method | Description |
|---|---|---|
| `/tailor` | `POST` | Batch auto-apply resume tailoring endpoint (used by Chrome Extension / Background Applier) with 2-hour deterministic Redis caching. |
| `/tailor/get-templates` | `GET` | Retrieve template previews for the 4 core resume templates. |
| `/portfolio` | `POST` | Generate a full-stack personal portfolio website from verified facts. |
| `/portfolio/get-templates` | `GET` | Retrieve portfolio design templates. |

---

## Resume Template Showcase (1-Page Synchronized LaTeX)

HireHawk features 4 production LaTeX templates, each engineered for strict 1-page budget fitting and synchronized with the frontend preview:

| Template | Name | Architecture & Styling |
|---|---|---|
| **Template 0** | Modern Minimalist | Clean, single-column design with high readability, compact job headers, and dynamic line skips. |
| **Template 1** | Two-Column Crimson | Palatino typography, 30/70 paracol column split, crimson skill score bars, and dark charcoal header banner. |
| **Template 2** | ModernCV Executive | Helvetica typography, blue-gray branding, clean section rules, and tiered publication/achievement formatting. |
| **Template 3** | Left-Rail Sidebar | Charcoal left sidebar for identity, skills, and education; right content rail for professional experience and projects. |

---

## Database Schema (Prisma / PostgreSQL)

HireHawk uses Supabase PostgreSQL mapped in Next.js with Prisma:

```prisma
model User {
  id                        String              @id @default(uuid()) @db.Uuid
  email                     String              @unique
  name                      String?
  resume_url                String?
  applied_jobs              String[]
  linkedin_context          Json?               @db.Json
  context_updated_at        DateTime?           @db.Timestamp(6)
  user_data                 Json?               // Cached parsed resume facts
  profile_image             String?
  credits_last_reset        DateTime            @default(now()) @db.Timestamptz(6)
  fetch_jobs_credits        Int                 @default(2)
  shared_generation_credits Int                 @default(5)
  tier                      TIER                @default(FREE)
  isConnected               Boolean             @default(false)
  workflow_sessions         workflow_sessions?
  daily_apply_count         Int                 @default(0)
  daily_apply_date          DateTime?           @db.Date

  @@map("User")
}

model workflow_sessions {
  id             String              @id @db.Uuid
  user_id        String              @unique(map: "one_active_job_per_user", where: raw("(status = ANY (ARRAY['pending'::session_status_enum, 'running'::session_status_enum, 'scraper_raw'::session_status_enum]))")) @db.Uuid
  workflow_type  workflow_type_enum
  status         session_status_enum @default(pending)
  input_data     Json?
  output_data    Json?
  last_active_at DateTime            @default(now()) @db.Timestamptz(6)
  created_at     DateTime            @default(now()) @db.Timestamptz(6)
  user           User                @relation(fields: [user_id], references: [id], onDelete: NoAction, onUpdate: NoAction)
}

enum session_status_enum {
  pending
  running
  scraper_raw
  completed
  failed
}

enum workflow_type_enum {
  fetch_jobs
  apply_jobs
}

enum TIER {
  FREE
  PRO
}

model SystemConfig {
  key        String   @id
  value      String
  updated_at DateTime @default(now()) @updatedAt

  @@map("SystemConfig")
}
```

---

## LLM Gateway Architecture (`agents/llm_gateway.py`)

HireHawk incorporates a fault-tolerant multi-provider LLM Gateway:
- **Gemini Multi-Key Pool**: Distributes traffic across multiple Google API keys (`GEMINI_API_KEYS`), tracking cooldowns (60s) upon encountering `429 RATE_LIMITED` errors.
- **Provider Cascading**: Automatically cascades from primary Groq models (`qwen/qwen3.8-27b`) to fallback models (`openai/gpt-oss-120b`) and Pro-tier dedicated Gemini instances.
- **Strict Schema Enforcement**: Transforms Pydantic schemas into OpenAI/Groq strict-mode schemas (`additionalProperties: false`) and sanitizes double-escaped responses.
- **Anti-Hallucination Guardrails**: Cross-references every revised bullet point against master `ResumeFacts` extracted during Pass 1.

---

## Local Development Setup

### Prerequisites
- Node.js >= 20
- Python >= 3.10
- PostgreSQL (Supabase)
- Redis (Upstash or local instance)

### 1. Frontend Setup (`my-fe`)
```bash
cd my-fe
npm install
npx prisma generate
npm run dev
# Running on http://localhost:3000
```

### 2. Python Backend Setup (`backend_python`)
```bash
cd backend_python
python -m venv .devhire_backend
# Activate virtual environment
# Windows:
.devhire_backend\Scripts\activate
# Linux/macOS:
source .devhire_backend/bin/activate

pip install -r requirements.txt
playwright install chromium

# Launch the FastAPI server with reload
uvicorn main.main:app --reload --port 8000
```

### 3. Auth Server Setup (`auth-server`)
```bash
cd auth-server
npm install
npm run dev
# Running on http://localhost:8080
```

---

## Subscription Tiers & Capabilities

| Capability | Basic (Free) | Pro |
|---|---|---|
| **Fetch Jobs Discovery** | 2 runs per period | Unlimited |
| **Shared Generation Credits** | 5 credits | Unlimited |
| **Execution Architecture** | Queued with delay jitter (~3.5 min wait) | Instant dedicated Cloud Run Worker |
| **Connection Security** | Shared worker execution pool | Isolated dedicated stealth connection |
| **Tailor V2 Studio** | 3 revisions per session | Unlimited dedicated revisions |
| **AI LLM Routing** | High-speed Groq Qwen inference | Dedicated Gemini Pro & Groq capacity |

---

## Security, Privacy & Compliance
- **Zero Raw Credential Storage**: User passwords are never saved. Accounts are authenticated through a remote sandboxed browser stream, and session cookies are persisted in encrypted database fields.
- **Isolated Namespaces**: V1 auto-apply and V2 interactive tailoring utilize strictly segregated Redis key prefixes (`tailor:*` vs `tailor_v2:*`), eliminating cache collision risks.
- **Deterministic ATS Formatting**: Produces industry-standard vector PDFs with pure text layers and embedded links, avoiding OCR parsing failures.
