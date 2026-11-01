"use client";

import React, { useState } from "react";
export interface TaggedSectionItem {
  sectionKey: string;
  label: string;
  instruction?: string;
}
export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  taggedSections?: string[];
  version?: number;
}

interface TailorStudioV2SplitProps {
  taggedItems: TaggedSectionItem[];
  onRemoveTag: (key: string) => void;
  onReviseWithPrompt: (prompt: string) => void;
  isRevising: boolean;
  revisionsRemaining: number;
  chatMessages: ChatMessage[];
  onExportPdf: () => void;
  isExportingPdf: boolean;
  onStartOver: () => void;
  quickPrompts: string[];
  onToggleTag?: (key: string, label: string) => void;
  onSwitchToResume?: () => void;
}

const ALL_SECTION_OPTIONS = [
  { key: "header", label: "Header" },
  { key: "summary", label: "Summary" },
  { key: "skills", label: "Skills" },
  { key: "experience", label: "Experience" },
  { key: "projects", label: "Projects" },
  { key: "education", label: "Education" },
];

export const TailorStudioV2Split: React.FC<TailorStudioV2SplitProps> = ({
  taggedItems,
  onRemoveTag,
  onReviseWithPrompt,
  isRevising,
  revisionsRemaining,
  chatMessages,
  onExportPdf,
  isExportingPdf,
  onStartOver,
  quickPrompts,
  onToggleTag,
  onSwitchToResume,
}) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() && taggedItems.length === 0) return;
    onReviseWithPrompt(prompt.trim());
    setPrompt("");
  };

  return (
    <div className="w-full h-full flex flex-col surface-card border border-white/[0.08] rounded-2xl overflow-hidden min-h-0 bg-[#0E0E0E]">
      {/* Chat Header */}
      <div className="px-4 py-3 border-b border-white/[0.08] bg-white/[0.02] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
            AI
          </div>
          <div>
            <h3 className="text-xs font-semibold text-gray-200">
              Tailor Chat Assistant
            </h3>
            <p className="text-[10px] text-gray-500">
              Interactive Section Revisions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-gray-300 bg-black/40 border border-white/[0.08] px-2.5 py-1 rounded-full font-mono">
            <span className={`w-1.5 h-1.5 rounded-full ${revisionsRemaining > 0 ? "bg-emerald-400" : "bg-red-400"}`} />
            <span>{revisionsRemaining}/3 Left</span>
          </div>

          {onSwitchToResume && (
            <button
              type="button"
              onClick={onSwitchToResume}
              className="md:hidden text-[11px] text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold hover:bg-emerald-500/20 transition cursor-pointer"
            >
              <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>View Resume</span>
            </button>
          )}

          <button
            type="button"
            onClick={onStartOver}
            className="text-[11px] text-gray-400 hover:text-white px-2 py-1 rounded-md hover:bg-white/[0.05]"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Chat Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 min-h-0">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                msg.sender === "user"
                  ? "bg-emerald-500 text-black font-medium rounded-br-none shadow-md shadow-emerald-500/10"
                  : "bg-white/[0.05] border border-white/[0.08] text-gray-200 rounded-bl-none"
              }`}
            >
              {msg.taggedSections && msg.taggedSections.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-1.5">
                  {msg.taggedSections.map((sec) => (
                    <span
                      key={sec}
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        msg.sender === "user" ? "bg-black/20 text-black" : "bg-emerald-500/20 text-emerald-300"
                      }`}
                    >
                      {sec}
                    </span>
                  ))}
                </div>
              )}
              <p>{msg.text}</p>
            </div>
            <span className="text-[10px] text-gray-500 mt-1 px-1">{msg.timestamp}</span>
          </div>
        ))}

        {isRevising && (
          <div className="flex items-start gap-2">
            <div className="bg-white/[0.05] border border-white/[0.08] text-gray-300 rounded-2xl rounded-bl-none px-4 py-2.5 text-xs flex items-center gap-2">
              <svg className="animate-spin h-3.5 w-3.5 text-emerald-400" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              <span>Refining tagged sections with LLM...</span>
            </div>
          </div>
        )}
      </div>

      {/* Active Tags & Quick Section Selector Bar */}
      <div className="px-3 sm:px-4 py-1.5 bg-black/40 border-t border-white/[0.06] shrink-0 space-y-1">
        {/* Quick Section Tag Selector (Tap directly to tag/untag) */}
        {onToggleTag && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
            <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider shrink-0">
              Quick Tag:
            </span>
            {ALL_SECTION_OPTIONS.map((sec) => {
              const isTagActive = taggedItems.some((item) => item.sectionKey === sec.key);
              return (
                <button
                  key={sec.key}
                  type="button"
                  onClick={() => onToggleTag(sec.key, sec.label)}
                  className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold transition cursor-pointer shrink-0 flex items-center gap-1 ${
                    isTagActive
                      ? "bg-emerald-500 text-black shadow-sm shadow-emerald-500/20"
                      : "bg-white/[0.04] hover:bg-white/[0.08] text-gray-300 border border-white/[0.08]"
                  }`}
                >
                  <span>{isTagActive ? "✓" : "+"}</span>
                  <span>{sec.label}</span>
                </button>
              );
            })}
          </div>
        )}

        <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-0.5 scrollbar-none">
          <span className="text-[11px] text-gray-400 font-medium shrink-0">
            {taggedItems.length === 0 ? "Select section to edit:" : "Tagged:"}
          </span>
          {taggedItems.length === 0 ? (
            <span className="text-[11px] text-gray-500 italic">
              Tap any [+ Tag Section] on the resume preview
            </span>
          ) : (
            taggedItems.map((item) => (
              <span
                key={item.sectionKey}
                className="inline-flex items-center gap-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs px-2.5 py-0.5 rounded-full font-semibold"
              >
                {item.label}
                <button
                  type="button"
                  onClick={() => onRemoveTag(item.sectionKey)}
                  className="hover:text-white ml-0.5 text-xs"
                >
                  ✕
                </button>
              </span>
            ))
          )}
        </div>

        {/* Quick Suggestions */}
        {taggedItems.length > 0 && quickPrompts.length > 0 && (
          <div className="flex items-center gap-1 overflow-x-auto pt-1 scrollbar-none">
            {quickPrompts.slice(0, 3).map((qp) => (
              <button
                key={qp}
                type="button"
                onClick={() => setPrompt(qp)}
                className="text-[10px] bg-white/[0.04] hover:bg-emerald-500/20 text-gray-300 hover:text-emerald-300 border border-white/[0.08] px-2 py-0.5 rounded-full whitespace-nowrap transition cursor-pointer shrink-0"
              >
                {qp}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Sticky Chat Input Bar */}
      <div className="p-2 sm:p-3 border-t border-white/[0.08] bg-[#121212] shrink-0 z-20">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isRevising || revisionsRemaining <= 0}
            placeholder={
              taggedItems.length === 0
                ? "Tag any section on preview to revise..."
                : `Instruct AI what to revise in tagged sections...`
            }
            className="flex-1 bg-black/60 border border-white/[0.1] focus:border-emerald-500 rounded-xl px-3.5 py-2.5 text-xs text-gray-200 placeholder-gray-500 outline-none transition"
          />

          <button
            type="submit"
            disabled={isRevising || (taggedItems.length === 0 && !prompt.trim()) || revisionsRemaining <= 0}
            className={`px-4 py-2.5 rounded-xl text-xs font-semibold transition flex items-center gap-1 shrink-0 ${
              isRevising || (taggedItems.length === 0 && !prompt.trim()) || revisionsRemaining <= 0
                ? "bg-white/[0.05] text-gray-500 cursor-not-allowed border border-white/[0.05]"
                : "bg-emerald-500 text-black hover:bg-emerald-400 cursor-pointer shadow-md shadow-emerald-500/20"
            }`}
          >
            Send
          </button>

          <button
            type="button"
            onClick={onExportPdf}
            disabled={isExportingPdf}
            className="px-3 py-2.5 rounded-xl text-xs font-semibold bg-white/[0.06] hover:bg-white/[0.12] text-gray-200 border border-white/[0.1] hover:border-white/[0.2] transition flex items-center gap-1 shrink-0 cursor-pointer"
            title="Download PDF"
          >
            {isExportingPdf ? "..." : "PDF ↓"}
          </button>
        </form>
      </div>
    </div>
  );
};

