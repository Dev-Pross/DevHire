const DB_NAME = "hirehawk_db";
const DB_VERSION = 1;
const STORE = "hirehawk_results";

function ensureBrowser(): void {
  if (typeof indexedDB === "undefined") {
    throw new Error("IndexedDB is not available in this environment");
  }
}

async function openDB(): Promise<IDBDatabase> {
  ensureBrowser();

  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);

    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };

    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error || new Error("Failed to open IndexedDB"));
  });
}

async function idbSet(key: string, value: unknown): Promise<void> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(value, key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error(`Failed to write key ${key}`));
  });
}

async function idbGet<T>(key: string): Promise<T | null> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(key);
    req.onsuccess = () => resolve((req.result as T) ?? null);
    req.onerror = () => reject(req.error || new Error(`Failed to read key ${key}`));
  });
}

async function idbDelete(key: string): Promise<void> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error(`Failed to delete key ${key}`));
  });
}

function buildJobKey(job: any, index: number): string {
  if (job && typeof job === "object") {
    const url = job.job_url || job.url;
    if (typeof url === "string" && url.trim()) {
      return `url:${url.trim()}`;
    }

    const id = job.job_id || job.id;
    if (typeof id === "string" && id.trim()) {
      return `id:${id.trim()}`;
    }

    const title = typeof job.title === "string" ? job.title.trim() : "";
    const company = typeof job.company_name === "string" ? job.company_name.trim() : "";
    const location = typeof job.location === "string" ? job.location.trim() : "";
    if (title || company || location) {
      return `meta:${title}|${company}|${location}`;
    }
  }

  return `fallback:${index}`;
}

function dedupeJobs(jobs: any[]): any[] {
  const map = new Map<string, any>();
  jobs.forEach((job, index) => {
    map.set(buildJobKey(job, index), job);
  });
  return Array.from(map.values());
}

export interface FetchedJobsRecord {
  jobs: any[];
  fetchedAt: number;
  isFresh: boolean;
}

export async function saveFetchedJobs(jobs: any[]): Promise<void> {
  await idbSet("fetched_jobs", {
    jobs: dedupeJobs(jobs || []),
    fetchedAt: Date.now(),
    isFresh: true,
  } satisfies FetchedJobsRecord);
}

export async function appendFetchedJobs(batch: any[]): Promise<void> {
  const existing = await idbGet<FetchedJobsRecord>("fetched_jobs");
  const current = existing?.jobs ?? [];

  await idbSet("fetched_jobs", {
    jobs: dedupeJobs([...current, ...(batch || [])]),
    fetchedAt: Date.now(),
    isFresh: true,
  } satisfies FetchedJobsRecord);
}

export async function getFetchedJobs(): Promise<FetchedJobsRecord | null> {
  return idbGet<FetchedJobsRecord>("fetched_jobs");
}

export async function clearFetchedJobs(): Promise<void> {
  await idbDelete("fetched_jobs");
}

export interface ApplyProgressItem {
  job_url: string;
  company_name?: string;
  reason?: string;
  timestamp: number;
}

export interface ApplyProgressRecord {
  applied: ApplyProgressItem[];
  failed: ApplyProgressItem[];
  total: number;
  completedAt: number | null;
}

function upsertProgress(items: ApplyProgressItem[], nextItem: ApplyProgressItem): ApplyProgressItem[] {
  const filtered = items.filter((item) => item.job_url !== nextItem.job_url);
  filtered.push(nextItem);
  return filtered;
}

function createEmptyApplyProgress(total: number): ApplyProgressRecord {
  return {
    applied: [],
    failed: [],
    total,
    completedAt: null,
  };
}

export async function initApplyProgress(total: number): Promise<void> {
  await idbSet("apply_progress", createEmptyApplyProgress(total));
}

export async function recordApplied(job_url: string, company_name?: string): Promise<void> {
  if (!job_url) {
    return;
  }

  const existing = (await idbGet<ApplyProgressRecord>("apply_progress")) || createEmptyApplyProgress(0);
  const nextItem: ApplyProgressItem = {
    job_url,
    company_name,
    timestamp: Date.now(),
  };

  await idbSet("apply_progress", {
    ...existing,
    failed: existing.failed.filter((item) => item.job_url !== job_url),
    applied: upsertProgress(existing.applied, nextItem),
  } satisfies ApplyProgressRecord);
}

export async function recordFailed(job_url: string, company_name?: string, reason?: string): Promise<void> {
  if (!job_url) {
    return;
  }

  const existing = (await idbGet<ApplyProgressRecord>("apply_progress")) || createEmptyApplyProgress(0);
  const nextItem: ApplyProgressItem = {
    job_url,
    company_name,
    reason,
    timestamp: Date.now(),
  };

  await idbSet("apply_progress", {
    ...existing,
    applied: existing.applied.filter((item) => item.job_url !== job_url),
    failed: upsertProgress(existing.failed, nextItem),
  } satisfies ApplyProgressRecord);
}

export async function finalizeApplyProgress(): Promise<void> {
  const existing = await idbGet<ApplyProgressRecord>("apply_progress");
  if (!existing) {
    return;
  }

  await idbSet("apply_progress", {
    ...existing,
    completedAt: Date.now(),
  } satisfies ApplyProgressRecord);
}

export async function syncApplyProgressFromFinal(applied: string[], failed: string[], total: number): Promise<void> {
  const toItems = (urls: string[]) =>
    urls
      .filter((url) => typeof url === "string" && url.trim())
      .map((job_url) => ({ job_url, timestamp: Date.now() }));

  await idbSet("apply_progress", {
    applied: toItems(applied || []),
    failed: toItems(failed || []),
    total,
    completedAt: Date.now(),
  } satisfies ApplyProgressRecord);
}

export async function getApplyProgress(): Promise<ApplyProgressRecord | null> {
  return idbGet<ApplyProgressRecord>("apply_progress");
}

export async function clearApplyProgress(): Promise<void> {
  await idbDelete("apply_progress");
}
