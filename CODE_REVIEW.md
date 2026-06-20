# DevHire — Full Codebase Review

**Date:** 2026-06-20
**Method:** Multi-agent review — 10 subsystem reviewers (backend orchestration, the 5 agents, backend API/security, frontend job-flow, frontend auth, frontend components, extension/infra). Every medium-or-higher finding was handed to an adversarial verifier instructed to *refute* it. 99 raw findings → **5 critical, 11 high, 19 medium** survived verification; **2 were refuted** (false positives); the rest are low/info hygiene.

---

## The meta-finding (read this first)

**The backend has no authentication or authorization layer at all.** Every backend route trusts a caller-supplied `user_id`/`email` from the request body or query string. The frontend `middleware.ts` only checks that a Supabase cookie is *present* — it never verifies it, and it does not cover `/api/*` at all. Combined with **secrets committed to git and hardcoded crypto keys shipped to the browser**, the security posture is the dominant theme of this review. Four of the five criticals are facets of these two root causes.

---

## 🔴 CRITICAL (5 — all confirmed with code traces)

| # | Finding | Location |
|---|---|---|
| 1 | **Unauthenticated SSRF + arbitrary headless browser.** `GET /debug/capture?url=` drives Chromium to *any* attacker URL (no auth, no scheme/host allow-list) and reflects the first 1000 chars back. Reaches cloud metadata (`169.254.169.254`) and internal services. | `backend_python/main/routes/debug_routes.py:17-62` |
| 2 | **The entire `/debug` router is unauthenticated and always mounted** — no `DEV_MODE`/prod gate. Exposes the SSRF above plus screenshot/HTML-dump/scraper-image endpoints to anyone. | `backend_python/main/main.py:54` |
| 3 | **Live LinkedIn session secrets committed to the remote repo.** `data_dump/cookies.json` contains a real `li_at` (`AQEDAV0MKDkC…`) + `JSESSIONID` + `liap` + full jar; `localStorage.json`/`sessionStorage.json` too. In git **history** across 3 commits — `.gitignore` lists them but they are already tracked, so it does nothing. **This is a breach.** | `backend_python/data_dump/cookies.json` |
| 4 | **IDOR on `/api/User`.** GET with any `?id=` returns another user's full row (resume_url, linkedin_context, applied_jobs); POST allows insert/update/upsert of any user by id. Zero session check; middleware does not cover the route. | `my-fe/app/api/User/route.ts:34-103` |
| 5 | **LinkedIn passwords "encrypted" with a hardcoded key + static IV, recoverable in the browser.** AES-256-CBC key `qwertyuiop…987456` + fixed IV `741852963qwerty0` + JWT secret `1w3r5y7i…` are string literals — *the same literals are shipped in client JS* (`Jobs.tsx`, `Apply.tsx`), so anyone can decrypt stored credentials. | `my-fe/app/api/store/route.ts:13-35` |

**Immediate breach response for #3 + #5:** log out all LinkedIn sessions / rotate the password to invalidate `li_at`; rotate the JWT/AES secrets; `git rm --cached` the three files and purge history (BFG / `git filter-repo`), then force-push.

---

## 🟠 HIGH (11 — confirmed/partial)

**Credential & secret handling (one systemic root cause, 5 facets):**
- JWT/AES secrets used as **hardcoded fallback defaults** — `get-data/route.ts:4` falls back to the literal; `store/route.ts:32` hardcodes it unconditionally. — `my-fe/app/api/get-data/route.ts:4`
- **Signer/verifier secret mismatch:** `/api/store` signs with the literal, `/api/get-data` prefers `process.env.JWT_SECRET` → if the env var is set (docs say it should be), every token 401s. — `my-fe/app/api/store/route.ts:32-35`
- Hardcoded **AES key+IV in the client bundle** (`Jobs.tsx:144-153`, dup `Apply.tsx:129-130`) — the "encryption" is decorative.
- `Linkedin.tsx` **POSTs the plaintext LinkedIn password** to that endpoint. — `my-fe/app/Components/Linkedin.tsx:14-22`
- `/logout` is **unauthenticated** and clears the LinkedIn context for any caller-supplied `user_id`. — `backend_python/main/routes/logout.py:12-20`

**Other SSRF:** `/portfolio` and `/tailor` fetch a client-supplied `resume_url` server-side with no host/scheme validation. — `backend_python/main/routes/portfolio_generator.py:43-56`

**Correctness bugs that break core flows:**
- **Auto-apply submits wrong answers:** when no dropdown option matches, it blindly `select_option(index=1)` — the 2nd option — for *any* question (work-authorization, experience, notice period). — `backend_python/agents/apply_agent.py:835-838`
- **Worker writes `last_active_at: "now()"` as a literal string** through PostgREST; Postgres rejects `'now()'` (with parens) as a timestamp → the update errors and, with try/finally and no `except`, crashes the worker right after flipping to `running`, stranding the job. — `backend_python/worker.py:132-135,143-145`
- **Scraper fetches job-detail pages with no auth cookies** — the entire cookie-injection block is commented out, so authenticated descriptions routinely fail to extract. — `backend_python/agents/scraper_agent.py:883-908`
- **`/tailor` 500s when `template` is omitted:** `process_batch` does `if template >= 0` but the route forwards `template=None` → `TypeError`. — `backend_python/agents/tailor.py:529-534`
- **`Linkedin.tsx` reports success on failure:** success toast gated on `res.ok || uploadStatus`, and `uploadStatus` flips true on button click — so a 4xx/5xx still shows "Successfully submitted." — `my-fe/app/Components/Linkedin.tsx:14-32`

