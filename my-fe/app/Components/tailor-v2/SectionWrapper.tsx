"use client";

import React, { useState } from "react";

interface SectionWrapperProps {
  sectionKey: string;
  label: string;
  isTagged: boolean;
  isUpdated?: boolean;
  onToggleTag: (sectionKey: string, label: string) => void;
  children: React.ReactNode;
}

export const SectionWrapper: React.FC<SectionWrapperProps> = ({
  sectionKey,
  label,
  isTagged,
  isUpdated = false,
  onToggleTag,
  children,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      data-section-key={sectionKey}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`relative group transition-all duration-200 rounded p-1 -m-1 ${
        isTagged
          ? "ring-1 ring-emerald-500/50 bg-emerald-500/[0.03]"
          : isHovered
          ? "ring-1 ring-emerald-500/30 bg-emerald-500/[0.015]"
          : ""
      } ${isUpdated ? "animate-[pulse_1.5s_ease-in-out_2] ring-2 ring-emerald-400 bg-emerald-500/10" : ""}`}
    >
      {/* Dedicated Floating Tag Button on Right Side */}
      <div
        className={`absolute top-0.5 right-1 z-20 transition-all duration-150 print:hidden ${
          isHovered || isTagged ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
        }`}
      >
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggleTag(sectionKey, label);
          }}
          className={`cursor-pointer inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium tracking-wide shadow-md transition-all ${
            isTagged
              ? "bg-emerald-500 text-black hover:bg-emerald-400 font-semibold shadow-emerald-500/20"
              : "bg-[#1A1A1A] text-gray-200 hover:bg-emerald-500 hover:text-black border border-white/10 hover:border-emerald-500/40"
          }`}
          title={isTagged ? "Click to remove tag" : `Tag ${label} for revision`}
        >
          {isTagged ? (
            <>
              <svg className="w-3 h-3 stroke-[2.5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span>Tagged</span>
            </>
          ) : (
            <>
              <svg className="w-3 h-3 stroke-[2.5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              <span>Edit {label}</span>
            </>
          )}
        </button>
      </div>

      {/* Selectable Section Content */}
      <div className="select-text">{children}</div>
    </div>
  );
};
