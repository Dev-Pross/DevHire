"use client";
import React, { useEffect, useRef, useState } from "react";
import CryptoJS from "crypto-js";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { API_URL } from "../utiles/api";
import getLoginUser from "../utiles/getUserData";

interface JobsData {
  job_url: string;
  job_description: string;
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

  const logEndRef   = useRef<HTMLDivElement>(null);
  const startTime   = useRef(Date.now());


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

  /* Auto-scroll log to bottom */
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activityLog]);

  // Effect 1 — session data + credentials + db jobs
  useEffect(() => {
    const pdf     = sessionStorage.getItem("resume");
    const context = sessionStorage.getItem("Lcontext");
    const jobData = sessionStorage.getItem("jobs");
    const id      = sessionStorage.getItem("id");

    if (!pdf) {
      toast.error("Resume not found");
      router.push("/Jobs/LinkedinUserDetails");
      return;
    }
    setUrl(pdf);

    if (!jobData) {
      toast.error("No jobs found to proceed");
      router.push("/Jobs");
      return;
    }
    setJobs(JSON.parse(jobData));

    if (!id) { toast.error("Please login to start"); return; }
    setUser(id);

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

  // Effect 4 — POST + fetch stream
  useEffect(() => {
    if (!user || !jobs.length || dbData === null || !Progress_userId || !url || !credentialsReady) return;
    if (hasStarted.current) return;
    hasStarted.current = true;
    startTime.current = Date.now();

    const controller = new AbortController();
    abortRef.current  = controller;

    async function startStream() {
      try {
        const res = await fetch(`${API_URL}/apply-jobs`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          signal:  controller.signal,
          body: JSON.stringify({
            resume_url:    url,
            jobs:          jobs,
            progress_user: Progress_userId,
            user_id:       userId   || undefined,
            password:      password || undefined,
          }),
        });

        if (!res.ok || !res.body) {
          setError("Failed to start application process");
          pushLog("Connection failed — please try again", "error");
          return;
        }

        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let   buffer  = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const line = part.trim();
            if (!line || line.startsWith(":")) continue;
            if (!line.startsWith("data: ")) continue;

            try {
              const data = JSON.parse(line.slice(6));

              // Fatal error — progress -1 or status error
              if (data.progress === -1 || data.status === "error") {
                setError(data.error || data.message || "Application process failed");
                pushLog(data.message || data.error || "Process interrupted", "error");
                toast.error(data.error || data.message || "Something went wrong");
                setIsDone(true);
                return;
              }

              // Non-fatal warning
              if (data.warning) toast.error(data.message);

              // Update progress
              if (data.progress !== undefined) setProgress(data.progress);

              // Push message to activity log
              if (data.message) {
                pushLog(data.message, data.status || "processing", data.success);
              }

              // Final event
              if (data.progress === 100 && data.status === "done") {
                const applied = (data.applied ?? []).flat(Infinity);
                sessionStorage.setItem("applied", String(applied.length));

                const payload = [...new Set([...dbData, ...applied])];
                const dbRes   = await fetch("/api/User?action=update", {
                  method:  "POST",
                  headers: { "Content-Type": "application/json" },
                  body:    JSON.stringify({ id: user, data: { column: "applied_jobs", value: payload } }),
                });
                if (dbRes.ok) console.log("Applied jobs saved");
                else console.error("Failed to save applied jobs");

                setResults(data);
                setIsDone(true);
              }
            } catch {
              // malformed JSON line — skip
            }
          }
        }
      } catch (e: any) {
        if (e.name === "AbortError") return;
        toast.error("Stream error: " + e.message);
        setError(e.message);
        pushLog("Connection lost — please try again", "error");
      }
    }

    startStream();
    return () => controller.abort();
  }, [user, jobs, dbData, Progress_userId, url, credentialsReady, retryCount]);

  /* ── Count applied/skipped from log ── */
  const appliedCount = activityLog.filter(e => e.type === "applied").length;
  const skippedCount = activityLog.filter(e => e.type === "skipped").length;

  return (
    <div className="w-full min-h-screen overflow-x-hidden flex flex-col">

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
              onClick={() => { hasStarted.current = false; setError(null); setResults(null); setActivityLog([]); setProgress(0); setElapsed(0); setIsDone(false); startTime.current = Date.now(); setRetryCount(c => c + 1); }}
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
              { label: "Total Jobs",  value: results.total_jobs,                         color: "text-white"       },
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