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
      onClick={(e) => {
        const target = e.target as HTMLElement;
        if (target.closest('a') || target.closest('button')) return;
        onToggleTag(sectionKey, label);
      }}
      className={`relative group transition-all duration-200 rounded p-1.5 -m-1 cursor-pointer sm:cursor-default ${
        isTagged
          ? "ring-2 ring-emerald-500 bg-emerald-500/[0.04]"
          : isHovered
          ? "ring-1 ring-emerald-500/30 bg-emerald-500/[0.015]"
          : "hover:ring-1 hover:ring-white/10"
      } ${isUpdated ? "animate-[pulse_1.5s_ease-in-out_2] ring-2 ring-emerald-400 bg-emerald-500/10" : ""}`}
    >
      {/* Dedicated Floating Tag Button on Right Side (Always accessible on touch, hover on desktop) */}
      <div
        className={`absolute top-1 right-1 z-20 transition-all duration-150 print:hidden ${
          isTagged
            ? "opacity-100 scale-100 pointer-events-auto"
            : isHovered
            ? "opacity-100 scale-100 pointer-events-auto"
            : "opacity-85 sm:opacity-0 sm:pointer-events-none scale-95 sm:group-hover:opacity-100 sm:group-hover:scale-100 pointer-events-auto"
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
