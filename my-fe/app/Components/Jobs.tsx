"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import JobCards from "./JobCards";
import CryptoJS from "crypto-js";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";
import { sampleJobs } from "./sampleJobs";
import { SSEManager } from "../utiles/sseManager";
import { appendFetchedJobs, clearFetchedJobs, getFetchedJobs, saveFetchedJobs } from "../utiles/jobStorage";
import { useUser } from "../utiles/UserContext";
import { UpgradePopup } from "./UpgradePopup";

const USE_SAMPLE_DATA = false;

interface LogEntry {
  id: number;
  message: string;
  type: string;
  timestamp: number;
}

/* ── Phase label from status ─────────────────────────────── */
function getPhaseLabel(type: string, message: string = ""): string {
  const msg = message.toLowerCase();
  if (msg.includes("analyzing") || msg.includes("extracting") || type === "batch_ready") return "Analyzing";
  if (msg.includes("scraping") || msg.includes("searching") || type === "in_progress") return "Scraping";
  if (type === "done") return "Completed";
  if (type === "error") return "Error";
  return "Initialized";
}

/* ── Elapsed timer ──────────────────────────────────────── */
function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}


function formatCacheAge(ageMs: number | null): string {
  if (ageMs === null || !Number.isFinite(ageMs)) return "some time ago";

  const minutes = Math.floor(ageMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;

  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

/* ── SVG icons ──────────────────────────────────────────── */
const CheckIcon = () => (
  <svg className="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
);
const ErrorIcon = () => (
  <svg className="w-3.5 h-3.5 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
  </svg>
);
const SpinnerIcon = () => (
  <div className="w-3.5 h-3.5 rounded-full border-2 border-emerald-400/30 border-t-emerald-400 animate-spin shrink-0" />
);
const DotIcon = () => (
  <div className="w-2 h-2 rounded-full bg-gray-500 shrink-0 mt-[3px]" />
);

// Match the backend's normalize_job_url (split('?')[0]) so frontend exclusion of
// already-applied jobs lines up with the normalized URLs stored in User.applied_jobs.
function normalizeUrl(url: any): string {
  return typeof url === "string" ? url.split("?")[0].trim() : "";
}

function buildJobKey(job: any, index: number): string {
  if (job && typeof job === "object") {
    if (typeof job.job_url === "string" && job.job_url.trim()) {
      return `url:${job.job_url.trim()}`;
    }
    if (typeof job.job_id === "string" && job.job_id.trim()) {
      return `id:${job.job_id.trim()}`;
    }
  }
  return `fallback:${index}`;
}

function mergeUniqueJobs(current: any[], incoming: any[]): any[] {
  const map = new Map<string, any>();
  [...current, ...incoming].forEach((job, index) => {
    map.set(buildJobKey(job, index), job);
  });
  return Array.from(map.values());
}

/* ── Log entry component ─────────────────────────────────── */
const LogItem = ({ entry, isLatest }: { entry: LogEntry; isLatest: boolean }) => {
  const icon = entry.type === "done" ? <CheckIcon />
    : entry.type === "error" ? <ErrorIcon />
      : isLatest ? <SpinnerIcon />
        : <DotIcon />;

  return (
    <div
      className={`flex items-start gap-2.5 py-1.5 px-1 transition-all duration-500 animate-[fadeSlideIn_0.35s_ease-out]
        ${isLatest ? "text-gray-200" : "text-gray-500"}`}
    >
      <div className="mt-[2px]">{icon}</div>
      <span className={`text-[13px] leading-snug break-words ${isLatest ? "text-gray-200" : "text-gray-500"}`}>
        {entry.message}
      </span>
    </div>
  );
};

const Jobs = () => {
  const router = useRouter();
  const { user, loading: userLoading } = useUser();
  const hasStarted = useRef(false);

  const [activityLog, setActivityLog] = useState<LogEntry[]>([]);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState("Preparing");
  const [jobs, setJobs] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [Progress_userId, setProgress_UserId] = useState("");
  const [credentialsReady, setCredentialsReady] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showRestorePrompt, setShowRestorePrompt] = useState(false);
  const [cacheCheckComplete, setCacheCheckComplete] = useState(false);
  const [recoveredJobId, setRecoveredJobId] = useState<string | null>(null);
  const [recentCachedJobs, setRecentCachedJobs] = useState<any[] | null>(null);
  const [recentCacheAgeLabel, setRecentCacheAgeLabel] = useState("some time ago");
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [estimatedWait, setEstimatedWait] = useState<string | null>(null);

  // ── Job filters (Keyword / Job type / Experience) ──
  const [keyword, setKeyword] = useState("");
  const [jobTypeFilter, setJobTypeFilter] = useState<string[]>([]);
  const [experienceFilter, setExperienceFilter] = useState("");

  const logEndRef = useRef<HTMLDivElement>(null);
  const startTime = useRef(Date.now());
  const accumulatedJobs = useRef<any[]>([]);
  const sseRef = useRef<SSEManager | null>(null);
  const jobsContainerRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);
  const seenLogMessages = useRef<Set<string>>(new Set());

  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456";
  const IV = "741852963qwerty0";

  function decryptData(ciphertext: string, keyStr: string, ivStr: string) {
    const key = CryptoJS.enc.Utf8.parse(keyStr);
    const iv = CryptoJS.enc.Utf8.parse(ivStr);
    return CryptoJS.AES.decrypt(ciphertext, key, {
      iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7,
    }).toString(CryptoJS.enc.Utf8);
  }

  /* push to log — deduplicate to prevent replays on SSE reconnect */
  function pushLog(message: string, type: string) {
    const dedupeKey = `${type}::${message}`;
    if (seenLogMessages.current.has(dedupeKey)) return;
    seenLogMessages.current.add(dedupeKey);

    setActivityLog(prev => {
      const nextId = prev.length > 0 ? prev[prev.length - 1].id + 1 : 1;
      return [...prev, { id: nextId, message, type, timestamp: Date.now() }];
    });
    setPhase(getPhaseLabel(type, message));
  }

  /* Elapsed timer */
  useEffect(() => {
    if (isDone || error) return;
    const iv = setInterval(() => setElapsed(Math.floor((Date.now() - startTime.current) / 1000)), 1000);
    return () => clearInterval(iv);
  }, [isDone, error]);

  /* Auto-scroll log — only scroll the log container, not the whole page */
  useEffect(() => {
    const container = logEndRef.current?.parentElement;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [activityLog]);

  // Effect 1 — progress user id
  useEffect(() => {
    async function loadUser() {
      const { data } = await getLoginUser();
      if (data?.user) setProgress_UserId(data.user.user_metadata.email);
      else {
        const email = sessionStorage.getItem("email");
        if (email) setProgress_UserId(email);
      }
    }
    loadUser();
  }, []);

  // Effect 2 — resume url + credentials
  useEffect(() => {
    // Wait for UserContext to finish loading before reading user data
    if (userLoading) return;

    // Read from user context instead of sessionStorage to avoid race conditions
    const pdf = user.resume_url;
    const context = user.linkedin_context;

    if (!pdf) {
      toast.error("Resume not found. Please upload your resume", { id: "resume-missing" });
      router.push("/");
      return;
    }
    setUrl(pdf);

    async function fetchCredentials() {
      if (user.tier !== "PRO") {
        setCredentialsReady(true);
        return;
      }
      try {
        const res = await fetch("/api/get-data", { method: "GET", credentials: "include" });
        const json = await res.json();
        if (json.encryptedData) {
          const creds = JSON.parse(decryptData(json.encryptedData, ENC_KEY, IV));
          setUserId(creds.username);
          setPassword(creds.password);
          setCredentialsReady(true);
        } else {
          toast.error("Please connect to Connector");
          setIsDone(true);
          setError("Please connect");
        }
      } catch (e: any) {
        toast.error("Error fetching credentials: " + e.message);
        setIsDone(true);
        setError("Error fetching credentials: " + e.message);
      }
    }

    if (!context) fetchCredentials();
    else setCredentialsReady(true);
  }, [userLoading, user]);

  // Effect 3 — restore cached jobs OR reconnect to active job
  useEffect(() => {
    let cancelled = false;

    async function checkActiveOrCached() {
      if (!Progress_userId) return; // Wait until user is loaded

      try {
        const activeRes = await fetch(`${API_URL}/api/jobs/active?user_id=${encodeURIComponent(Progress_userId)}&workflow_type=fetch_jobs`);
        if (activeRes.ok) {
          const statusData = await activeRes.json();
          const { job_id, status, output_data, last_active_at } = statusData;

          if (job_id) {
            if (status === "completed") {
              const outputJobs = Array.isArray(output_data) ? output_data : (output_data?.jobs || []);
              if (outputJobs.length > 0) {
                // Show these as restorable — let the user decide whether to
                // view these results or start a fresh fetch.
                const serverTime = last_active_at ? new Date(last_active_at).getTime() : 0;
                const ageMs = serverTime > 0 ? Math.max(0, Date.now() - serverTime) : null;

                if (!cancelled) {
                  setRecentCachedJobs(outputJobs);
                  setRecentCacheAgeLabel(formatCacheAge(ageMs));
                  setCacheCheckComplete(true);
                }
                return;
              }
              // Completed but empty output → allow fresh start
              if (!cancelled) setCacheCheckComplete(true);
              return;
            }

            if (status === "failed") {
              if (!cancelled) setCacheCheckComplete(true);
              return;
            }

            if (status === "running" || status === "pending" || status === "scraper_raw") {
              if (!cancelled) {
                pushLog("Reconnecting to active job...", "processing");
                setRecentCachedJobs(null);
                setRecoveredJobId(job_id);
                setCacheCheckComplete(true);
              }
              return; // Don't fall through to IndexedDB
            }
          }
        }
      } catch (err) {
        console.error("Failed to check active job on server:", err);
      }

      // No server session (or server unreachable) — check IndexedDB as fallback
      try {
        const cached = await getFetchedJobs();
        if (cancelled) return;

        if (cached?.jobs?.length) {
          const fetchedAt = typeof cached.fetchedAt === "number" ? cached.fetchedAt : 0;
          const ageMs = fetchedAt > 0 ? Math.max(0, Date.now() - fetchedAt) : null;

          setRecentCachedJobs(cached.jobs);
          setRecentCacheAgeLabel(formatCacheAge(ageMs));
        }

        if (!cancelled) setCacheCheckComplete(true);
      } catch (err) {
        console.error("Failed to restore cached jobs:", err);
        if (!cancelled) setCacheCheckComplete(true);
      }
    }

    checkActiveOrCached();
    return () => {
      cancelled = true;
    };
  }, [Progress_userId]);

  // Effect 4 — cleanup stream resources on unmount
  useEffect(() => {
    return () => {
      sseRef.current?.destroy();
      sseRef.current = null;
    };
  }, []);

  // Effect 5 — Start Job & Open SSE stream
  useEffect(() => {
    if (!cacheCheckComplete) return;
    if (recentCachedJobs) return;
    if (!url || !Progress_userId || !credentialsReady) return;
    if (hasStarted.current) return;
    hasStarted.current = true;
    startTime.current = Date.now();

    async function triggerJob() {
      // Tier Check - only deduct credits for fresh searches, not reconnected/restored ones
      if (user?.tier === "FREE" && !recoveredJobId) {
        if ((user?.fetch_jobs_credits || 0) <= 0) {
          setPopupMessage("You have exhausted your daily limit of 2 job fetches. Upgrade to Pro for unlimited job searches!");
          setShowPopup(true);
          setIsDone(true);
          setError("Fetch limit reached");
          return;
        }

        // Deduct credit before processing
        try {
          await fetch("/api/User?action=deduct_credit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: user.id, type: "fetch" })
          });
          if (user.fetch_jobs_credits) user.fetch_jobs_credits -= 1;
        } catch (err) {
          console.error("Failed to deduct credit:", err);
        }
      }

      try {
        let activeJobId = recoveredJobId;

        if (!activeJobId) {
          pushLog("Initiating job container...", "processing");
          const res = await fetch(`${API_URL}/api/jobs/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: Progress_userId,
              workflow_type: 'fetch_jobs',
              input_data: {
                user_id: Progress_userId,
                resume_url: url,
                ...(userId && { linkedin_id: userId }),
                ...(password && { linkedin_password: password })
              }
            })
          });

          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Failed to start job");
          }

          const data = await res.json();
          activeJobId = data.job_id;
        }

        setRecoveredJobId(activeJobId);

        // 2. Open SSE progress stream
        const manager = new SSEManager({
          url: `${API_URL}/api/jobs/stream?job_id=${activeJobId}`,
          reconnectBaseDelayMs: 1_500,
          reconnectMaxDelayMs: 12_000,
          withCredentials: true,
        });
        sseRef.current = manager;

        manager.onTerminalError = (message) => {
          setError(message);
          pushLog(message, "error");
          toast.error(message);
          setIsDone(true);
        };

        manager.onEvent = async (evData: any) => {
          if (evData?.error || evData?.progress === -1 || evData?.status === "error") {
            manager.destroy();
            setError(evData.error || evData.message || "Failed to fetch jobs");
            pushLog(evData.message || evData.error || "Process interrupted", "error");
            toast.error(evData.error || evData.message || "Something went wrong");
            setIsDone(true);
            return;
          }

          if (evData?.status === "queued") {
            setQueuePosition(evData.queue_position);
            setEstimatedWait(evData.estimated_wait);
            setPhase("Queued");
            return;
          } else {
            // Unconditionally clear queue state for any non-queued progress updates (avoids stale closures)
            setQueuePosition(null);
            setEstimatedWait(null);
          }

          if (typeof evData?.progress === "number") {
            setProgress(evData.progress);
          }

          if (evData?.message) {
            pushLog(evData.message, evData.status || "processing");
          }

          if (evData?.status === "batch_ready" && Array.isArray(evData.jobs) && evData.jobs.length > 0) {
            accumulatedJobs.current = mergeUniqueJobs(accumulatedJobs.current, evData.jobs);
            // Preserve scroll position before update
            if (jobsContainerRef.current) {
              scrollPositionRef.current = window.scrollY;
            }
            setJobs([...accumulatedJobs.current]);
            // Restore scroll position after React re-render
            requestAnimationFrame(() => {
              window.scrollTo(0, scrollPositionRef.current);
            });
            await appendFetchedJobs(evData.jobs);
          }

          if (evData?.status === "done") {
            manager.destroy();
            const fetched = Array.isArray(evData.jobs) ? evData.jobs : [];

            if (fetched.length > 0) {
              await saveFetchedJobs(fetched);
              accumulatedJobs.current = mergeUniqueJobs(accumulatedJobs.current, fetched);
            }
            // Preserve scroll position before update
            if (jobsContainerRef.current) {
              scrollPositionRef.current = window.scrollY;
            }
            setJobs([...accumulatedJobs.current]);
            // Restore scroll position after React re-render
            requestAnimationFrame(() => {
              window.scrollTo(0, scrollPositionRef.current);
            });
            setProgress(100);
            setIsDone(true);
          }
        };
      } catch (err: any) {
        setError(err.message || "Failed to initialize pipeline");
        pushLog(err.message || "Initialization failed", "error");
        setIsDone(true);
      }
    }

    triggerJob();

  }, [cacheCheckComplete, recentCachedJobs, url, Progress_userId, credentialsReady, retryCount]);

  function handleUseRecentJobs() {
    if (!recentCachedJobs?.length) return;

    accumulatedJobs.current = recentCachedJobs;
    setJobs(recentCachedJobs);
    setProgress(100);
    setIsDone(true);
    setShowRestorePrompt(true);
    setRecentCachedJobs(null);
    pushLog("Showing recently fetched jobs from your previous session.", "done");
    hasStarted.current = true;
  }

  function handleFreshRequestFromPrompt() {
    setRecentCachedJobs(null);
    setRecentCacheAgeLabel("some time ago");
    handleRetry();
  }

  /* ── Retry handler ── */
  function handleRetry() {
    sseRef.current?.destroy();
    sseRef.current = null;
    hasStarted.current = false;
    accumulatedJobs.current = [];
    seenLogMessages.current.clear();
    void clearFetchedJobs();
    setShowRestorePrompt(false);
    setRecentCachedJobs(null);
    setRecentCacheAgeLabel("some time ago");
    setError(null);
    setJobs(null);
    setIsDone(false);
    setActivityLog([]);
    setProgress(0);
    setElapsed(0);
    startTime.current = Date.now();
    setRetryCount(c => c + 1);
  }

  // Exclude already-applied jobs (frontend guard for the IndexedDB cache; the backend
  // already filters them at scrape time), then apply the active filters.
  const appliedSet = useMemo(
    () => new Set((user.applied_jobs || []).map(normalizeUrl)),
    [user.applied_jobs]
  );
  const baseJobs: any[] = useMemo(
    () => (Array.isArray(jobs) ? jobs.filter((j) => !appliedSet.has(normalizeUrl(j?.job_url))) : []),
    [jobs, appliedSet]
  );
  const jobTypeOptions = useMemo(
    () => Array.from(new Set(baseJobs.map((j) => String(j?.job_type || "").trim()).filter(Boolean))).sort(),
    [baseJobs]
  );
  const experienceOptions = useMemo(
    () =>
      Array.from(
        new Set(
          baseJobs
            .map((j) => String(j?.experience || "").trim())
            .filter((v) => v && v.toLowerCase() !== "not specified")
        )
      ).sort(),
    [baseJobs]
  );
  const visibleJobs = useMemo(() => {
    const kw = keyword.trim().toLowerCase();
    return baseJobs.filter((j) => {
      if (kw) {
        const skills = Array.isArray(j?.key_skills) ? j.key_skills.join(" ") : "";
        const hay = `${j?.title || ""} ${j?.company_name || ""} ${skills}`.toLowerCase();
        if (!hay.includes(kw)) return false;
      }
      if (jobTypeFilter.length && !jobTypeFilter.includes(String(j?.job_type || "").trim())) return false;
      if (experienceFilter && String(j?.experience || "").trim() !== experienceFilter) return false;
      return true;
    });
  }, [baseJobs, keyword, jobTypeFilter, experienceFilter]);

  const filtersActive = keyword.trim() !== "" || jobTypeFilter.length > 0 || experienceFilter !== "";
  const toggleJobType = (t: string) =>
    setJobTypeFilter((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  const clearFilters = () => {
    setKeyword("");
    setJobTypeFilter([]);
    setExperienceFilter("");
  };

  if (!userLoading && !user?.resume_url) {
    return null;
  }

  return (
    <div className="flex flex-col min-h-screen relative">

      <UpgradePopup isOpen={showPopup} onClose={() => setShowPopup(false)} message={popupMessage} />

      {!userLoading && user?.tier === "FREE" && (
        <div className="fixed bottom-6 right-6 bg-[#1A1A1A] border border-white/[0.08] text-gray-400 text-xs px-4 py-2 rounded-full font-medium z-50 shadow-2xl flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          Credits: {user?.fetch_jobs_credits || 0}/2
        </div>
      )}

      {/* ─── Activity Feed Panel (top on mobile, sidebar on desktop) ── */}
      <div className={`shrink-0 w-full lg:fixed lg:top-[65px] lg:left-0 lg:h-[calc(100vh-65px)] lg:overflow-hidden bg-[#111] border-b lg:border-b-0 lg:border-r border-white/[0.06] cursor-default z-10 flex flex-col transition-all duration-300 ${sidebarOpen ? "lg:w-72" : "lg:w-12"
        }`}>

        {/* Header + progress */}
        <div className={`px-4 pt-5 pb-3 sm:px-6 ${sidebarOpen ? "lg:px-5" : "lg:px-2 lg:pt-4 lg:pb-2"}`}>
          <div className="flex items-center justify-between mb-3">
            <div className={`flex items-center gap-2.5 ${!sidebarOpen ? "lg:justify-center lg:w-full" : ""}`}>
              {!isDone && !error ? (
                <div className="rounded-full border-2 border-emerald-400/30 border-t-emerald-400 animate-spin shrink-0" style={{ width: 18, height: 18 }} />
              ) : isDone && !error ? (
                <svg className="w-[18px] h-[18px] text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
                </svg>
              ) : (
                <svg className="w-[18px] h-[18px] text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
                </svg>
              )}
              <h3 className={`text-sm font-semibold text-gray-200 tracking-tight ${!sidebarOpen ? "lg:hidden" : ""}`}>
                {isDone && !error ? "Jobs ready" : error ? "Search interrupted" : "Discovering jobs"}
              </h3>
            </div>
            <div className={`flex items-center gap-3 text-xs text-gray-500 ${!sidebarOpen ? "lg:hidden" : ""}`}>
              <span className="hidden sm:inline lg:hidden xl:inline px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-gray-400">
                {phase}
              </span>
              <span className="tabular-nums">{formatElapsed(elapsed)}</span>
            </div>
            {/* Collapse/expand toggle — desktop only */}
            <button
              onClick={() => setSidebarOpen(p => !p)}
              className="hidden lg:flex items-center justify-center w-6 h-6 rounded hover:bg-white/[0.06] text-gray-500 hover:text-gray-300 transition-colors"
              title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              <svg className={`w-4 h-4 transition-transform duration-300 ${sidebarOpen ? "" : "rotate-180"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>

          {/* Progress bar */}
          <div className={`w-full h-1 bg-white/[0.06] rounded-full overflow-hidden ${!sidebarOpen ? "lg:mt-2" : ""}`}>
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${error ? "bg-red-500" : isDone ? "bg-emerald-500" : "bg-emerald-500/80"
                }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          {/* Stats */}
          {jobs && jobs.length > 0 && (
            <div className={`flex gap-4 mt-2.5 text-xs ${!sidebarOpen ? "lg:hidden" : ""}`}>
              <span className="text-emerald-400 tabular-nums">{jobs.length} jobs found</span>
              <span className="text-gray-500 tabular-nums">{progress}%</span>
            </div>
          )}
        </div>

        {/* Scrollable activity log — hidden when collapsed on desktop */}
        <div className={`max-h-40 sm:max-h-48 lg:max-h-none lg:flex-1 overflow-y-auto px-4 pb-4 sm:px-6 lg:px-5 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10 ${!sidebarOpen ? "lg:hidden" : ""}`}>
          {activityLog.length === 0 && !error && (
            <div className="flex items-center gap-2 py-2 text-xs text-gray-600">
              <div className="w-3 h-3 rounded-full border border-gray-700 border-t-gray-500 animate-spin" />
              <span>Preparing to start...</span>
            </div>
          )}
          {activityLog.map((entry, i) => (
            <LogItem key={entry.id} entry={entry} isLatest={i === activityLog.length - 1 && !isDone && !error} />
          ))}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* ─── Job Cards Area ───────────────────────────────────── */}
      <div ref={jobsContainerRef} className={`flex-1 p-4 md:p-6 lg:p-8 transition-all duration-300 ${sidebarOpen ? "lg:ml-72" : "lg:ml-12"
        }`}>
        {USE_SAMPLE_DATA ? (
          <JobCards jobs={sampleJobs as any} />
        ) : queuePosition !== null ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="surface-card p-8 border border-emerald-500/30 bg-emerald-500/[0.03] text-center max-w-md w-full shadow-2xl rounded-2xl">
              <div className="w-16 h-16 rounded-full border-4 border-emerald-500/30 border-t-emerald-500 animate-spin mx-auto mb-6"></div>
              <h2 className="text-xl font-bold text-white mb-2">Priority Desk</h2>
              <p className="text-emerald-300 font-medium mb-4">
                Estimated Wait: <span className="text-white">{estimatedWait}</span>
              </p>
              {user?.tier !== "PRO" && (
                <div className="bg-[#1A1A1A] p-5 rounded-xl border border-white/[0.08] mt-6 shadow-inner">
                  <button
                    onClick={() => { window.location.href = "mailto:tejabudumuru3@gmail.com?subject=Interested%20in%20HireHawk%20Pro%20Plan&body=Hi%2C%0A%0AI%20am%20interested%20in%20upgrading%20to%20the%20HireHawk%20Pro%20Plan.%20Please%20let%20me%20know%20the%20next%20steps.%0A%0AThanks!"; }}
                    className="w-full px-4 py-3.5 bg-white/[0.04] border border-white/[0.1] text-gray-200 font-bold rounded-xl shadow-lg hover:bg-white/[0.08] backdrop-blur-md transition-all cursor-pointer hover:shadow-white/[0.05]"
                  >
                    Skip the wait with Pro
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="surface-card p-8 border border-red-500/30 text-center max-w-md">
              <p className="text-red-400 font-medium mb-2">Failed to load jobs</p>
              <p className="text-gray-400 text-sm mb-4">{error}</p>
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/20 transition"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : recentCachedJobs && recentCachedJobs.length > 0 ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="surface-card p-7 sm:p-8 border border-emerald-500/30 bg-emerald-500/[0.03] max-w-lg w-full">
              <p className="text-emerald-300 font-semibold text-lg">Saved jobs are available</p>
              <p className="text-gray-300/90 text-sm mt-2 leading-relaxed">
                We found previously fetched jobs from {recentCacheAgeLabel}. Do you want to continue with these saved results or run a fresh search now?
              </p>
              <div className="mt-5 flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleUseRecentJobs}
                  className="px-4 py-2.5 rounded-lg border border-white/[0.12] bg-white/[0.04] text-gray-200 text-sm font-medium hover:bg-white/[0.08] transition"
                >
                  Continue with Saved Jobs
                </button>
                <button
                  onClick={handleFreshRequestFromPrompt}
                  className="px-4 py-2.5 rounded-lg border border-emerald-400/40 bg-emerald-500/10 text-emerald-300 text-sm font-medium hover:bg-emerald-500/20 transition"
                >
                  Fetch Fresh Jobs
                </button>
              </div>
            </div>
          </div>
        ) : jobs && jobs.length > 0 ? (
          <>
            {showRestorePrompt && (
              <div className="mb-5 rounded-xl border border-emerald-500/25 bg-emerald-500/[0.06] px-4 py-3 sm:px-5 sm:py-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-emerald-300">Showing saved results from your previous search</p>
                    <p className="mt-1 text-xs text-emerald-200/75">
                      Want the latest listings? Start a fresh request to run a new job search.
                    </p>
                  </div>
                  <button
                    onClick={handleRetry}
                    className="inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/10 px-3.5 py-2 text-xs font-medium text-emerald-300 transition hover:bg-emerald-500/20 hover:text-emerald-200"
                  >
                    Request Fresh Jobs
                  </button>
                </div>
              </div>
            )}
            {baseJobs.length > 0 && (
              <div className="mb-5 flex flex-col gap-3 rounded-2xl border border-white/[0.06] bg-[#0A0A0A]/60 p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="Search title, company, or skills..."
                    className="flex-1 min-w-[180px] rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-emerald-500/40"
                  />
                  {experienceOptions.length > 0 && (
                    <select
                      value={experienceFilter}
                      onChange={(e) => setExperienceFilter(e.target.value)}
                      className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-gray-200 outline-none focus:border-emerald-500/40"
                    >
                      <option value="">Any experience</option>
                      {experienceOptions.map((exp) => (
                        <option key={exp} value={exp}>{exp}</option>
                      ))}
                    </select>
                  )}
                  {filtersActive && (
                    <button
                      onClick={clearFilters}
                      className="text-xs text-gray-400 px-3 py-2 rounded-lg border border-white/[0.08] hover:text-white hover:bg-white/[0.04] transition"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
                {jobTypeOptions.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs text-gray-500 mr-1">Type:</span>
                    {jobTypeOptions.map((t) => (
                      <button
                        key={t}
                        onClick={() => toggleJobType(t)}
                        className={`text-xs px-3 py-1.5 rounded-full border transition ${jobTypeFilter.includes(t)
                          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                          : "border-white/[0.08] text-gray-400 hover:text-white hover:bg-white/[0.04]"
                          }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            {!isDone ? (
              <p className="text-xs text-emerald-400/60 mb-4">
                {visibleJobs.length} of {baseJobs.length} jobs{filtersActive ? " match" : ""} — still searching for more...
              </p>
            ) : filtersActive ? (
              <p className="text-xs text-gray-500 mb-4">
                {visibleJobs.length} of {baseJobs.length} jobs match your filters
              </p>
            ) : null}
            {visibleJobs.length > 0 ? (
              <JobCards jobs={visibleJobs} />
            ) : (
              <div className="flex items-center justify-center min-h-[30vh]">
                <p className="text-gray-500 text-sm">
                  {baseJobs.length === 0
                    ? "You've already applied to all of these jobs."
                    : "No jobs match your filters."}
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center min-h-[60vh] lg:min-h-[80vh]">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
              <p className="text-gray-400 text-sm">Finding the best jobs for you...</p>
            </div>
          </div>
        )}
      </div>

      {/* ── Keyframe animation ──────────────────────────────── */}
      <style jsx>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateY(6px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default Jobs;