---

## 🟡 MEDIUM (19) — grouped

- **Orchestration:** 30s synchronous Redis latch holds an API worker per `/start` (`jobs_api.py:164-183`); TOCTOU on the 429 stale-resume branch picks `active_res.data[0]` with no ordering (`jobs_api.py:277-294`); `last_active_at` never refreshed mid-pipeline, so a Redis outage misclassifies long jobs as stale and can spawn a **duplicate worker** on the same `job_id` (partial — Redis-up is protected by a 10s heartbeat loop).
- **Portfolio agent (`portfolio_agent.py`):** `url.lower` referenced without `()` → `AttributeError` on non-PDF URLs (`:2056`); per-request mutation of module-global `_TAMPLATE` **races under concurrency** (`:2062-2134`); template `0` silently ignored via falsy guard; fetch failure swallowed → `None` → opaque 500.
- **Apply agent:** form submitted even when answers are guessed (`:1069-1083`); `finally` references possibly-unbound `context`, masking the real exception (`:1343-1493`).
- **Schema drift (data-integrity):** `schema.sql` says table `users`, all code uses `"User"`; Prisma schema **omits the `one_active_job_per_user` index** that the whole 429 rate-limit depends on.
- **Frontend:** `Register.tsx` sends `user_metadata.sub` instead of `user.id` to the insert (`:61-69`); `Apply.tsx` "done" handler requires `progress===100` but the DB-fallback "done" omits progress → UI can hang at running (`:463-505`).
- **Resilience:** `parse_agent.parse_pdf` does `requests.get` with **no timeout** → worker can hang indefinitely (`:464-467`).
- **Infra:** extension exfiltrates the full cookie jar every 2 min to a hardcoded `localhost` endpoint (partial); frontend `Dockerfile` uses EOL `node:19`, `npm install` not `npm ci`, runs as root.

---

## ✅ What the verifiers REFUTED (do not chase these)

The adversarial pass killed two plausible-looking findings — noted so they do not resurface:
1. *"Reconnect can reattach without a live SSE stream"* — **refuted**: the `"started"` event is read with `LRANGE` (not popped), so it persists in `stream:{job_id}`; a late SSE client still sees it.
2. *"`parse_pdf` validity check is always-true so every resume fails"* — **refuted**: a markdown rendering artifact. The code counts a PUA bullet glyph (`\xef\x82\xb7`), not the empty string; it is conditional, not always-true.

---

## 🧹 Dead code & hygiene

- **Dead modules:** `my-fe/app/utiles/agentsCall.ts` (calls removed `/get-jobs`,`/apply-jobs`, no importers); `backend_python/lib/session_manager.py`; `data_dump/apply.py` (ships `--disable-web-security --no-sandbox`).
- **The Groq client in `apply_agent.py` is never used** — form answering is pure keyword matching despite the "LLM-driven" framing. Same dead-LLM-client pattern in `tailor.py`.
- **45MB of committed binaries** (`tesseract…exe` 21M, `extract.zip` 16M, screenshots) bloat every clone.
- `.gitignore` has **duplicate lines** (25/27, 26/28); `requirements.txt` has **0 of 23 deps pinned**.
- **Doc drift vs CLAUDE.md:** Prisma migrations *do* exist (`my-fe/prisma/migrations/`); invalid model id `gemini-3.1-flash-lite` left in `tailor.py`; `my-fe/..env` (malformed name) is untracked **and not matched by the `.env` ignore rule** → one `git add .` from leaking.

---

## Remediation order

1. **Breach response (today):** invalidate the leaked `li_at`/LinkedIn session, rotate JWT+AES secrets, scrub the 3 secret files from history + force-push.
2. **Kill the attack surface:** gate `/debug` behind `DEV_MODE` (or delete it); add server-side auth to `/api/User`, `/logout`, `/portfolio`, `/tailor` deriving `user_id` from a verified session, not the request body.
3. **Stop shipping crypto to the browser:** move key/IV/JWT to server-only env; have the worker read credentials by user id; drop client-side decryption.
4. **Fix the correctness landmines:** dropdown `index=1` fallback (wrong applications submitted), `last_active_at:"now()"`, `/tailor` template `None` crash, scraper cookie injection.
5. **Hardening/cleanup:** SSRF allow-lists, request timeouts, the `_TAMPLATE` global race, schema/Prisma index drift, then dead code + binary purge.

---

The two highest-leverage structural fixes — **a real auth dependency on the backend** and **removing all hardcoded/committed secrets** — collapse 9 of the 16 critical+high findings at once.
