"use client";
import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

/**
 * Floating banner that appears on pages other than /apply when an
 * active apply session exists (tracked via sessionStorage).
 * Matches the app's dark theme with emerald accents.
 */
const ActiveApplyBanner: React.FC = () => {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Don't show on the apply page itself
    if (pathname === "/apply") {
      setVisible(false);
      return;
    }

    // Check sessionStorage for active apply session
    const isActive = sessionStorage.getItem("apply_active") === "true";
    setVisible(isActive);

    // Re-check when the tab regains focus (user might have completed on another tab)
    const onFocus = () => {
      setVisible(sessionStorage.getItem("apply_active") === "true");
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [pathname]);

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-[slideUp_0.4s_ease-out]">
      <Link
        href="/apply"
        className="group flex items-center gap-3 px-5 py-3 rounded-2xl
          bg-[#1A1A1A]/95 backdrop-blur-xl border border-emerald-500/25
          shadow-[0_8px_32px_rgba(0,0,0,0.5),0_0_0_1px_rgba(255,255,255,0.04)]
          hover:border-emerald-500/40 hover:shadow-[0_8px_32px_rgba(16,185,129,0.15)]
          transition-all duration-300 cursor-pointer select-none"
      >
        {/* Pulsing dot */}
        <span className="relative flex h-2.5 w-2.5 shrink-0">
          <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
        </span>

        <span className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
          Application in progress
        </span>

        {/* Arrow */}
        <svg
          className="w-4 h-4 text-emerald-400 group-hover:translate-x-0.5 transition-transform duration-200"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </Link>

      {/* Keyframe for the slide-up entrance */}
      <style jsx>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translate(-50%, 16px);
          }
          to {
            opacity: 1;
            transform: translate(-50%, 0);
          }
        }
      `}</style>
    </div>
  );
};

export default ActiveApplyBanner;
