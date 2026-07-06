# DevHire – AI-Powered LinkedIn Job Application Automation

[![Demo Video](https://img.shields.io/badge/🎬_Demo-Watch_Video-red?style=for-the-badge)](https://www.loom.com/share/ae8227b5df5446669f74b63288176082)

## 🎬 Demo Video

Watch the full product demo to see DevHire in action:

[![DevHire Demo](https://cdn.loom.com/sessions/thumbnails/ae8227b5df5446669f74b63288176082-with-play.gif)](https://www.loom.com/share/ae8227b5df5446669f74b63288176082)

👉 **[Watch Full Demo on Loom](https://www.loom.com/share/ae8227b5df5446669f74b63288176082)**

---

## 🎯 The Problem It Solves

Applying to jobs on LinkedIn is **tedious, time-consuming, and repetitive**. Professionals spend hours:
- Manually searching for relevant job postings
- Reading job descriptions to find matches
- Customizing resumes for each application
- Filling out LinkedIn forms repeatedly
- Tracking which jobs they've applied to

**DevHire automates this entire workflow**, enabling job seekers to apply to dozens of relevant positions in minutes instead of hours, with AI-powered resume customization tailored to each job.

---

## 🚀 What DevHire Does

DevHire is a **full-stack AI automation platform** that:

1. **Extracts Your Profile** – Uses a Chrome extension to capture LinkedIn credentials, cookies, and browser fingerprint
2. **Parses Your Resume** – Analyzes your resume using Google Gemini AI to extract skills, experience, and qualifications
3. **Searches for Jobs** – Scrapes LinkedIn using Playwright (headless browser) based on parsed job titles and keywords from your resume
4. **Tailors Resumes** – Uses Google Gemini to dynamically generate job-specific resumes for each application with LaTeX rendering to PDF (supports **4 professional templates**)
5. **Auto-Applies** – Programmatically fills out LinkedIn's Easy Apply forms and submits applications with tailored resumes
6. **Generates Portfolios** – 🆕 **AI-powered portfolio website generator** creates professional HTML/CSS portfolio pages from your resume (supports **5 templates**)
7. **Tracks Progress** – Provides real-time progress tracking and application history in the web dashboard
8. **Persistent Sessions** – 🆕 Stores LinkedIn browser context in database for seamless session resumption
9. **Remote Browser Webcast Stream (Remote Login)** – 🆕 Streams a headless browser session directly to a Next.js client-side `<canvas>` element via WebSocket and CDP (Chrome DevTools Protocol), supporting real-time mouse clicks, scrolls, and keystrokes to authenticate securely.
10. **Dynamic Viewport Emulation** – 🆕 Dynamically reads client screen resolution and resizes the remote browser context (supporting touch-based mobile layouts) for accurate coordinate mappings.
11. **Fail-Fast Session Guard** – 🆕 Validates LinkedIn session cookies *before* run starts to prevent wasted Gemini API costs, shuts down browser memory resources while tailoring, and aborts immediately on mid-run session loss (preserving completed jobs).

**Result:** Apply to 50+ tailored job applications in the time it used to take to apply to 5.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│        Frontend (Next.js 15 + React 19)             │
│  ✨ Dashboard, Login, Job Selection, Apply Flow    │
│  🆕 Portfolio Builder, Pricing Plans, Password Reset│
│  🆕 Canvas-based Remote Login Webcast Control       │
│         Supabase Auth + Prisma ORM                 │
└─────────────────────────────────────────────────────┘
         ↕ (API calls)                      ↕ (CDP Webcast Stream)
┌──────────────────────────────────┐      ┌─────────────────────────────┐
│ Backend (Python FastAPI)         │      │ WS Streaming Server (Node)  │
│ • /get-jobs /apply-jobs /tailor  │      │ • Streams headless browser  │
│ • 🆕 /linkedin/connect-token     │ ───> │   session to Next.js canvas │
│ • 🆕 /portfolio generator        │      │ • Syncs mouse/touch inputs  │
│ • 🆕 /logout, /debug/*           │      │ • Saves session to Postgres │
└──────────────────────────────────┘      └─────────────────────────────┘
         ↕ (Browser control)
┌─────────────────────────────────────────────────────┐
│   Chrome Extension (Manifest V3)                   │
│  • Captures LinkedIn cookies & localStorage       │
│  • Sends credentials to backend                   │
│  • Injects content scripts for data collection    │
│  • 🆕 Browser fingerprint collection              │
└─────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────┐
│   Agents (Async Python Tasks)                      │
│  • Scraper Agent – LinkedIn job search (Playwright)│
│  • Parser Agent – Resume analysis (Gemini AI)      │
│  • Tailor Agent – Resume generation (Gemini)      │
│  • Apply Agent – Form filling & submission         │
│  • 🆕 Portfolio Agent – Website generation (Groq) │
└─────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────┐
│   Databases                                        │
│  • PostgreSQL (Prisma ORM) – Users, applied jobs  │
│  • 🆕 LinkedIn Context Storage – Session persist  │
│  • Supabase – Authentication & Auth helpers       │
└─────────────────────────────────────────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 15, React 19, TypeScript | User dashboard, job browsing, application tracking, portfolio builder |
| **Backend** | Python FastAPI, Uvicorn | Job scraping, resume tailoring, form automation, portfolio generation |
| **AI Engines** | Google Gemini 2.5 Flash + Groq GPT | Resume parsing, job-resume matching, tailored resume generation, portfolio creation |
| **Browser Automation** | Playwright (async) | LinkedIn login, job scraping, form filling |
| **Auth** | Supabase + JWT + AES-256 | User registration, login, session management, credential encryption |
| **Database** | PostgreSQL + Prisma | User profiles, applied jobs, resume URLs, LinkedIn context |
| **Extension** | Chrome Manifest V3 | Cookie/fingerprint capture, credential sync, session persistence |
| **Webcast Server** | Node.js, Playwright, WS, CDP | Streams remote headless browser login session to frontend canvas with mouse/keyboard/scroll sync |

---

## 🧠 Frontend Architecture & State Management

### Frontend State Management Flow

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        Frontend State Management Flow                          │
└────────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────┐
   │  App Load → layout.tsx wraps with <UserProvider>           │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  UserContext.tsx::fetchUserData()                           │
   │  ─────────────────────────────────────────────────────────  │
   │  1. supabase.auth.getSession() → Get auth token from cookie │
   │  2. /api/User?id={userId} → Fetch from public.User table   │
   │  3. Extract: id, email, name, resume_url, profile_image    │
   │  4. Store in sessionStorage (backup)                        │
   │  5. Sync to context state                                   │
   └──────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
   │ UserContext  │  │ SessionStor. │  │ IndexedDB        │
   │ (React State)│  │ (Backup)     │  │ (Job Cache)      │
   │              │  │              │  │                  │
   │ • id         │  │ • id         │  │ • Fetched Jobs   │
   │ • email      │  │ • email      │  │ • Apply Progress │
   │ • name       │  │ • name       │  │ • Results        │
   │ • resume_url │  │ • resume     │  │ • Status         │
   │ • profile... │  │ • Lcontext   │  │                  │
   │ • loading    │  └──────────────┘  └──────────────────┘
   │ • isLoggedIn │
   └──────────────┘
        │
        └─────────────────────────────────┬──────────────────────────────┐
                                          │                              │
                    ┌─────────────────────▼────────────────────┐         │
                    │    Components using useUser()           │         │
                    ├──────────────────────────────────────────┤         │
                    │ • Navbar                                 │         │
                    │ • hero-section (Find Jobs button)        │         │
                    │ • Tailor_resume (resume_url)             │         │
                    │ • PortfolioPage (resume_url)             │         │
                    │ • Jobs (user.id for API calls)           │         │
                    │ • Profile (user data display)            │         │
                    └──────────────────────────────────────────┘         │
                                                                          │
                    ┌─────────────────────────────────────────┐          │
                    │  Backend API Calls                      │          │
                    ├─────────────────────────────────────────┤          │
                    │ • /get-jobs (resume_url)                │◄─────────┘
                    │ • /apply-jobs (user_id, resume_url)    │
                    │ • /tailor (job_desc, resume_url)       │
                    │ • /portfolio (resume_url)              │
                    └─────────────────────────────────────────┘
```

### Key Insight: Single Fetch Strategy ⚡
- **One API call per session**: User data fetched once when app loads
- **Context as source of truth**: All components read from UserContext via `useUser()` hook
- **SessionStorage as backup**: Persists across page refreshes for edge cases  
- **No polling**: No 2-second intervals or duplicate API calls
- **Resume URL ready immediately**: Available on landing page for all features

---

## 🔐 Authentication & Session Persistence

### Complete Auth Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Authentication & Session Persistence                      │
└─────────────────────────────────────────────────────────────────────────────┘

   First Visit/Login                          Return Visit (Persistent)
   ────────────────                           ─────────────────────────
        │                                            │
        ▼                                            ▼
   ┌─────────────────┐                        ┌──────────────────┐
   │ /login or       │                        │ App Load          │
   │ /register       │                        │ (page.tsx)        │
   └─────────────────┘                        └──────────────────┘
        │                                            │
        ▼                                            ▼
   ┌─────────────────────────────────┐        ┌──────────────────────────┐
   │ Email/Pass or Google OAuth      │        │ Check Supabase Cookie    │
   │ supabase.auth.signIn*()         │        │ (sb-{projectid}-auth)   │
   └─────────────────────────────────┘        └──────────────────────────┘
        │                                            │
        ▼                                            ▼
   ┌─────────────────────────────────┐        ┌──────────────────────────┐
   │ Supabase Sets Cookie            │        │ UserContext.fetchData()  │
   │ (httpOnly, 24h expiry)          │        │ Uses existing cookie!    │
   │ + Emits "SIGNED_IN" event       │        └──────────────────────────┘
   └─────────────────────────────────┘                  │
        │                                               ▼
        │                                        ┌─────────────────┐
        └───────────┬──────────────────────────►│ User data ready │
                    │                            │ No re-login!    │
                    ▼                            └─────────────────┘
        ┌──────────────────────────┐
        │ UserContext.fetchData()  │
        │ (Same flow for both)     │
        │ ✓ Fetches from DB        │
        │ ✓ Syncs to sessionStor.  │
        │ ✓ Provides via useUser() │
        └──────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────┐
        │ User ready to use app    │
        │ ✓ resume_url available   │
        │ ✓ profile_image ready    │
        │ ✓ Can access all pages   │
        └──────────────────────────┘

   ┌────────────────────────────────────────────────────────────┐
   │ KEY: Cookie persistence = Users stay logged in until 24h  │
   │ No re-login needed on page refresh or app restart!        │
   └────────────────────────────────────────────────────────────┘
```

### Resume URL Fetching Strategy 📄

1. **At Login**: UserContext fetches resume_url from `/api/User` (PostgreSQL)
2. **In sessionStorage**: Backup stored as `resume` key  
3. **Used by**: Hero section (Find Jobs button), Tailor Resume, Portfolio, Jobs pages
4. **No re-fetch**: All components read from UserContext context - never re-fetch from DB
5. **On Upload**: Resume upload hook emits `resume-uploaded` event → UserContext refreshes data

```javascript
// In any component:
const { user } = useUser();
// user.resume_url is immediately available - no loading needed!
```

---

## 🎨 Component Documentation

### Core Components Using UserContext

| Component | Location | Purpose | Depends On |
|-----------|----------|---------|-----------|
| **UserProvider** | `app/utiles/UserContext.tsx` | Centralizes user data fetching and caching | Supabase session + `/api/User` |
| **Navbar** | `app/Components/Navbar.tsx` | Header with user profile + logout | `useUser()` hook |
| **hero-section** | `app/Components/Landing-Page/hero-section.tsx` | Landing page - shows "Find Jobs" if resume_url exists | `useUser()` hook |
| **Tailor_resume** | `app/Components/Tailor_resume.tsx` | Resume tailoring interface | `useUser()` + resume_url |
| **PortfolioPage** | `app/Components/PortfolioPage.tsx` | Portfolio builder (requires resume) | `useUser()` + resume_url |
| **Jobs** | `app/Components/Jobs.tsx` | Job search & listing | `useUser()` + user.id |
| **Login** | `app/Components/Login.tsx` | Email/OAuth login | Supabase auth |
| **Register** | `app/Components/Register.tsx` | User registration | Supabase auth |

### How to Use UserContext in a Component

```typescript
import { useUser } from '@/app/utiles/UserContext';

export default function MyComponent() {
  const { user, loading, isLoggedIn, logout } = useUser();

  if (loading) return <div>Loading user data...</div>;
  if (!isLoggedIn) return <div>Please log in</div>;

  return (
    <div>
      <h1>Hello, {user.name}</h1>
      <p>Resume: {user.resume_url ? 'Uploaded' : 'Not uploaded'}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### useUser() Hook API

```typescript
const { user, loading, isLoggedIn, logout } = useUser();

// user object shape:
{
  id: string;              // Supabase user ID
  email: string;           // User email
  name: string;            // User name
  resume_url: string | null; // S3 URL to uploaded resume
  profile_image: string | null; // Profile picture URL
  linkedin_context: string | null; // LinkedIn user context for job search
}

// loading: boolean - True while fetching user data on app load
// isLoggedIn: boolean - True if user has valid session
// logout(): Promise<void> - Sign out user and clear data
```

---

## 📡 API Endpoints Reference

### Frontend API Endpoints (`my-fe/app/api/`)

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|-----------|
| `/api/User` | `GET` | Fetch user profile | `id` (query param) |
| `/api/User` | `POST` | Update user profile | `id`, `name`, `email`, etc. |
| `/api/resume-upload` | `POST` | Handle resume file upload | `file` (FormData) |
| `/api/portfolio-generate` | `POST` | Generate portfolio website | `user_id`, `resume_url` |

### Backend API Endpoints (FastAPI)

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/get-jobs` | `POST` | Parse resume + scrape LinkedIn | Jobs component |
| `/tailor` | `POST` | Tailor resume to job description | Tailor_resume component |
| `/apply-jobs` | `POST` | Apply to jobs with tailored resume | Apply component |
| `/portfolio` | `POST` | Generate AI portfolio website | PortfolioPage component |
| `/store-cookie` | `POST` | Receive LinkedIn auth from extension | Chrome Extension |
| `/logout` | `POST` | Clear session + LinkedIn context | Navbar component |

---

## 💾 Database Schema

### PostgreSQL (Prisma ORM)

```prisma
model User {
  id              String    @id @default(cuid())
  email           String    @unique
  name            String?
  resume_url      String?   // S3 URL to uploaded resume
  profile_image   String?   // Profile picture URL
  linkedin_context String?  // LinkedIn session for job scraping
  
  appliedJobs     AppliedJob[]
  portfolios      Portfolio[]
  
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
}

model AppliedJob {
  id              String    @id @default(cuid())
  user_id         String
  job_url         String
  company_name    String
  position        String
  tailored_resume String    // Resume tailored for this job
  status          String    // "applied", "pending", "rejected", etc.
  
  user            User      @relation(fields: [user_id], references: [id], onDelete: Cascade)
  
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
}

model Portfolio {
  id              String    @id @default(cuid())
  user_id         String
  portfolio_url   String    // URL to generated portfolio website
  ai_content      String    // AI-generated portfolio content
  
  user            User      @relation(fields: [user_id], references: [id], onDelete: Cascade)
  
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
}
```

### Supabase Authentication

- **Provider**: Email + Google OAuth
- **Session Storage**: httpOnly cookies (24h expiry)
- **User Sync**: Supabase `auth.users` table ↔ PostgreSQL `public.User` table

---

## ⚡ Performance Optimizations

### 1. Single Fetch Strategy
- **Problem**: Components were fetching user data independently, causing multiple API calls
- **Solution**: UserContext fetches once on app load, provides via hook
- **Benefit**: 1 API call per session instead of N calls

### 2. SessionStorage Backup
- **Purpose**: Handles page refreshes faster than re-fetching from API
- **Synced**: Whenever UserContext data changes
- **Fallback**: If IndexedDB or React Context fails, sessionStorage provides data

### 3. Resume URL Caching
- **Strategy**: Fetch once at login, store in context + sessionStorage
- **Eliminates**: Repeated DB queries for `public.User.resume_url`
- **Used by**: Hero section, Tailor, Portfolio, Jobs - all read from context

### 4. IndexedDB for Job Caching
- **Stores**: Fetched jobs list, apply progress, results
- **Advantage**: Offline access, faster queries than API
- **Updated**: Each time user runs job search

### 5. Lazy Loading Pages
- **Tailor Resume**: Only available if `user.resume_url` exists
- **Portfolio**: Only available if resume exists
- **Find Jobs**: Button hidden until resume is uploaded

### 6. Async Backend Operations  
- **Scraping**: Runs async without blocking UI
- **Resume Tailoring**: Streams results via SSE for real-time updates
- **Portfolio Generation**: Async with progress notifications

---

```
DevHire/
├── my-fe/                          # Next.js Frontend
│   ├── app/
│   │   ├── Components/
│   │   │   ├── Home.tsx           # Landing page hero section
│   │   │   ├── Jobs.tsx           # Job search & listing
│   │   │   ├── Apply.tsx          # Application progress tracker
│   │   │   ├── Tailor_resume.tsx  # Resume tailoring UI
│   │   │   ├── Login.tsx          # Authentication
│   │   │   ├── Register.tsx       # 🆕 User registration with validation
│   │   │   ├── ResetPass.tsx      # 🆕 Password reset flow
│   │   │   ├── JobCards.tsx       # Job card display
│   │   │   ├── PortfolioPage.tsx  # 🆕 AI portfolio builder UI
│   │   │   ├── Navbar.tsx         # Navigation with session management
│   │   │   ├── Features.tsx       # Feature showcase with animations
│   │   │   ├── Linkedin.tsx       # LinkedIn credentials input
│   │   │   ├── About.jsx          # About page
│   │   │   ├── Pricing/           # 🆕 Pricing plans (Basic/Pro)
│   │   │   └── Landing-Page/      # Landing page components
│   │   ├── api/                   # Backend API routes (Next.js)
│   │   │   ├── store/             # 🆕 Encrypted credential storage
│   │   │   ├── get-data/          # 🆕 Retrieve encrypted credentials
│   │   │   └── User/              # User CRUD operations
│   │   ├── Jobs/                  # Job pages
│   │   │   ├── LinkedinUserDetails/ # LinkedIn login page
│   │   │   ├── tailor/            # Resume tailoring page
│   │   │   └── portfolio/         # 🆕 Portfolio builder page
│   │   ├── apply/                 # Application flow pages
│   │   ├── login/                 # Login page
│   │   ├── register/              # 🆕 Registration page
│   │   ├── reset-password/        # 🆕 Password reset page
│   │   ├── pricing/               # 🆕 Pricing page
│   │   ├── about/                 # About page
│   │   └── utiles/
│   │       ├── agentsCall.ts      # API calls to Python backend
│   │       ├── supabaseClient.ts  # Supabase initialization
│   │       ├── getUserData.ts     # User profile management
│   │       ├── useUploadResume.ts # 🆕 Resume upload hook
│   │       ├── database.ts        # 🆕 Prisma client
│   │       └── api.ts             # 🆕 API URL configuration
│   ├── prisma/
│   │   └── schema.prisma          # Database schema (PostgreSQL)
│   ├── context/                   # React context providers
│   ├── store/                     # Redux store configuration
│   └── package.json
│
├── backend_python/                # Python FastAPI Backend
│   ├── main/
│   │   ├── main.py               # FastAPI app setup
│   │   ├── progress_dict.py      # 🆕 Shared progress tracking
│   │   └── routes/
│   │       ├── list_jobs.py      # GET /get-jobs endpoint
│   │       ├── apply_jobs.py     # POST /apply-jobs endpoint
│   │       ├── get_resume.py     # POST /tailor endpoint
│   │       ├── cookie_receiver.py # POST /store-cookie endpoint
│   │       ├── progress_route.py # Progress tracking
│   │       ├── portfolio_generator.py # 🆕 Portfolio generation endpoint
│   │       ├── logout.py         # 🆕 LinkedIn context cleanup
│   │       ├── debug_routes.py   # 🆕 Visual debugging dashboard
│   │       └── templates/        # 🆕 Resume template images
│   ├── agents/
│   │   ├── scraper_agent.py             # LinkedIn job scraper
│   │   ├── scraper_agent_optimized.py   # Optimized async scraper
│   │   ├── apply_agent.py               # Form filling & submission
│   │   ├── tailor.py                    # Resume AI customization (4 templates)
│   │   ├── parse_agent.py               # Resume parsing
│   │   └── portfolio_agent.py           # 🆕 AI portfolio generator (5 templates)
│   ├── database/
│   │   ├── db_engine.py          # SQLAlchemy connection
│   │   ├── SchemaModel.py        # User model (SQLAlchemy)
│   │   └── linkedin_context.py   # 🆕 LinkedIn session persistence
│   ├── lib/
│   │   └── session_manager.py    # 🆕 Session management utilities
│   ├── data_dump/                # 🆕 Playwright persistent storage
│   ├── config.py                 # API keys & environment variables
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # 🆕 Docker containerization
│   ├── run.sh                    # Linux startup script
│   └── run.bat                   # 🆕 Windows startup script
│
├── extension/                     # Chrome Extension
│   ├── manifest.json             # Extension configuration
│   ├── background.js             # Service worker (cookie/storage sync)
│   └── content.js                # Content script (fingerprint collection)
│
├── next-app/                      # 🆕 Alternative Next.js app
│   ├── app/
│   │   ├── api/
│   │   ├── components/
│   │   ├── signin/
│   │   ├── signup/
│   │   └── UserDetails/
│   └── prisma/
│
├── schema.sql                     # 🆕 Database SQL schema
└── prisma/                        # Prisma schema (shared)
    └── schema.prisma             # Database models
```

---

## 🔄 User Journey & Data Flow

### Step 1: User Authenticates
```
1. User logs in with LinkedIn on DevHire web app
2. Chrome extension captures LinkedIn cookies & localStorage
3. Extension sends data to backend (/store-cookie)
4. Backend stores encrypted credentials for session
```

### Step 2: Resume Upload & Parsing
```
1. User uploads resume (PDF/DOCX)
2. Backend extracts text using PyMuPDF + OCR (pytesseract)
3. Gemini AI parses resume → extracts job titles, skills, experience
4. Output: ["Full Stack Developer, Backend Engineer"] + ["Python, React, PostgreSQL"]
```

### Step 3: Job Search
```
1. Frontend calls POST /get-jobs with:
   - user_id, password, resume_url
2. Backend uses Playwright to:
   - Login to LinkedIn with credentials
   - Search for each parsed job title
   - Scrape job listings (title, company, description, link)
3. Jobs returned to frontend, user selects 10-50 jobs
```

### Step 4: Resume Tailoring (Per Job)
```
1. For each selected job:
   - Frontend calls POST /tailor with:
     - original_resume_url, job_description
2. Backend:
   - Downloads original resume PDF
   - Sends to Gemini: "Tailor this resume for this JD"
   - Gemini generates LaTeX with highlighted relevant skills
   - LaTeX rendered to PDF
   - PDF converted to Base64
3. Base64 PDFs sent to frontend, stored in sessionStorage
```

### Step 5: Batch Application
```
1. Frontend calls POST /apply-jobs with:
   - jobs: [{job_url, job_description}]
   - user_id, password, resume_url
2. Backend applies in parallel batches (15 jobs per batch):
   - Open LinkedIn Easy Apply modal via Playwright
   - Detect form fields (experience, skills, resume upload)
   - Fill fields with tailored answers + upload tailored PDF
   - Click Submit
3. Real-time progress updates via /progress endpoint
4. Applications tracked in PostgreSQL (User.applied_jobs)
```

---

## 🛠️ Tech Stack Deep Dive

### Frontend (Next.js)
- **Framework:** Next.js 15.4.6 with App Router
- **Language:** TypeScript + React 19
- **Styling:** Tailwind CSS 4
- **State Management:** Redux Toolkit
- **HTTP:** Axios for API calls
- **Auth:** Supabase Auth + JWT
- **Database ORM:** Prisma Client
- **Animations:** Framer Motion
- **UI Feedback:** React Hot Toast (notifications)
- **PDF Handling:** PDF.js for rendering

### Backend (Python)
- **Framework:** FastAPI (async web server)
- **Async Runtime:** Uvicorn (ASGI)
- **Browser Automation:** Playwright (async headless browser)
- **Database:** PostgreSQL + SQLAlchemy ORM
- **AI Models:**
  - Google Gemini 2.5 Flash (resume parsing, tailoring) with fallback chain
  - Groq GPT-oss-120b (portfolio generation)
- **PDF Processing:** PyMuPDF (fitz), pdf2image, pytesseract (OCR)
- **Resume Generation:** LaTeX rendering (4 templates), FPDF, python-docx
- **Portfolio Generation:** HTML/CSS (5 templates)
- **HTTP:** aiohttp for async requests
- **Auth:** browser-cookie3 for session cookies
- **Containerization:** Docker support

### Database (PostgreSQL + Prisma)
```prisma
model User {
  id                 String    @id @default(uuid()) @db.Uuid
  email              String    @unique
  name               String?
  resume_url         String?
  applied_jobs       String[]  // Array of LinkedIn job URLs applied to
  linkedin_context   Json?     // 🆕 Playwright browser session state
  context_updated_at DateTime? // 🆕 LinkedIn context last update timestamp
}
```

### Chrome Extension
- **Manifest:** V3 (latest standard)
- **Service Worker:** background.js (cookie sync every 2 minutes)
- **Content Script:** content.js (data injection + fingerprint collection)
- **Capabilities:** 
  - Cookie capture (`.linkedin.com` and `www.linkedin.com` domains)
  - localStorage/sessionStorage access
  - 🆕 Browser fingerprint collection (userAgent, platform, language, timezone, hardware info, screen dimensions, viewport size, pixel ratio, color depth)
  - 🆕 SPA navigation detection for re-injection

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** ≥ 20
- **Python** 3.9+
- **PostgreSQL** database (local or cloud)
- **Google API Key** (Gemini access)
- **Supabase Project** (optional, for auth)
- **Chrome Browser** (for extension & Playwright)

### Environment Setup

#### 1. Clone & Install Frontend
```bash
cd my-fe
npm install
npx prisma generate  # Generate Prisma Client
```

Create `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STREAM_SERVER=http://localhost:8080
DATABASE_URL=postgresql://user:password@localhost:5432/devhire
```

#### 2. Install Backend Dependencies
```bash
cd backend_python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install  # Download browser binaries
```

Create `config.py`:
```python
GOOGLE_API = "your_gemini_api_key"
GROQ_API = "your_groq_api_key"  # For portfolio generation
LINKEDIN_ID = "your_linkedin_email"
LINKEDIN_PASSWORD = "your_linkedin_password"
```

#### 3. Setup Database
```bash
cd my-fe
npx prisma migrate dev --name init
```

#### 4. Run Backend API
```bash
cd backend_python
python -m uvicorn main.main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. Run Webcast Streaming Server
```bash
cd auth-server
npm install
npm run dev
```

#### 6. Run Frontend Dashboard
```bash
cd my-fe
npm run dev
```

Open `http://localhost:3000` in browser.

#### 6. Load Chrome Extension
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `DevHire/extension/` folder

---

## 🔑 Key Features & Examples

### Feature 1: Smart Job Parsing
**Input:** Resume PDF
**Process:** 
- Extract text with OCR
- Send to Gemini: "Extract job titles and technical skills"
- Parse response
**Output:** `["Full Stack Developer", "Backend Engineer"] + ["Python", "React", "PostgreSQL", ...]`

### Feature 2: Intelligent Resume Tailoring (4 Templates)
**Input:** Original resume + Job description
**Templates Available:**
- Classic Professional
- Modern Minimalist
- Technical Focus
- Creative Design

**Process:**
```python
prompt = f"""
Given this resume:
{resume_text}

And this job description:
{job_description}

Generate a tailored resume in LaTeX that:
1. Highlights relevant skills
2. Reorders experience by relevance
3. Emphasizes matching technologies
"""
response = gemini_model.generate_content(prompt)
# Response is LaTeX → rendered to PDF → Base64
```
**Output:** Customized PDF resume (Base64 encoded)

### Feature 3: 🆕 AI Portfolio Website Generator (5 Templates)
**Input:** Resume data + Selected template
**Templates Available:**
1. Modern Developer Portfolio
2. Minimalist Professional
3. Creative Designer
4. Tech Startup Style
5. Corporate Executive

**Process:**
```python
# Uses Groq GPT-oss-120b for HTML/CSS generation
prompt = f"""
Generate a complete, responsive portfolio website HTML/CSS based on:
- Resume data: {resume_data}
- Template style: {template_id}

Include sections for: About, Skills, Experience, Projects, Contact
"""
response = groq_client.generate(prompt)
# Returns production-ready HTML/CSS
```
**Output:** Complete HTML/CSS portfolio page with live preview

### Feature 4: Automated Job Application
**Example Flow:**
```python
# 1. Playwright opens LinkedIn Easy Apply
await page.click('button:has-text("Easy Apply")')

# 2. Detect form fields
experience_field = await page.query_selector('input[name="experience"]')
skills_field = await page.query_selector('input[name="skills"]')

# 3. Fill with AI-suggested answers
await experience_field.fill("5 years in Full Stack Development")
await skills_field.fill("Python, React, PostgreSQL")

# 4. Upload tailored resume
resume_input = await page.query_selector('input[type="file"]')
await resume_input.set_input_files(tailored_resume_path)

# 5. Submit
await page.click('button:has-text("Submit application")')
```

### Feature 5: 🆕 LinkedIn Session Persistence
**Process:**
```python
# Save browser context to database
await save_linkedin_context(
    email=user_email,
    context={
        "storage_state": browser_context.storage_state(),
        "cookies": cookies,
        "localStorage": local_storage
    }
)

# Restore session on next visit - no re-login needed!
context = await load_linkedin_context(user_email)
browser_context = await browser.new_context(storage_state=context)
```

### Feature 6: 🆕 Visual Debugging Dashboard
**Endpoints:**
- `/debug/screenshots` - View all debug screenshots
- `/debug/gallery` - HTML gallery for visual inspection
- `/debug/images` - Get images from recent scraper runs

---

## � Pricing Plans

| Feature | Basic (Free) | Pro (₹199/month) |
|---------|--------------|------------------|
| Job Applications | 10/month | Unlimited |
| Resume Tailoring | 5/month | Unlimited |
| Portfolio Generation | 1 template | All 5 templates |
| LinkedIn Context Persistence | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

---

## �📊 Performance & Metrics

| Metric | Value |
|--------|-------|
| **Jobs Applied Per Hour** | 50-100 (vs. 5-10 manual) |
| **Resume Customization Time** | <5 seconds per job (Gemini) |
| **Job Scraping Speed** | 20-30 jobs/minute |
| **End-to-End Application Time** | 10-15 minutes for 50 jobs |
| **Success Rate (Easy Apply)** | ~85% (varies by form complexity) |

---

## 🔒 Security & Privacy

### Credential Handling
- LinkedIn credentials encrypted with AES-256-CBC
- Session-based authentication (JWT)
- Credentials stored in HTTP-only cookies (encrypted)
- LinkedIn context stored in PostgreSQL (session persistence)

### Data Protection
- CORS middleware restricts to authorized origins (extension ID + Vercel production URL)
- Supabase Auth for user verification
- PostgreSQL for encrypted data at rest

### LinkedIn Compliance
- Uses official LinkedIn API where available
- Respects robots.txt and rate limits
- Stealth mode Playwright (mimics human behavior)

---

## 🐛 Troubleshooting

### "Cannot use import statement outside a module"
**Solution:** Ensure `package.json` has `"type": "module"`

### "Playwright browser download failed"
**Solution:** Run `playwright install` after pip install

### "Gemini API rate limit exceeded"
**Solution:** Add delays between tailoring requests (5-10 second intervals). The system has automatic fallback to: `gemini-2.5-flash` → `gemini-2.5-flash-lite` → `gemini-2.0-flash` → `gemini-1.5-flash`

### "LinkedIn login failing"
**Solution:**
- Update `LINKEDIN_ID` and `LINKEDIN_PASSWORD` in `config.py`
- Check if LinkedIn has changed login flow (inspect with DevTools)
- Ensure 2FA is disabled or use app passwords
- Use the debug dashboard at `/debug/gallery` to see screenshots

### "Resume tailoring returns LaTeX errors"
**Solution:** Retry with simpler job description or increase context length in Gemini prompt

### "Portfolio generation not working"
**Solution:** 
- Ensure Groq API key is configured in `config.py`
- Check that resume data is properly parsed
- Try a different template

### "LinkedIn context not persisting"
**Solution:**
- Check database connection in `db_engine.py`
- Verify `linkedin_context` column exists in User table
- Run database migrations: `npx prisma migrate dev`

---

## 📚 API Endpoints

### Frontend Calls Backend

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/get-jobs` | POST | Parse resume & fetch matching jobs from LinkedIn |
| `/apply-jobs` | POST | Apply to selected jobs with tailored resumes |
| `/tailor` | POST | Generate AI-tailored resume for a job |
| `/store-cookie` | POST | Receive LinkedIn cookies from extension |
| `/progress` | GET | Real-time application progress tracking |
| `/portfolio` | POST | 🆕 Generate AI-powered portfolio website |
| `/portfolio/templates` | GET | 🆕 Get available portfolio templates |
| `/templates` | GET | 🆕 Get available resume templates |
| `/logout` | DELETE | 🆕 Clear LinkedIn context from database |
| `/progress/scraping/{email}` | GET | 🆕 Job scraping progress by user |
| `/progress/applying/{email}` | GET | 🆕 Application progress by user |

### Debug Endpoints (Development)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/debug/capture` | GET | 🆕 Capture screenshot with Playwright |
| `/debug/screenshot` | GET | 🆕 Get captured screenshot |
| `/debug/html` | GET | 🆕 Get captured HTML |
| `/debug/screenshots` | GET | 🆕 Get all debug screenshots as base64 |
| `/debug/images` | GET | 🆕 Get debug images from scraper runs |
| `/debug/gallery` | GET | 🆕 HTML gallery to view screenshots |
| `/debug/cleanup` | DELETE | 🆕 Clear old debug files |

### Next.js API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/store` | POST | 🆕 Encrypt LinkedIn credentials (AES-256-CBC) |
| `/api/get-data` | GET | 🆕 Retrieve encrypted credentials |
| `/api/User?action=insert` | POST | 🆕 Create new user |
| `/api/User?action=update` | POST | 🆕 Update user data |
| `/api/User?id={id}` | GET | 🆕 Fetch user by ID |

### Example Requests

```bash
# Parse resume & get jobs
curl -X POST http://localhost:8000/get-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "file_url": "https://..../resume.pdf",
    "password": "linkedin_password"
  }'

# Tailor resume for a job
curl -X POST http://localhost:8000/tailor \
  -H "Content-Type: application/json" \
  -d '{
    "job_desc": "We are looking for a Full Stack Developer...",
    "resume_url": "https://..../resume.pdf"
  }'

# Apply to jobs
curl -X POST http://localhost:8000/apply-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "password": "linkedin_password",
    "resume_url": "https://..../resume.pdf",
    "jobs": [
      {
        "job_url": "https://linkedin.com/jobs/123456",
        "job_description": "Full Stack Developer..."
      }
    ]
  }'

# 🆕 Generate portfolio website
curl -X POST http://localhost:8000/portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://..../resume.pdf",
    "template_id": "modern-developer"
  }'

# 🆕 Get available portfolio templates
curl -X GET http://localhost:8000/portfolio/templates

# 🆕 Get available resume templates
curl -X GET http://localhost:8000/templates

# 🆕 Clear LinkedIn context (logout)
curl -X DELETE http://localhost:8000/logout?email=user@example.com

# 🆕 Check scraping progress
curl -X GET http://localhost:8000/progress/scraping/user@example.com

# 🆕 Check application progress
curl -X GET http://localhost:8000/progress/applying/user@example.com
```

---

## 🎓 Learning Resources

### Understanding Key Workflows

1. **Async Python in Backend**
   - Read: `backend_python/agents/scraper_agent_optimized.py` (async Playwright usage)
   - Learn: How Playwright async contexts handle multiple browser sessions

2. **Resume Tailoring Logic**
   - Read: `backend_python/agents/tailor.py` (Gemini integration)
   - Learn: PDF text extraction, LaTeX generation, batch processing, 4 template system

3. **🆕 Portfolio Generation**
   - Read: `backend_python/agents/portfolio_agent.py` (Groq integration)
   - Learn: HTML/CSS generation from resume data, 5 template system

4. **Frontend State Management**
   - Read: `my-fe/app/Components/Jobs.tsx` & `Apply.tsx`
   - Learn: Redux + sessionStorage for multi-step flows

5. **🆕 Portfolio Builder UI**
   - Read: `my-fe/app/Components/PortfolioPage.tsx`
   - Learn: Template selection, live preview, code export

6. **Database Models**
   - Read: `my-fe/prisma/schema.prisma` & `backend_python/database/SchemaModel.py`
   - Learn: How Prisma ORM mirrors SQLAlchemy models, LinkedIn context storage

7. **🆕 LinkedIn Session Persistence**
   - Read: `backend_python/database/linkedin_context.py`
   - Learn: Browser context serialization and restoration

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Commit with clear messages: `git commit -m "Add resume parsing optimization"`
4. Push and create a Pull Request

---

## 📝 License

This project is licensed under the MIT License – see LICENSE file for details.

---

## 🎉 Future Enhancements

- [ ] Support for multiple job boards (Indeed, Glassdoor, Dice)
- [ ] Resume versioning & A/B testing
- [ ] Salary negotiation insights
- [ ] Interview prep with AI coaching
- [ ] Email notification tracking
- [ ] Mobile app (React Native)
- [ ] API marketplace for third-party integrations
- [ ] Cover letter generation
- [ ] Application analytics dashboard
- [ ] Multi-language resume support

---

## 📧 Contact & Support

**For issues, questions, or feature requests:**
- Open an issue on GitHub
- Email: support@devhire.dev
- Discord: [Join our community](https://discord.gg/devhire)

---

**Made with ❤️ to help developers land their dream jobs faster.**

---

## 📋 Changelog

### Latest Updates (v2.0)
- ✅ **AI Portfolio Generator** - Create professional portfolio websites from your resume
- ✅ **5 Portfolio Templates** - Modern, Minimalist, Creative, Startup, Corporate styles
- ✅ **4 Resume Templates** - Choose from multiple LaTeX resume designs
- ✅ **LinkedIn Session Persistence** - No more re-logging in every session
- ✅ **Visual Debugging Dashboard** - See exactly what the scraper sees
- ✅ **Pricing System** - Basic (Free) and Pro tiers
- ✅ **Password Reset Flow** - Full Supabase-powered password recovery
- ✅ **Browser Fingerprint Collection** - Enhanced session authenticity
- ✅ **Docker Support** - Easy containerized deployment
- ✅ **Windows Support** - `run.bat` for Windows users
- ✅ **Groq AI Integration** - Additional AI model for portfolio generation
- ✅ **Gemini Fallback Chain** - Automatic failover between Gemini models
