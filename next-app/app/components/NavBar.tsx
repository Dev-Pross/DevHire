"use client";
import { SessionProvider, useSession, signOut } from "next-auth/react";
import { FaHome, FaBriefcase, FaFlask } from "react-icons/fa";
import Link from "next/link";

// NavBar component, expects to be wrapped in SessionProvider for fast session access
function NavBarInner() {
  const { data: session, status } = useSession();

  // Shared button styles for both "Get Started" and "Sign Out"
  const buttonBase =
    "px-6 py-2 rounded-full bg-gradient-to-r from-white/20 via-slate-400/30 to-white/10 text-white font-semibold shadow-lg border border-slate-600/40 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-200/80";
  const buttonHover =
    "hover:bg-white/90 hover:text-black hover:scale-105 hover:shadow-2xl";
  const buttonText =
    "bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent group-hover:text-black transition-all duration-200";

  // Only render after session status is not loading
  if (status === "loading") {
    return (
      <nav className="w-full flex justify-center mt-8">
        <div className="flex w-full max-w-5xl items-center justify-between rounded-3xl border border-white/20 bg-white/10 backdrop-blur-lg shadow-2xl px-10 py-4 transition-all duration-500 hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.25)]">
          <ul className="flex space-x-2 md:space-x-4">
            <NavItem href="/" icon={<FaHome />} label="Home" />
            <NavItem href="/jobs" icon={<FaBriefcase />} label="Jobs" />
            <NavItem href="/research" icon={<FaFlask />} label="Research" />
          </ul>
          <div>
            <div className="w-32 h-10 bg-white/20 rounded-full animate-pulse" />
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="w-full flex justify-center mt-8">
      <div className="flex w-full max-w-5xl items-center justify-between rounded-3xl border border-white/20 bg-white/10 backdrop-blur-lg shadow-2xl px-10 py-4 transition-all duration-500 hover:shadow-[0_12px_40px_0_rgba(31,38,135,0.25)]">
        <ul className="flex space-x-2 md:space-x-4">
          <NavItem href="/" icon={<FaHome />} label="Home" />
          <NavItem href="/jobs" icon={<FaBriefcase />} label="Jobs" />
          <NavItem href="/research" icon={<FaFlask />} label="Research" />
        </ul>
        <div>
          {session ? (
            <div className="flex items-center space-x-4">
              <span className="text-white/80 font-medium text-lg hidden md:inline transition-all duration-300">
                {session.user?.name
                  ? `Hi, ${session.user.name.split(" ")[0]}`
                  : session.user?.email}
              </span>
              <button
                className={`group ${buttonBase} ${buttonHover}`}
                style={{
                  fontWeight: 700,
                  fontSize: "1.13rem",
                  letterSpacing: "0.01em",
                  boxShadow: "0 2px 24px 0 rgba(192,192,192,0.10)",
                  backgroundImage:
                    "linear-gradient(90deg, rgba(255,255,255,0.13) 0%, rgba(180,180,180,0.18) 50%, rgba(255,255,255,0.08) 100%)",
                  cursor: "pointer",
                }}
                onClick={() => signOut()}
              >
                <span className={buttonText}>Sign Out</span>
              </button>
            </div>
          ) : (
            <Link
              href="/signin"
              className={`group ${buttonBase} ${buttonHover}`}
              style={{
                fontWeight: 700,
                fontSize: "1.13rem",
                letterSpacing: "0.01em",
                boxShadow: "0 2px 24px 0 rgba(192,192,192,0.10)",
                backgroundImage:
                  "linear-gradient(90deg, rgba(255,255,255,0.13) 0%, rgba(180,180,180,0.18) 50%, rgba(255,255,255,0.08) 100%)",
                cursor: "pointer",
              }}
            >
              <span className={buttonText}>Get Started</span>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

// NavItem component for pretty nav links with icons and transitions
function NavItem({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <li>
      <a
        href={href}
        className="flex items-center gap-2 px-5 py-2 rounded-xl text-white/90 font-medium text-lg transition-all duration-300 hover:bg-white/90 hover:text-black hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-white/40"
      >
        <span className="text-xl">{icon}</span>
        <span className="hidden sm:inline">{label}</span>
      </a>
    </li>
  );
}

// RealNavBar: Wraps NavBarInner in SessionProvider for correct next-auth usage and fast session hydration
export function RealNavBar() {
  return (
    <SessionProvider>
      <NavBarInner />
    </SessionProvider>
  );
}
