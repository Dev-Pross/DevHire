"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";
import toast from "react-hot-toast";

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

const JobCards: React.FC<JobCardsProps> = ({ jobs = [] }) => {
  const router = useRouter();
  const [selectedIds, setSelectedIds] = useState<{ job_id: string; job_url: string; job_description: string }[]>([]);

  const selectAllHandler = () => {
    if (selectedIds.length == jobs.length) {
      setSelectedIds([]);
      return;
    }
    const allIds = jobs.map(({ job_id, job_description, job_url }) => ({
      job_id, job_description, job_url,
    }));
    setSelectedIds(allIds);
  };

  const ApplierHandler = () => {
    if (selectedIds.length === 0) {
      toast.error("Please select jobs to proceed");
      return;
    } else {
      const refinedJobs = selectedIds.map(({ job_url, job_description }) => ({
        job_url, job_description,
      }));
      sessionStorage.setItem("jobs", JSON.stringify(refinedJobs));
      router.push("/apply");
    }
  };

  const cardHandler = (e: React.MouseEvent<HTMLLabelElement>, job: { job_id: string; job_url: string; job_description: string }) => {
    e.preventDefault();
    setSelectedIds((prev) => {
      const isSelected = prev.some((selectedJob) => selectedJob.job_id === job.job_id);
      if (isSelected) {
        return prev.filter((selectedJob) => selectedJob.job_id !== job.job_id);
      } else {
        return [...prev, { job_url: job.job_url, job_id: job.job_id, job_description: job.job_description }];
      }
    });
  };

  return (
    <>
      {/* Sticky toolbar */}
      <div className="w-full p-4 flex justify-between items-center sticky top-[65px] backdrop-blur-xl bg-[#0A0A0A]/80 z-10 border-b border-white/[0.06] rounded-xl mb-4">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            <span className="text-emerald-400 font-semibold">{selectedIds.length}</span> selected
          </span>
          <button
            className="text-sm text-gray-300 px-4 py-2 rounded-lg border border-white/[0.08] hover:border-white/[0.15] hover:bg-white/[0.03] transition-all cursor-pointer"
            onClick={selectAllHandler}
          >
            {selectedIds.length === jobs.length ? "Deselect all" : "Select all"}
          </button>
        </div>
        <button
          className="btn-primary text-sm !py-2.5 !px-6"
          onClick={ApplierHandler}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
          Apply Selected
        </button>
      </div>

      {/* Job cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {jobs.map((job) => (
          <label
            key={job.job_id}
            className={`surface-card overflow-hidden cursor-pointer flex flex-col transition-all duration-300 ${
              selectedIds.some((s) => s.job_id === job.job_id)
                ? "!border-emerald-500/50 shadow-lg shadow-emerald-500/10"
                : ""
            }`}
            onClick={(e) => cardHandler(e, { job_id: job.job_id, job_url: job.job_url, job_description: job.job_description })}
          >
            <input
              type="checkbox"
              name="job_selector"
              className="sr-only"
              checked={selectedIds.some((s) => s.job_id === job.job_id)}
              onChange={() => {}}
            />

            {/* Card content */}
            <div className="p-5 flex flex-col flex-1">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <p className="text-sm text-gray-400 font-medium">{job.company_name}</p>
                <span className="text-xs text-gray-600 whitespace-nowrap">{job.posted_at}</span>
              </div>

              {/* Title */}
              <a
                className="text-white font-semibold text-lg hover:text-emerald-400 transition-colors mb-2 line-clamp-2"
                href={job.job_url}
                onClick={(e) => e.stopPropagation()}
                target="_blank"
              >
                {job.title || "Network error"}
              </a>

              {/* Location */}
              <div className="flex items-center gap-1.5 mb-4">
                <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <p className="text-sm text-gray-500">{job.location}</p>
              </div>

              {/* Skills */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {job.key_skills.slice(0, 5).map((skill, idx) => (
                  <span
                    className="px-2.5 py-1 rounded-md bg-white/[0.05] text-xs text-gray-400 border border-white/[0.04]"
                    key={skill + idx}
                  >
                    {skill}
                  </span>
                ))}
              </div>

              {/* Footer stats */}
              <div className="flex items-center gap-4 mt-auto pt-4 border-t border-white/[0.06]">
                {job.relevance_score && (
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-sm text-gray-400">Match:</span>
                    <span className="text-sm text-emerald-400 font-semibold">{job.relevance_score}</span>
                  </div>
                )}
                {job.experience && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm text-gray-400">Exp:</span>
                    <span className="text-sm text-gray-300">{job.experience}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Selection indicator */}
            <div
              className={`h-1 w-full transition-all duration-300 ${
                selectedIds.some((s) => s.job_id === job.job_id) ? "bg-emerald-500" : "bg-transparent"
              }`}
            />
          </label>
        ))}
      </div>
    </>
  );
};

export default JobCards;
