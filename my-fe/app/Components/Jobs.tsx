"use client";
import React, { useEffect, useRef, useState } from "react";
import JobCards from "./JobCards";
import CryptoJS from "crypto-js";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";
import { sampleJobs } from "./sampleJobs";
import { SSEManager } from "../utiles/sseManager";
import { appendFetchedJobs, clearFetchedJobs, getFetchedJobs, saveFetchedJobs } from "../utiles/jobStorage";

const USE_SAMPLE_DATA = false;

interface LogEntry {
  id: number;
  message: string;
  type: string;
  timestamp: number;
}

/* ── Phase label from status ─────────────────────────────── */
function getPhaseLabel(type: string): string {
  switch (type) {
    case "processing": return "Processing";
    case "searching": return "Searching";
    case "analyzing": return "Analyzing";
    case "batch_ready": return "Extracting";
    case "done": return "Complete";
    case "error": return "Error";
    default: return "Working";
  }
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
  const hasStarted = useRef(false);

  const [activityLog, setActivityLog] = useState<LogEntry[]>([]);
  const [progress, setProgress]       = useState(0);
  const [phase, setPhase]             = useState("Initializing");
  const [jobs, setJobs]               = useState<any>(null);
  const [error, setError]             = useState<string | null>(null);
  const [url, setUrl]                 = useState("");
  const [userId, setUserId]           = useState("");
  const [password, setPassword]       = useState("");
  const [Progress_userId, setProgress_UserId] = useState("");
  const [credentialsReady, setCredentialsReady] = useState(false);
  const [isDone, setIsDone]           = useState(false);
  const [elapsed, setElapsed]         = useState(0);
  const [retryCount, setRetryCount]   = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showRestorePrompt, setShowRestorePrompt] = useState(false);
  const [cacheCheckComplete, setCacheCheckComplete] = useState(false);
  const [recentCachedJobs, setRecentCachedJobs] = useState<any[] | null>(null);
  const [recentCacheAgeLabel, setRecentCacheAgeLabel] = useState("some time ago");

  const logEndRef  = useRef<HTMLDivElement>(null);
  const startTime  = useRef(Date.now());
  const accumulatedJobs = useRef<any[]>([]);
  const sseRef = useRef<SSEManager | null>(null);
  const jobsContainerRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);

  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456";
  const IV = "741852963qwerty0";

  function decryptData(ciphertext: string, keyStr: string, ivStr: string) {
    const key = CryptoJS.enc.Utf8.parse(keyStr);
    const iv = CryptoJS.enc.Utf8.parse(ivStr);
    return CryptoJS.AES.decrypt(ciphertext, key, {
      iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7,
    }).toString(CryptoJS.enc.Utf8);
  }

  /* push to log */
  function pushLog(message: string, type: string) {
    setActivityLog(prev => {
      const nextId = prev.length > 0 ? prev[prev.length - 1].id + 1 : 1;
      return [...prev, { id: nextId, message, type, timestamp: Date.now() }];
    });
    setPhase(getPhaseLabel(type));
  }

  /* Elapsed timer */
  useEffect(() => {
    if (isDone || error) return;
    const iv = setInterval(() => setElapsed(Math.floor((Date.now() - startTime.current) / 1000)), 1000);
    return () => clearInterval(iv);
  }, [isDone, error]);

  /* Auto-scroll log */
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
    const pdf = sessionStorage.getItem("resume");
    const context = sessionStorage.getItem("Lcontext");

    if (!pdf) {
      toast.error("Resume not found. Please upload your resume");
      router.push("/Jobs/LinkedinUserDetails");
      return;
    }
    setUrl(pdf);

    async function fetchCredentials() {
      try {
        const res = await fetch("/api/get-data", { method: "GET", credentials: "include" });
        const json = await res.json();
        if (json.encryptedData) {
          const creds = JSON.parse(decryptData(json.encryptedData, ENC_KEY, IV));
          setUserId(creds.username);
          setPassword(creds.password);
          setCredentialsReady(true);
        } else {
          toast.error("LinkedIn credentials not provided");
          router.push("/Jobs/LinkedinUserDetails");
        }
      } catch (e: any) {
        toast.error("Error fetching credentials: " + e.message);
      }
    }

    if (context !== "true") fetchCredentials();
    else setCredentialsReady(true);
  }, [router]);

  // Effect 3 — restore cached jobs OR reconnect to active job
  useEffect(() => {
    let cancelled = false;

    async function checkActiveOrCached() {
      const activeJobId = localStorage.getItem("fetch_jobs_id");

      if (activeJobId) {
        // Check if job is still running or completed
        try {
          const statusRes = await fetch(`${API_URL}/api/jobs/status?job_id=${activeJobId}`);
          if (statusRes.ok) {
            const statusData = await statusRes.json();

            if (statusData.status === "completed") {
              // Job finished while we were away - load results
              localStorage.removeItem("fetch_jobs_id");
              const outputJobs = statusData.output_data?.jobs || [];
              if (outputJobs.length > 0) {
                accumulatedJobs.current = outputJobs;
                setJobs(outputJobs);
                await saveFetchedJobs(outputJobs);
                setProgress(100);
                setIsDone(true);
                hasStarted.current = true;
                pushLog("Loaded completed job results.", "done");
              }
              if (!cancelled) setCacheCheckComplete(true);
              return;
            }

            if (statusData.status === "failed") {
              // Job failed - clear and allow fresh start
              localStorage.removeItem("fetch_jobs_id");
              if (!cancelled) setCacheCheckComplete(true);
              return;
            }

            if (
              statusData.status === "running" ||
              statusData.status === "pending" ||
              statusData.status === "scraper_raw"
            ) {
              // Job still running - reconnect to stream
              if (!cancelled) {
                pushLog("Reconnecting to active job...", "processing");
                setCacheCheckComplete(true);
                // The main effect (Effect 5) will handle reconnection since activeJobId exists
              }
              return;
            }
          }
        } catch (err) {
          console.error("Failed to check job status:", err);
        }
        if (!cancelled) setCacheCheckComplete(true);
        return;
      }

      // No active job - check for cached results
      try {
        const cached = await getFetchedJobs();
        if (cancelled) {
          return;
        }

        if (!cached?.jobs?.length) {
          setCacheCheckComplete(true);
          return;
        }

        const fetchedAt = typeof cached.fetchedAt === "number" ? cached.fetchedAt : 0;
        const ageMs = fetchedAt > 0 ? Math.max(0, Date.now() - fetchedAt) : null;

        setRecentCachedJobs(cached.jobs);
        setRecentCacheAgeLabel(formatCacheAge(ageMs));

        setCacheCheckComplete(true);
      } catch (err) {
        console.error("Failed to restore cached jobs:", err);
        if (!cancelled) setCacheCheckComplete(true);
      }
    }

    checkActiveOrCached();
    return () => {
      cancelled = true;
    };
  }, []);

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
      try {
        let savedJobId = localStorage.getItem("fetch_jobs_id");
        if (!savedJobId) {
            savedJobId = crypto.randomUUID();
            localStorage.setItem("fetch_jobs_id", savedJobId);
        }

        pushLog("Initiating job container...", "processing");
        const res = await fetch(`${API_URL}/api/jobs/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: Progress_userId,
                workflow_type: 'fetch_jobs',
                job_id: savedJobId,
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
        const jobId = data.job_id;
        
        // If server provided a different active job ID (auto-recover), update it
        if (jobId && jobId !== savedJobId) {
            localStorage.setItem("fetch_jobs_id", jobId);
            savedJobId = jobId;
        }
        
        pushLog("Job container started. Connecting to stream...", "processing");

        sseRef.current?.destroy();
        const manager = new SSEManager({
          url: `${API_URL}/api/jobs/stream?job_id=${savedJobId}`,
          staleThresholdMs: 90_000,
          reconnectBaseDelayMs: 1_500,
          reconnectMaxDelayMs: 12_000,
          withCredentials: true,
        });
        sseRef.current = manager;

        manager.onTerminalError = (message) => {
          localStorage.removeItem("fetch_jobs_id");
          setError(message);
          pushLog(message, "error");
          toast.error(message);
          setIsDone(true);
        };

        manager.onEvent = async (evData: any) => {
          if (evData?.error || evData?.progress === -1 || evData?.status === "error") {
            manager.destroy();
            localStorage.removeItem("fetch_jobs_id");
            setError(evData.error || evData.message || "Failed to fetch jobs");
            pushLog(evData.message || evData.error || "Process interrupted", "error");
            toast.error(evData.error || evData.message || "Something went wrong");
            setIsDone(true);
            return;
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
            if (Array.isArray(evData.jobs) && evData.jobs.length > 0) {
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
            }

            await saveFetchedJobs(accumulatedJobs.current);
            manager.destroy();
            localStorage.removeItem("fetch_jobs_id");
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
    localStorage.removeItem("fetch_jobs_id");
    hasStarted.current = false;
    accumulatedJobs.current = [];
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

  return (
    <div className="flex flex-col min-h-screen">

      {/* ─── Activity Feed Panel (top on mobile, sidebar on desktop) ── */}
      <div className={`shrink-0 w-full lg:fixed lg:top-[65px] lg:left-0 lg:h-[calc(100vh-65px)] lg:overflow-hidden bg-[#111] border-b lg:border-b-0 lg:border-r border-white/[0.06] cursor-default z-10 flex flex-col transition-all duration-300 ${
        sidebarOpen ? "lg:w-72" : "lg:w-12"
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
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                error ? "bg-red-500" : isDone ? "bg-emerald-500" : "bg-emerald-500/80"
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
      <div ref={jobsContainerRef} className={`flex-1 p-4 md:p-6 lg:p-8 transition-all duration-300 ${
        sidebarOpen ? "lg:ml-72" : "lg:ml-12"
      }`}>
        {USE_SAMPLE_DATA ? (
          <JobCards jobs={sampleJobs as any} />
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
            {!isDone && (
              <p className="text-xs text-emerald-400/60 mb-4">
                {jobs.length} jobs found — still searching for more...
              </p>
            )}
            <JobCards jobs={jobs} />
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