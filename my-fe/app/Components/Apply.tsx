"use client";
import React, { useEffect, useRef, useState } from "react";
import CryptoJS from "crypto-js";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";
import { SSEManager } from "../utiles/sseManager";
import {
  clearApplyProgress,
  clearApplyResults,
  finalizeApplyProgress,
  getApplyProgress,
  getApplyResults,
  initApplyProgress,
  recordApplied,
  recordFailed,
  saveApplyResults,
  seedApplyProgressFromServer,
  syncApplyProgressFromFinal,
} from "../utiles/jobStorage";
import { useUser } from "../utiles/UserContext";
import { UpgradePopup } from "./UpgradePopup";

interface JobsData {
  job_url: string;
  job_description: string;
  company_name?: string;
}

interface LogEntry {
  id: number;
  message: string;
  type: "applied" | "skipped" | "processing" | "tailoring" | "starting" | "done" | "error" | string;
  timestamp: number;
  success?: boolean;
}

/* ── Phase badge helper ─────────────────────────────────── */
function getPhaseFromType(type: string): string {
  switch (type) {
    case "starting": return "Initializing";
    case "processing": return "Processing";
    case "tailoring": return "Tailoring";
    case "applied":
    case "skipped": return "Applying";
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

/* ── Status icon SVGs ───────────────────────────────────── */
const CheckIcon = () => (
  <svg className="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
);

const SkipIcon = () => (
  <svg className="w-3.5 h-3.5 text-amber-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
  </svg>
);

const SpinnerIcon = () => (
  <div className="w-3.5 h-3.5 rounded-full border-2 border-emerald-400/30 border-t-emerald-400 animate-spin shrink-0" />
);

const DotIcon = () => (
  <div className="w-2 h-2 rounded-full bg-gray-500 shrink-0 mt-[3px]" />
);

/* ── Animated log entry ─────────────────────────────────── */
const LogItem = ({ entry, isLatest }: { entry: LogEntry; isLatest: boolean }) => {
  const icon = entry.type === "applied" ? <CheckIcon />
    : entry.type === "skipped" ? <SkipIcon />
    : entry.type === "error" ? <SkipIcon />
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


const Apply: React.FC = () => {
  const router     = useRouter();
  const { user: globalUser, loading: userLoading, refreshUser } = useUser();
  const hasStarted = useRef(false);
  const abortRef   = useRef<AbortController | null>(null);

  const [activityLog, setActivityLog]       = useState<LogEntry[]>([]);
  const [progress, setProgress]             = useState(0);
  const [phase, setPhase]                   = useState("Initializing");
  const [results, setResults]               = useState<any>(null);
  const [error, setError]                   = useState<string | null>(null);
  const [url, setUrl]                       = useState("");
  const [userId, setUserId]                 = useState("");
  const [password, setPassword]             = useState("");
  const [user, setUser]                     = useState<string | null>(null);
  const [Progress_userId, setProgress_UserId] = useState("");
  const [jobs, setJobs]                     = useState<JobsData[]>([]);
  const [dbData, setDbData]                 = useState<any>(null);
  const [credentialsReady, setCredentialsReady] = useState(false);
  const [elapsed, setElapsed]               = useState(0);
  const [isDone, setIsDone]                 = useState(false);
  const [retryCount, setRetryCount]         = useState(0);
  const [appliedCount, setAppliedCount]     = useState(0);
  const [skippedCount, setSkippedCount]     = useState(0);
  const [totalJobs, setTotalJobs]           = useState(0);
  const [recoveredJobId, setRecoveredJobId] = useState<string | null>(null);
  const [showPopup, setShowPopup]           = useState(false);

  const logEndRef   = useRef<HTMLDivElement>(null);
  const startTime   = useRef(Date.now());
  const sseRef      = useRef<SSEManager | null>(null);


  const ENC_KEY = "qwertyuioplkjhgfdsazxcvbnm987456";
  const IV      = "741852963qwerty0";

  function decryptData(ciphertext: string, keyStr: string, ivStr: string) {
    const key = CryptoJS.enc.Utf8.parse(keyStr);
    const iv  = CryptoJS.enc.Utf8.parse(ivStr);
    return CryptoJS.AES.decrypt(ciphertext, key, {
      iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7,
    }).toString(CryptoJS.enc.Utf8);
  }

  /* push to log */
  function pushLog(message: string, type: string, success?: boolean) {
    setActivityLog(prev => {
      const nextId = prev.length > 0 ? prev[prev.length - 1].id + 1 : 1;
      return [...prev, { id: nextId, message, type, timestamp: Date.now(), success }];
    });
    setPhase(getPhaseFromType(type));
  }

  /* Elapsed timer */
  useEffect(() => {
    if (isDone || error) return;
    const iv = setInterval(() => setElapsed(Math.floor((Date.now() - startTime.current) / 1000)), 1000);
    return () => clearInterval(iv);
  }, [isDone, error]);

  /* Auto-scroll log to bottom — only scroll the log container, not the whole page */
  useEffect(() => {
    const container = logEndRef.current?.parentElement;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }, [activityLog]);

  // Effect 1 — session data + credentials + db jobs
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      // Wait for UserContext to finish loading before making tier decisions
      if (userLoading) return;

      if (globalUser?.tier === "FREE") {
        setShowPopup(true);
        return;
      }

      // Read from user context instead of sessionStorage to avoid race conditions
      const pdf     = globalUser.resume_url;
      const context = globalUser.linkedin_context;
      const jobData = sessionStorage.getItem("jobs");
      const id      = globalUser.id;

      if (!pdf) {
        toast.error("Resume not found");
        return;
      }
      setUrl(pdf);

      // Smart initialization: Check for cached results vs fresh job selections
      const cachedResults = await getApplyResults().catch(() => null);

      // If no new job selections but we have cached results, show them
      if (!jobData && cachedResults && cachedResults.completedAt) {
        if (!cancelled) {
          setResults({
            applied: cachedResults.applied,
            failed: cachedResults.failed,
            total_jobs: cachedResults.total_jobs,
          });
          setAppliedCount(cachedResults.applied.length);
          setSkippedCount(cachedResults.failed.length);
          setProgress(100);
          setIsDone(true);
          hasStarted.current = true;
          pushLog("Showing results from your last application session.", "done");
        }
        return;
      }

      // Check if there's an active job to reconnect to via the server.
      let isReconnecting = false;
      if (id) {
        try {
          const activeRes = await fetch(`${API_URL}/api/jobs/active?user_id=${encodeURIComponent(id)}&workflow_type=apply_jobs`);
          if (activeRes.ok) {
            const statusData = await activeRes.json();
            const { job_id, status, output_data } = statusData;

            if (job_id) {
              if (status === 'running' || status === 'pending' || status === 'scraper_raw') {
                // Fetch full status (including input_data) to hydrate the job list
                const statusRes = await fetch(`${API_URL}/api/jobs/status?job_id=${job_id}`);
                if (statusRes.ok) {
                  const fullStatusData = await statusRes.json();
                  const inputJobs = fullStatusData.input_data?.jobs || [];
                  if (inputJobs.length > 0 && !cancelled) {
                    setJobs(inputJobs);
                    isReconnecting = true;
                    setRecoveredJobId(job_id); // Pass to Effect 4

                    const outData = fullStatusData.output_data || {};
                    const appliedUrls = (Array.isArray(outData.applied) ? outData.applied : []).flat(Infinity).filter(Boolean);
                    const failedUrls = (Array.isArray(outData.failed) ? outData.failed : []).flat(Infinity).filter(Boolean);
                    const authoritativeTotal = outData.total_jobs ?? inputJobs.length;

                    setAppliedCount(appliedUrls.length);
                    setSkippedCount(failedUrls.length);
                    setTotalJobs(authoritativeTotal);
                    await seedApplyProgressFromServer(appliedUrls, failedUrls, authoritativeTotal).catch(() => {});

                    pushLog("Reconnecting to active job...", "processing");
                  }
                }
              } else if (status === 'completed') {
                if (!jobData) {
                  const applied = (output_data.applied ?? []).flat(Infinity);
                  const failed = (output_data.failed ?? []).flat(Infinity);

                  if (!cancelled) {
                    setResults({ applied, failed, total_jobs: output_data.total_jobs || applied.length + failed.length });
                    setAppliedCount(applied.length);
                    setSkippedCount(failed.length);
                    await saveApplyResults(applied, failed, output_data.total_jobs || applied.length + failed.length);
                    setProgress(100);
                    setIsDone(true);
                    hasStarted.current = true;
                    pushLog("Loaded completed application results from server.", "done");
                  }
                  return;
                }
              }
            }
          }
        } catch (err) {
          console.error("Failed to check active job on server:", err);
        }
      }

      if (!jobData && !isReconnecting) {
        // Server had no active/completed session, and no fresh job selections exist — try IndexedDB as fallback
        const persisted = await getApplyProgress().catch(() => null);
        if (!cancelled && persisted && (persisted.applied.length > 0 || persisted.failed.length > 0)) {
          const appliedUrls = persisted.applied.map((item) => item.job_url);
          const failedUrls = persisted.failed.map((item) => item.job_url);

          setResults({
            applied: appliedUrls,
            failed: failedUrls,
            total_jobs: persisted.total || appliedUrls.length + failedUrls.length,
          });
          setProgress(100);
          setIsDone(true);
          setAppliedCount(persisted.applied.length);
          setSkippedCount(persisted.failed.length);
          hasStarted.current = true;
          pushLog("Loaded saved application progress from previous session.", "done");
          return;
        }

        toast.error("No jobs found to proceed");
        router.push("/Jobs");
        return;
      }

      // If we have new job selections (not reconnecting), clear any old cached results
      if (!isReconnecting) {
        await clearApplyResults().catch(() => {});
        setJobs(JSON.parse(jobData!));
      }

      if (!id) {
        toast.error("Please login to start");
        return;
      }
      setUser(id);

      // Mark apply session as active for the floating banner
      sessionStorage.setItem("apply_active", "true");

      async function fetchCredentials() {
        try {
          const res  = await fetch("/api/get-data", { method: "GET", credentials: "include" });
          const json = await res.json();
          if (json.encryptedData) {
            const creds = JSON.parse(decryptData(json.encryptedData, ENC_KEY, IV));
            setUserId(creds.username);
            setPassword(creds.password);
            setCredentialsReady(true);
          } else {
            // LinkedIn not connected — proceed without credentials, backend handles this
            toast("LinkedIn is not connected. Proceeding without it.", { icon: "ℹ️" });
            setCredentialsReady(true);
          }
        } catch (e: any) {
          toast.error("Error fetching credentials: " + e.message);
        }
      }

      if (!context) await fetchCredentials();
      else setCredentialsReady(true);
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, [router, userLoading, globalUser]);

  // Effect 2 — progress user id
  useEffect(() => {
    async function loadUser() {
      const { data } = await getLoginUser();
      if (data?.user) setProgress_UserId(data.user.user_metadata.email);
    }
    loadUser();
  }, []);

  // Effect 3 — db applied jobs
  useEffect(() => {
    if (!user) return;
    async function getAppliedJobs() {
      const res     = await fetch(`/api/User?id=${user}`, { method: "GET", credentials: "include" });
      const my_data = await res.json();
      setDbData(my_data?.user?.applied_jobs ?? []);
    }
    getAppliedJobs();
  }, [user]);

  useEffect(() => {
    return () => {
      sseRef.current?.destroy();
      sseRef.current = null;
    };
  }, []);

  // Effect 4 — POST + fetch stream
  useEffect(() => {
    if (!user || !jobs.length || dbData === null || !Progress_userId || !url || !credentialsReady) return;
    if (hasStarted.current) return;
    hasStarted.current = true;
    startTime.current = Date.now();

    async function startStream() {
      try {
        // On a fresh start the selection IS the total; on reconnect the authoritative
        // server total was already set in Effect 1, so don't clobber it.
        setTotalJobs((t) => t || jobs.length);
        
        let activeJobId = recoveredJobId;
        const isFreshStart = !activeJobId;

        if (!activeJobId) {
            await initApplyProgress(jobs.length);
            pushLog("Initiating job container...", "processing");
            const res = await fetch(`${API_URL}/api/jobs/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: Progress_userId,
                    workflow_type: 'apply_jobs',
                    input_data: {
                        user_id: Progress_userId,
                        resume_url: url,
                        jobs: jobs,
                        ...(userId && { linkedin_id: userId }),
                        ...(password && { linkedin_password: password })
                    }
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to start application process");
            }

            const data = await res.json();
            activeJobId = data.job_id;
        }

        if (!activeJobId) throw new Error("Did not receive a valid job ID from server");

        pushLog("Job container started. Connecting to stream...", "processing");

        sseRef.current?.destroy();
        const manager = new SSEManager({
          url: `${API_URL}/api/jobs/stream?job_id=${activeJobId}`,
          staleThresholdMs: 90_000,
          reconnectBaseDelayMs: 1_500,
          reconnectMaxDelayMs: 12_000,
          withCredentials: true,
        });
        sseRef.current = manager;

        manager.onTerminalError = async (message) => {
          await finalizeApplyProgress();
          sessionStorage.removeItem("apply_active");
          setError(message);
          pushLog(message, "error");
          toast.error(message);
          setIsDone(true);
        };

        manager.onEvent = async (evData: any) => {
          if (evData?.error || evData?.progress === -1 || evData?.status === "error") {
            manager.destroy();
            await finalizeApplyProgress();
            sessionStorage.removeItem("apply_active");
            setError(evData.error || evData.message || "Application process failed");
            pushLog(evData.message || evData.error || "Process interrupted", "error");
            toast.error(evData.error || evData.message || "Something went wrong");
            setIsDone(true);
            return;
          }

          if (evData?.warning) toast.error(evData.message);

          if (typeof evData?.progress === "number") {
            setProgress(evData.progress);
          }

          if (evData?.message) {
            pushLog(evData.message, evData.status || "processing");
          }

          if (evData?.status === "applied" && evData?.job_url) {
            await recordApplied(evData.job_url, evData.job_company || evData.company_name);
            const progress = await getApplyProgress();
            if (progress) {
              setAppliedCount(progress.applied.length);
            }
          }

          if (evData?.status === "skipped" && evData?.job_url) {
            await recordFailed(evData.job_url, evData.job_company || evData.company_name, evData.message);
            const progress = await getApplyProgress();
            if (progress) {
              setSkippedCount(progress.failed.length);
            }
          }

          if (evData?.progress === 100 && evData?.status === "done") {
            manager.destroy();
            // Clear selected jobs and active flag from sessionStorage
            sessionStorage.removeItem("jobs");
            sessionStorage.removeItem("apply_active");

            let finalResult: any = null;
            try {
              const statusRes = await fetch(`${API_URL}/api/jobs/status?job_id=${activeJobId}`);
              if (statusRes.ok) {
                const statusData = await statusRes.json();
                finalResult = statusData.output_data;
              }
            } catch (e: any) {
              console.error("Failed to fetch final status:", e);
            }

            if (finalResult) {
              const applied = (finalResult.applied ?? []).flat(Infinity);
              const failed = (finalResult.failed ?? []).flat(Infinity);
              sessionStorage.setItem("applied", String(applied.length));
              setResults(finalResult);
              await syncApplyProgressFromFinal(applied, failed, finalResult.total_jobs || totalJobs || jobs.length);
              // Save final results to IndexedDB for future reference
              await saveApplyResults(applied, failed, finalResult.total_jobs || totalJobs || jobs.length);
            } else {
              const persisted = await getApplyProgress();
              if (persisted) {
                const applied = persisted.applied.map((item) => item.job_url);
                const failed = persisted.failed.map((item) => item.job_url);
                setResults({
                  applied,
                  failed,
                  total_jobs: persisted.total || totalJobs || jobs.length,
                });
                sessionStorage.setItem("applied", String(applied.length));
              }
            }

            await finalizeApplyProgress();
            // Refresh User.applied_jobs in context so the job list (and its
            // already-applied filter) reflects this run when the user returns to /Jobs.
            refreshUser().catch(() => {});
            setProgress(100);
            setIsDone(true);
          }
        };

        if (!isFreshStart) {
          const existingProgress = await getApplyProgress();
          if (!existingProgress) {
            await initApplyProgress(jobs.length);
          }
        }
      } catch (err: any) {
        sessionStorage.removeItem("apply_active");
        setError(err.message || "Failed to initialize pipeline");
        pushLog(err.message || "Initialization failed", "error");
        setIsDone(true);
      }
    }

    startStream();
  }, [user, jobs, dbData, Progress_userId, url, credentialsReady, retryCount]);

  return (
    <div className="w-full min-h-screen overflow-x-hidden flex flex-col">
      <UpgradePopup 
        isOpen={showPopup} 
        onClose={() => {
          setShowPopup(false);
          router.push("/Jobs");
        }} 
        message="Smart Apply is a Pro feature. Upgrade to automatically apply to jobs with AI!" 
      />
      {/* ─── Activity Feed Panel ──────────────────────────────── */}
      <div className="shrink-0 w-full bg-[#111] border-b border-white/[0.06] cursor-default">

        {/* Header + progress bar */}
        <div className="px-4 pt-5 pb-3 sm:px-6 md:px-8">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              {!isDone && !error ? (
                <div className="w-5 h-5 rounded-full border-2 border-emerald-400/30 border-t-emerald-400 animate-spin" />
              ) : isDone ? (
                <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
                </svg>
              )}
              <h3 className="text-sm font-semibold text-gray-200 tracking-tight">
                {isDone ? "Applications complete" : error ? "Process interrupted" : "Applying to jobs"}
              </h3>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-gray-400">
                {phase}
              </span>
              <span className="tabular-nums">{formatElapsed(elapsed)}</span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                error ? "bg-red-500" : isDone ? "bg-emerald-500" : "bg-emerald-500/80"
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          {/* Stats row — only show when applying has started */}
          {(appliedCount > 0 || skippedCount > 0) && (
            <div className="flex gap-4 mt-2.5 text-xs">
              <span className="text-emerald-400 tabular-nums">{appliedCount} applied</span>
              {skippedCount > 0 && <span className="text-amber-400 tabular-nums">{skippedCount} skipped</span>}
              <span className="text-gray-500 tabular-nums">{progress}%</span>
            </div>
          )}
        </div>

        {/* Scrollable activity log */}
        <div className="max-h-44 sm:max-h-52 md:max-h-60 overflow-y-auto px-4 pb-4 sm:px-6 md:px-8 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10">
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

      {/* ─── Main content area ────────────────────────────────── */}

      {/* Error state */}
      {error && (
        <div className="p-6 sm:p-8 lg:p-16">
          <div className="surface-card p-6 border border-red-500/30 text-center max-w-md mx-auto">
            <p className="text-red-400 font-medium mb-2">Something went wrong</p>
            <p className="text-gray-400 text-sm">{error}</p>
            <button
              onClick={() => {
                sseRef.current?.destroy();
                sseRef.current = null;
                void clearApplyProgress();
                void clearApplyResults();
                hasStarted.current = false;
                setError(null);
                setResults(null);
                setActivityLog([]);
                setProgress(0);
                setElapsed(0);
                setIsDone(false);
                startTime.current = Date.now();
                setRetryCount(c => c + 1);
              }}
              className="mt-4 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/20 transition"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Loading state — before results arrive and no error */}
      {!results && !error && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
            <p className="text-gray-400 text-sm text-center">Applying to selected jobs...</p>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="p-6 sm:p-8 lg:p-16">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
            {[
              { label: "Total Jobs",  value: results.total_jobs || totalJobs || jobs.length,               color: "text-white"       },
              { label: "Successful",  value: (results.applied  ?? []).flat(Infinity).length, color: "text-emerald-400" },
              { label: "Skipped",     value: (results.failed   ?? []).flat(Infinity).length, color: "text-amber-400"  },
            ].map((stat) => (
              <div key={stat.label} className="surface-card p-5 sm:p-6 text-center">
                <p className="text-sm text-gray-400 mb-1">{stat.label}</p>
                <p className={`text-2xl sm:text-3xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </div>
          <a href="https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED" target="_blank" className="block text-center">
            <div className="surface-card p-5 sm:p-6 hover:border-emerald-500/30 transition-all">
              <p className="text-emerald-400 text-base sm:text-lg font-semibold">Track your applications on LinkedIn →</p>
            </div>
          </a>
        </div>
      )}

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

export default Apply;