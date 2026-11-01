"use client";

import React from "react";

export interface TaggedSectionItem {
  sectionKey: string;
  label: string;
  instruction: string;
}

interface TailorComposerProps {
  mode: "generate" | "revise";
  jobDescription: string;
  onJobDescriptionChange: (val: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;

  // Revise state
  taggedItems: TaggedSectionItem[];
  onRemoveTag: (sectionKey: string) => void;
  onInstructionChange: (sectionKey: string, instruction: string) => void;
  onRevise: () => void;
  isRevising: boolean;
  revisionsRemaining: number;
  onRegenerate: () => void;
  onExportLatexPdf: () => void;
  isExportingPdf: boolean;
  masterResumeUrl?: string | null;
}

export const TailorComposer: React.FC<TailorComposerProps> = ({
  mode,
  jobDescription,
  onJobDescriptionChange,
  onGenerate,
  isGenerating,
  taggedItems,
  onRemoveTag,
  onInstructionChange,
  onRevise,
  isRevising,
  revisionsRemaining,
  onRegenerate,
  onExportLatexPdf,
  isExportingPdf,
  masterResumeUrl,
}) => {
  // -------------------------------------------------------------
  // MODE 1: Initial Job Description Input
  // -------------------------------------------------------------
  if (mode === "generate") {
    return (
      <div className="surface-card w-full h-full flex flex-col justify-between p-4 md:p-6 relative overflow-hidden">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="text-gray-300 font-semibold text-sm tracking-wide uppercase">
              AI Tailoring Pipeline v2
            </h2>
          </div>
          <h1 className="text-gray-200 text-sm md:text-base leading-relaxed">
            Paste the target job description. Our AI will analyze requirements and tailor your master resume to match.
          </h1>
        </div>

        <div className="w-full flex items-end gap-3 mt-4">
          <textarea
            value={jobDescription}
            onChange={(e) => {
              onJobDescriptionChange(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 220)}px`;
            }}
            placeholder="Paste job description here..."
            className="input-dark w-full min-h-[5rem] max-h-[14rem] resize-none text-sm leading-relaxed"
            rows={2}
          />
          <button
            type="button"
            onClick={onGenerate}
            disabled={isGenerating || !jobDescription.trim()}
            className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center font-bold transition-all shrink-0 ${isGenerating || !jobDescription.trim()
                ? "bg-emerald-500/40 text-black/50 cursor-not-allowed"
                : "bg-emerald-500 text-black hover:bg-emerald-400 shadow-lg shadow-emerald-500/20 cursor-pointer"
              }`}
          >
            {isGenerating ? (
              <svg className="animate-spin h-5 w-5 text-black" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // MODE 2: Interactive Chat Revision Composer
  // -------------------------------------------------------------
  return (
    <div className="surface-card w-full h-full flex flex-col justify-between p-4 md:p-6 overflow-hidden">
      {/* Top Header & Revisions Counter */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-gray-200 font-semibold text-sm tracking-wide">
            Section-Level Editor
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {masterResumeUrl && (
            <a
              href={masterResumeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 bg-[#141414] border border-white/[0.08] hover:border-emerald-500/40 px-2.5 py-1 rounded-full text-xs font-medium text-gray-300 hover:text-emerald-400 transition-colors"
              title="Open master resume in new tab"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <span className="hidden sm:inline">Master Resume</span>
              <span className="sm:hidden">Resume</span>
            </a>
          )}
          <div className="flex items-center gap-2 bg-[#141414] border border-white/[0.08] px-3 py-1 rounded-full text-xs font-medium text-gray-300 shrink-0">
            <span
              className={`w-2 h-2 rounded-full ${revisionsRemaining > 0 ? "bg-emerald-500 animate-pulse" : "bg-red-500"
                }`}
            />
            <span>{revisionsRemaining}/3 Revisions Left</span>
          </div>
        </div>
      </div>

      {/* Tagged Sections List */}
      <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1">
        {taggedItems.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-400 gap-2">
            <div className="w-10 h-10 rounded-full bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-emerald-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
            </div>
            <p className="text-xs md:text-sm text-gray-300 font-medium">
              Hover over any section in the resume preview
            </p>
            <p className="text-xs text-gray-500 max-w-xs">
              Click <span className="text-emerald-400 font-semibold">[+ Edit Section]</span> on the right of any section to tag it here for instant rewriting.
            </p>
          </div>
        ) : (
          taggedItems.map((item) => (
            <div
              key={item.sectionKey}
              className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 space-y-2 transition-all hover:border-emerald-500/30"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-400">
                    {item.label}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => onRemoveTag(item.sectionKey)}
                  className="text-gray-400 hover:text-white p-1 rounded-md transition-colors"
                  title="Remove section tag"
                >
                  ✕
                </button>
              </div>
              <textarea
                value={item.instruction}
                onChange={(e) => onInstructionChange(item.sectionKey, e.target.value)}
                placeholder={`What should AI change in ${item.label}? (e.g. 'Emphasize Kubernetes and p99 latency')`}
                rows={2}
                maxLength={500}
                className="input-dark w-full text-xs leading-relaxed resize-none bg-black/40"
              />
              <div className="text-[10px] text-gray-500 text-right">
                {item.instruction.length}/500 chars
              </div>
            </div>
          ))
        )}
      </div>

      {/* Bottom Controls */}
      <div className="pt-3 border-t border-white/[0.08] space-y-2.5">
        <button
          type="button"
          onClick={onRevise}
          disabled={isRevising || taggedItems.length === 0 || revisionsRemaining <= 0}
          className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg ${isRevising || taggedItems.length === 0 || revisionsRemaining <= 0
              ? "bg-white/[0.06] text-gray-500 border border-white/[0.05] cursor-not-allowed"
              : "bg-emerald-500 text-black hover:bg-emerald-400 shadow-emerald-500/20 cursor-pointer"
            }`}
        >
          {isRevising ? (
            <>
              <svg className="animate-spin h-4 w-4 text-black" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <span>Refining Tagged Sections...</span>
            </>
          ) : (
            <span>
              Apply Revisions {taggedItems.length > 0 ? `(${taggedItems.length} section${taggedItems.length > 1 ? "s" : ""})` : ""}
            </span>
          )}
        </button>

        {/* Export and Reset row */}
        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            type="button"
            onClick={onRegenerate}
            disabled={isRevising}
            className="text-xs text-gray-400 hover:text-gray-200 px-3 py-1.5 rounded-lg hover:bg-white/[0.05] transition-all"
          >
            ← Start Over
          </button>

          {/* Single Download Action */}
          <button
            type="button"
            onClick={onExportLatexPdf}
            disabled={isExportingPdf}
            className="text-xs bg-emerald-500 text-black hover:bg-emerald-400 font-semibold px-4 py-2 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-emerald-500/20"
          >
            {isExportingPdf ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-black" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                <span>Preparing PDF...</span>
              </>
            ) : (
              <>
                <span>Download PDF</span>
                <span>↓</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
