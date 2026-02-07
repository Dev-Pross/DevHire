"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";
import toast from "react-hot-toast";
import { motion, type Variants } from "framer-motion";

interface JobcardProps {
  title: string;
  job_id: string;
  company_name: string;
  location: string;
  experience: string;
  salary: string;
  key_skills: string[];
  job_url: string;
  posted_at: string;
  job_description: string;
  source: string;
  relevance_score: string;
}

interface JobCardsProps {
  jobs: JobcardProps[];
}

/* ── helpers ── */
const containerVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.045 } },
};
const cardVariants: Variants = {
  hidden: { opacity: 0, y: 18, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: "easeOut" } },
};

function parseScore(raw: string): number {
  const n = parseInt(raw, 10);
  return isNaN(n) ? 0 : Math.min(100, Math.max(0, n));
}

const JobCards: React.FC<JobCardsProps> = ({ jobs = [] }) => {
  const router = useRouter();
  const [selectedIds, setSelectedIds] = useState<{ job_id: string; job_url: string; job_description: string }[]>([]);
  const [layout, setLayout] = useState<"grid" | "list">("grid");

  const isSelected = (id: string) => selectedIds.some((s) => s.job_id === id);

  const selectAllHandler = () => {
    if (selectedIds.length === jobs.length) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(jobs.map(({ job_id, job_description, job_url }) => ({ job_id, job_description, job_url })));
  };

  const ApplierHandler = () => {
    if (selectedIds.length === 0) {
      toast.error("Please select jobs to proceed");
      return;
    }
    sessionStorage.setItem(
      "jobs",
      JSON.stringify(selectedIds.map(({ job_url, job_description }) => ({ job_url, job_description })))
    );
    router.push("/apply");
  };

  const cardHandler = (e: React.MouseEvent<HTMLLabelElement>, job: { job_id: string; job_url: string; job_description: string }) => {
    e.preventDefault();
    setSelectedIds((prev) =>
      prev.some((s) => s.job_id === job.job_id)
        ? prev.filter((s) => s.job_id !== job.job_id)
        : [...prev, job]
    );
  };

  return (
    <>
      {/* ─── Sticky Toolbar ─── */}
      <div className="w-full px-5 py-3.5 flex flex-wrap justify-between items-center gap-3 sticky top-[65px] backdrop-blur-xl bg-[#0A0A0A]/85 z-10 border border-white/[0.06] rounded-2xl mb-6">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <p className="text-sm text-gray-500">
            <span className="text-emerald-400 font-semibold">{jobs.length}</span> jobs found
          </p>
          <div className="w-px h-4 bg-white/[0.08]" />
          <p className="text-sm text-gray-500">
            <span className="text-white font-medium">{selectedIds.length}</span> selected
          </p>
          <button
            className="text-xs text-gray-400 px-3 py-1.5 rounded-lg border border-white/[0.08] hover:border-white/[0.15] hover:text-white hover:bg-white/[0.04] transition-all cursor-pointer"
            onClick={selectAllHandler}
          >
            {selectedIds.length === jobs.length ? "Deselect all" : "Select all"}
          </button>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-3">
          {/* Layout toggle */}
          <div className="flex items-center bg-white/[0.04] rounded-lg border border-white/[0.06] p-0.5">
            <button
              onClick={() => setLayout("grid")}
              className={`p-1.5 rounded-md transition-all cursor-pointer ${layout === "grid" ? "bg-white/[0.08] text-emerald-400" : "text-gray-500 hover:text-gray-300"}`}
              title="Grid view"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <rect x="3" y="3" width="7" height="7" rx="1.5" />
                <rect x="14" y="3" width="7" height="7" rx="1.5" />
                <rect x="3" y="14" width="7" height="7" rx="1.5" />
                <rect x="14" y="14" width="7" height="7" rx="1.5" />
              </svg>
            </button>
            <button
              onClick={() => setLayout("list")}
              className={`p-1.5 rounded-md transition-all cursor-pointer ${layout === "list" ? "bg-white/[0.08] text-emerald-400" : "text-gray-500 hover:text-gray-300"}`}
              title="List view"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <rect x="3" y="4" width="18" height="4" rx="1.5" />
                <rect x="3" y="10" width="18" height="4" rx="1.5" />
                <rect x="3" y="16" width="18" height="4" rx="1.5" />
              </svg>
            </button>
          </div>

          <button className="btn-primary text-sm !py-2 !px-5 flex items-center gap-2" onClick={ApplierHandler}>
            Apply Selected
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      </div>

      {/* ─── Job Cards Grid ─── */}
      <motion.div
        className={`grid gap-5 ${
          layout === "grid"
            ? "grid-cols-1 md:grid-cols-2 xl:grid-cols-3"
            : "grid-cols-1 md:grid-cols-2"
        }`}
        variants={containerVariants}
        initial="hidden"
        animate="show"
        key={layout}
      >
        {jobs.map((job) => {
          const selected = isSelected(job.job_id);
          const score = parseScore(job.relevance_score);

          return (
            <motion.label
              key={job.job_id}
              variants={cardVariants}
              className={`group relative overflow-hidden rounded-2xl border cursor-pointer flex flex-col transition-all duration-300
                ${
                  selected
                    ? "border-emerald-500/40 bg-emerald-500/[0.03] shadow-[0_0_30px_-8px_rgba(16,185,129,0.12)]"
                    : "border-white/[0.06] bg-[#111]/80 hover:border-emerald-500/20 hover:shadow-[0_0_40px_-12px_rgba(16,185,129,0.06)]"
                }`}
              onClick={(e) => cardHandler(e, { job_id: job.job_id, job_url: job.job_url, job_description: job.job_description })}
            >
              <input type="checkbox" name="job_selector" className="sr-only" checked={selected} onChange={() => {}} />

              {/* ── Selection Checkbox (top-right) ── */}
              <div className="absolute top-4 right-4 z-10">
                <div
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
                    selected
                      ? "bg-emerald-500 border-emerald-500 scale-110"
                      : "border-white/[0.15] bg-transparent group-hover:border-white/[0.3]"
                  }`}
                >
                  {selected && (
                    <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </div>

              {/* ── Card Body ── */}
              <div className="p-5 pb-0 flex flex-col flex-1">
                {/* Header: company + posted */}
                <div className="flex items-center gap-2 mb-3 pr-8">
                  {job.company_name && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.05] border border-white/[0.06] text-xs font-medium text-gray-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/70" />
                      {job.company_name}
                    </span>
                  )}
                  {job.posted_at && (
                    <span className="text-[11px] text-gray-600 ml-auto whitespace-nowrap">{job.posted_at}</span>
                  )}
                </div>

                {/* Title */}
                <a
                  className="text-white font-semibold text-[15px] leading-snug hover:text-emerald-400 transition-colors mb-3 line-clamp-2"
                  href={job.job_url}
                  onClick={(e) => e.stopPropagation()}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {job.title || "Untitled Position"}
                </a>

                {/* Meta pills: location / salary / experience */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {job.location && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.04] text-xs text-gray-400">
                      <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {job.location}
                    </span>
                  )}
                  {job.salary && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.04] text-xs text-gray-400">
                      <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                      {job.salary}
                    </span>
                  )}
                  {job.experience && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.04] text-xs text-gray-400">
                      <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0H8m8 0h2a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2h2" />
                      </svg>
                      {job.experience}
                    </span>
                  )}
                </div>

                {/* Skills chips */}
                {job.key_skills?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {job.key_skills.slice(0, 4).map((skill, idx) => (
                      <span
                        className="px-2.5 py-0.5 rounded-full bg-emerald-500/[0.08] text-[11px] font-medium text-emerald-400 border border-emerald-500/[0.15]"
                        key={skill + idx}
                      >
                        {skill}
                      </span>
                    ))}
                    {job.key_skills.length > 4 && (
                      <span className="px-2.5 py-0.5 rounded-full bg-white/[0.04] text-[11px] text-gray-500 border border-white/[0.06]">
                        +{job.key_skills.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* ── Footer ── */}
              <div className="px-5 py-3.5 mt-auto border-t border-white/[0.05] flex items-center justify-between gap-3">
                {/* Relevance score bar */}
                {job.relevance_score && (
                  <div className="flex items-center gap-2.5 flex-1 min-w-0">
                    <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden max-w-[80px]">
                      <motion.div
                        className={`h-full rounded-full ${
                          score >= 80 ? "bg-emerald-400" : score >= 60 ? "bg-yellow-400" : "bg-orange-400"
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${score}%` }}
                        transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
                      />
                    </div>
                    <span className={`text-xs font-semibold tabular-nums ${
                      score >= 80 ? "text-emerald-400" : score >= 60 ? "text-yellow-400" : "text-orange-400"
                    }`}>
                      {job.relevance_score}
                    </span>
                  </div>
                )}

                {/* Source badge */}
                {job.source && (
                  <span className="text-[10px] uppercase tracking-wider text-gray-600 font-medium px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.04] shrink-0">
                    {job.source}
                  </span>
                )}
              </div>
            </motion.label>
          );
        })}
      </motion.div>
    </>
  );
};

export default JobCards;
